import redis
from fastapi import FastAPI, HTTPException, Depends, Body
import aiohttp
import asyncio
from urllib.parse import urlparse
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from dotenv import load_dotenv

from .models import UserQueries, Fact, ResponseData
from .processing import process_html_content
from .retrieval import lance_retrieval, lance_search
from .enumeration import get_all_website_links
from .retrieval import lance_retrieval

import logging
import json  # Add this import at the top
from json import JSONEncoder

logger = logging.getLogger("medscrape")
logging.basicConfig(level=logging.INFO)

app = FastAPI()

load_dotenv()

class FactEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Fact):  
            return obj.__dict__  
        
        if isinstance(obj, ResponseData):  
            return obj.__dict__  
        return JSONEncoder.default(self, obj)

@app.post("/run/")
async def medscrape(query: UserQueries):
    website_url = query.tld
    user_questions = query.questions
    print(f"Initiating processing for URL: {website_url}")
    tld = urlparse(website_url).netloc
    async with aiohttp.ClientSession() as session:
        website = await get_all_website_links(website_url, session)
        print(f"Found {len(website.urls)} URLs to process.")
        tasks = [process_html_content(url, tld, session) for url in website.urls]
        await asyncio.gather(*tasks)
        print("Processing completed.")
    print("Starting to search for answers...")
    answers = await lance_retrieval(query)
    formatted_answers = [{"question": q, "answer": a.answer} for q, a in zip(user_questions, answers)]
    print("Completed searching for answers.")
    response =  {"message": "Completed processing and answering questions.", "data": formatted_answers}
    print(json.dumps(response, indent=4, cls=FactEncoder))
    return response

@app.post("/process/")
async def scrape_and_process(tld: str = Body(..., embed=True)):
    website_tld = tld
    print(f"Initiating scraping and processing for URL: {tld}")
    parsed_tld = urlparse(website_tld).netloc
    async with aiohttp.ClientSession() as session:
        website = await get_all_website_links(website_tld, session)
        print(f"Found {len(website.urls)} URLs to process.")
        tasks = [process_html_content(url, website_tld, session) for url in website.urls]
        await asyncio.gather(*tasks)
    return {"message": "Scraping and processing completed", "url": parsed_tld, "urls_found": len(website.urls)}

@app.post("/query/")
async def make_query_call(query: UserQueries):
    print(f"Making query call with LLM over questions: {query.questions}")
    answers = await lance_retrieval(query)
    formatted_answers = [{"question": q, "answer": a.answer} for q, a in zip(query.questions, answers)]
    response = {"message": "Inference call made successfully", "data": formatted_answers}
    print(json.dumps(response, indent=4, cls=FactEncoder))  # Use the custom encoder here
    return response

@app.post("/search/")
async def make_search_call(query: UserQueries):
    print(f"Initiating database search over questions: {query.questions}")
    search_results = await lance_search(query)
    formatted_search_results = [{"question": q, "search_result": sr} for q, sr in zip(query.questions, search_results)]
    response = {"message": "Database search call made successfully", "data": formatted_search_results}
    print(json.dumps(response, indent=4, cls=FactEncoder))  # Use the custom encoder here
    return response

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response: {response.status_code}")
    return response

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logger.error(f"HTTP error occurred for {request.url}: {exc.detail}")
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