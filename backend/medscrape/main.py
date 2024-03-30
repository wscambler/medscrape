import os
import logging
import json
import aiohttp
import asyncio
import gspread

from dotenv import load_dotenv
from json import JSONEncoder
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis
from contextlib import asynccontextmanager
from urllib.parse import urlparse
from starlette.requests import Request
from starlette.responses import JSONResponse, Response as StarletteResponse
from starlette.middleware.base import BaseHTTPMiddleware
import time

from .models import UserQueries, Response, ResponseData
from .processing import process_html_content
from .retrieval import lance_retrieval, lance_search
from .enumeration import get_all_website_links
from .retrieval import lance_retrieval



logger = logging.getLogger("medscrape")
logging.basicConfig(filename='app.log', level=logging.INFO)

load_dotenv()

REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')

@asynccontextmanager
async def app_lifespan(app: FastAPI):
    global log_redis_client
    log_redis_client = await Redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)
    try:
        yield
    finally:
        await log_redis_client.close()
        await log_redis_client.wait_closed()

app = FastAPI(lifespan=app_lifespan)

# Split the CORS_ORIGINS by comma to support multiple origins
allowed_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ResponseEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Response):  
            return obj.__dict__  
        
        if isinstance(obj, ResponseData):  
            return obj.__dict__  
        return JSONEncoder.default(self, obj)

class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        log_message = f'Path: {request.url.path}, Method: {request.method}, Status: {response.status_code}, Time: {process_time}'
        logger.info(log_message)
        asyncio.create_task(log_redis_client.publish('log_channel', log_message))
        return response

app.add_middleware(LoggingMiddleware)

@app.post("/run/")
async def medscrape(query: UserQueries):
    website_url = query.tld
    user_questions = query.questions
    tld = urlparse(website_url).netloc
    async with aiohttp.ClientSession() as session:
        website = await get_all_website_links(website_url, session)
        tasks = [process_html_content(url, tld, session) for url in website.urls]
        await asyncio.gather(*tasks)
    answers = await lance_retrieval(query)
    formatted_answers = [{"question": q, "answer": a.answer} for q, a in zip(user_questions, answers)]
    response =  {"message": "Completed processing and answering questions.", "data": formatted_answers}
    log_message = f'Processing and answering questions completed for {website_url}'
    logger.info(log_message)
    asyncio.create_task(log_redis_client.publish('response_channel', json.dumps(response, cls=ResponseEncoder)))
    return response

@app.post("/process/")
async def scrape_and_process(request: Request):
    body = await request.json()
    website_tld = body.get('tld')
    if not website_tld:
        raise HTTPException(status_code=400, detail="URL is required")
    parsed_tld = urlparse(website_tld).netloc
    try:
        async with aiohttp.ClientSession() as session:
            website = await get_all_website_links(website_tld, session)
            tasks = [process_html_content(url, website_tld, session) for url in website.urls]
            total_tasks = len(tasks)
            completed_tasks = 0
            for task in asyncio.as_completed(tasks):
                await task
                completed_tasks += 1
                progress_percentage = (completed_tasks / total_tasks) * 100
                progress_update = {"status": "Processing", "progress": progress_percentage}
                asyncio.create_task(log_redis_client.publish('progress_channel', json.dumps(progress_update)))
        response = {"message": "Scraping and processing completed", "url": parsed_tld, "urls_found": len(website.urls)}
        log_message = f'Scraping and processing completed for {parsed_tld}'
        logger.info(log_message)
        asyncio.create_task(log_redis_client.publish('response_channel', json.dumps(response)))
    except Exception as e:
        logger.error(f"Error during processing: {str(e)}")
        response = {"message": "An error occurred during processing", "error": str(e)}
    return response

@app.post("/query/")
async def make_query_call(query: UserQueries):
    log_message = f"Making query call with LLM over questions: {query.questions}"
    logger.info(log_message)
    asyncio.create_task(log_redis_client.publish('response_channel', log_message))
    progress_update = {"status": "Query Processing", "progress": 0}
    asyncio.create_task(log_redis_client.publish('query_progress_channel', json.dumps(progress_update)))
    answers = await lance_retrieval(query)
    for i, answer in enumerate(answers):
        progress = (i + 1) / len(answers) * 100
        asyncio.create_task(log_redis_client.publish('query_progress_channel', json.dumps({"progress": progress})))
    formatted_answers = [{"question": q, "answer": a.answer} for q, a in zip(query.questions, answers)]
    response = {"message": "Inference call made successfully", "data": formatted_answers}
    
    # Set up the Google Sheets client using your JSON key file for authentication
    gc = gspread.service_account(filename=os.getenv('GOOGLE_CREDENTIALS_PATH'))
    sheet_id = os.getenv('GOOGLE_SHEET_ID')  # Replace with your actual Google Sheet ID
    sheet = gc.open_by_key(sheet_id).sheet1
    
    # Ensure each value is a string and not None. If None, replace with a default value, e.g., "N/A"
    cleaned_answers = []
    for answer in formatted_answers:
        cleaned_answer = {key: (str(value) if value is not None else "N/A") for key, value in answer.items()}
        cleaned_answers.append(cleaned_answer)

    # Convert each dictionary to a list of values in the correct order before appending
    values_to_append = [[answer['question'], answer['answer']] for answer in cleaned_answers]

    # Use gspread to append `values_to_append` to the sheet in a single batch operation
    sheet.append_rows([[query.tld] + row for row in values_to_append])
    
    progress_update = {"status": "Query Processing", "progress": 100}
    asyncio.create_task(log_redis_client.publish('query_progress_channel', json.dumps(progress_update)))
    
    logger.info(json.dumps(response, indent=4, cls=ResponseEncoder))
    asyncio.create_task(log_redis_client.publish('response_channel', json.dumps(response, indent=4, cls=ResponseEncoder)))
    return response

