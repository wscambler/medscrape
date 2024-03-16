import redis
from fastapi import FastAPI, HTTPException, Depends
import aiohttp
import asyncio
from urllib.parse import urlparse
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from dotenv import load_dotenv

from .models import UserQueries
from .processing import process_html_content
from .retrieval import lance_search
from .enumeration import get_all_website_links
from .retrieval import lance_search

import logging
import json  # Add this import at the top

logger = logging.getLogger("medscrape")
logging.basicConfig(level=logging.INFO)

app = FastAPI()

load_dotenv()


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
    answers = await lance_search(query)
    formatted_answers = [{"question": q, "answer": a.answer} for q, a in zip(user_questions, answers)]
    print("Completed searching for answers.")
    return {"message": "Completed processing and answering questions.", "data": formatted_answers}

@app.post("/process/")
async def scrape_and_process(url: str):
    print(f"Initiating scraping and processing for URL: {url}")
    tld = urlparse(url).netloc
    async with aiohttp.ClientSession() as session:
        website = await get_all_website_links(url, session)
        print(f"Found {len(website.urls)} URLs to process.")
        tasks = [process_html_content(url, tld, session) for url in website.urls]
        await asyncio.gather(*tasks)
    return {"message": "Scraping and processing completed", "url": url, "urls_found": len(website.urls)}

@app.post("/query/")
async def make_query_call(query: UserQueries):
    print(f"Making query call with LLM over questions: {query.questions}")
    answers = await lance_search(query)
    formatted_answers = [{"question": q, "answer": a.answer} for q, a in zip(query.questions, answers)]
    response = {"message": "Inference call made successfully", "data": formatted_answers}
    print(json.dumps(response, indent=4))  # Pretty print the response
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