@app.post("/search/")
async def make_search_call(query: UserQueries):
    log_message = f"Initiating database search over questions: {query.questions}"
    logger.info(log_message)
    asyncio.create_task(log_redis_client.publish('log_channel', log_message))
    search_results = await lance_search(query)
    formatted_search_results = [{"question": q, "search_result": sr} for q, sr in zip(query.questions, search_results)]
    response = {"message": "Database search call made successfully", "data": formatted_search_results}
    logger.info(json.dumps(response, indent=4, cls=ResponseEncoder))  # Use the custom encoder here
    asyncio.create_task(log_redis_client.publish('response_channel', json.dumps(response, indent=4, cls=ResponseEncoder)))
    return response

@app.middleware("http")
async def log_requests(request: Request, call_next):
    log_message = f"Request: {request.method} {request.url}"
    logger.info(log_message)
    asyncio.create_task(log_redis_client.publish('log_channel', log_message))
    response = await call_next(request)
    log_message = f"Response: {response.status_code}"
    logger.info(log_message)
    asyncio.create_task(log_redis_client.publish('log_channel', log_message))
    return response

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    log_message = f"HTTP error occurred for {request.url}: {exc.detail}"
    logger.error(log_message)
    asyncio.create_task(log_redis_client.publish('log_channel', log_message))
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": exc.detail},
    )

@app.get("/health/")
async def health_check():
    return {"status": "healthy"}

@app.get("/v1/health/")
async def health_check_v1():
    return {"status": "healthy", "version": "v1"}

@app.get("/stream/")
async def stream(request: Request, channel: str = 'log_channel'):
    logger.info(f"Attempting to connect to Redis at URL: {REDIS_URL}")
    r = await Redis.from_url(os.getenv('REDIS_URL', 'redis://redis:6379/0'), encoding="utf-8", decode_responses=True) 
    logger.info("Connected to Redis successfully.")
    pubsub = r.pubsub()
    await pubsub.subscribe(channel)
    logger.info(f"Subscribed to Redis channel: {channel}")
    
    async def event_generator():
        try:
            while True:
                message = await pubsub.get_message()
                if message and message['type'] == 'message':
                    log_data = message['data']
                    logger.info(f"Streaming data: {log_data}")
                    yield f"data: {json.dumps({'message': log_data})}\n\n"
                await asyncio.sleep(.01)
        except Exception as e:
            logger.error(f"Error in stream event generator: {str(e)}")
        finally:
            await pubsub.unsubscribe(channel)
            pubsub.close()
            await r.wait_closed()
            logger.info(f"Unsubscribed from Redis channel: {channel} and connection closed.")

    response = StreamingResponse(event_generator(), media_type="text/event-stream")
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response

@app.get("/progress_stream/")
async def progress_stream(request: Request, channel: str = 'progress_channel'):
    logger.info(f"Attempting to connect to Redis for progress updates at URL: {REDIS_URL}")
    r = await Redis.from_url(os.getenv('REDIS_URL', 'redis://redis:6379/0'), encoding="utf-8", decode_responses=True) 
    logger.info("Connected to Redis for progress updates successfully.")
    pubsub = r.pubsub()
    await pubsub.subscribe(channel)
    logger.info(f"Subscribed to Redis progress channel: {channel}")
    
    async def progress_event_generator():
        try:
            while True:
                message = await pubsub.get_message()
                if message and message['type'] == 'message':
                    progress_data = message['data']
                    logger.info(f"Streaming progress data: {progress_data}")
                    yield f"data: {progress_data}\n\n"
                await asyncio.sleep(1)  # Adjust sleep time as needed
        except Exception as e:
            logger.error(f"Error in progress stream event generator: {str(e)}")
        finally:
            await pubsub.unsubscribe(channel)
            pubsub.close()
            await r.wait_closed()
            logger.info(f"Unsubscribed from Redis progress channel: {channel} and connection closed.")

    response = StreamingResponse(progress_event_generator(), media_type="text/event-stream")
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response

@app.get("/query_progress_stream/")
async def query_progress_stream(request: Request, channel: str = 'query_progress_channel'):
    logger.info(f"Attempting to connect to Redis for query progress updates at URL: {REDIS_URL}")
    r = await Redis.from_url(os.getenv('REDIS_URL', 'redis://redis:6379/0'), encoding="utf-8", decode_responses=True) 
    logger.info("Connected to Redis for query progress updates successfully.")
    pubsub = r.pubsub()
    await pubsub.subscribe(channel)
    logger.info(f"Subscribed to Redis query progress channel: {channel}")
    
    async def query_progress_event_generator():
        try:
            while True:
                message = await pubsub.get_message()
                if message and message['type'] == 'message':
                    query_progress_data = message['data']
                    logger.info(f"Streaming query progress data: {query_progress_data}")
                    yield f"data: {query_progress_data}\n\n"
                await asyncio.sleep(1)  # Adjust sleep time as needed
        except Exception as e:
            logger.error(f"Error in query progress stream event generator: {str(e)}")
        finally:
            await pubsub.unsubscribe(channel)
            pubsub.close()
            await r.wait_closed()
            logger.info(f"Unsubscribed from Redis query progress channel: {channel} and connection closed.")

    response = StreamingResponse(query_progress_event_generator(), media_type="text/event-stream")
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response