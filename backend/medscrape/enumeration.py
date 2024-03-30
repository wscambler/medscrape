import re
import asyncio
import logging
import redis
import os
import time

from redis.asyncio import Redis
from pydantic import BaseModel, Field
from typing import List
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

# Initialize Redis client (adjust parameters as needed for your Redis setup)
redis_client = redis.Redis(host=os.getenv('REDIS_HOST', 'localhost'), port=int(os.getenv('REDIS_PORT', 6379)), db=0, decode_responses=True)

class Website(BaseModel):
    tld: str = Field(..., description="The top-level domain of the website.")
    urls: List[str] = Field(..., description="The sub pages collected from the website.")

CONCURRENCY_LIMIT = int(os.getenv('CONCURRENCY_LIMIT', 100))
REVISIT_INTERVAL = int(os.getenv('REVISIT_INTERVAL', 43200))  # Default to 12 hours

def is_valid(url):
    """
    Checks whether `url` is a valid URL.
    """
    parsed = urlparse(url)
    return bool(parsed.netloc) and bool(parsed.scheme)

def should_exclude_link(href):
    # Define patterns for links to exclude
    excluded_patterns = [
        '^#',  # Anchor links
        '^mailto:',  # Mail links
        '^tel:',  # Telephone links
        '^javascript:',  # JavaScript links
        '\.(pdf|docx|xlsx|zip)$',  # Direct file downloads
        '/login', '/logout', '/register', '/password'  # Authentication links
    ]
    return any(re.search(pattern, href, re.IGNORECASE) for pattern in excluded_patterns)

def extract_tld(url):
    """
    Extracts the top-level domain (TLD) from the given URL.
    """
    parsed_url = urlparse(url)
    return parsed_url.netloc if parsed_url.netloc else parsed_url.path

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
# Initialize Redis client for publishing logs
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')
log_redis_client = Redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)

async def get_all_website_links(url, session, visited=set(), semaphore=None):
    """
    Recursively finds all URLs within the same domain as the starting URL, with improved error handling and caching of visited URLs using Redis.
    """
    if semaphore is None:
        semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT) 

    # Check if URL has been visited recently using Redis
    visited_timestamp = redis_client.hget("visited_urls", url)
    if visited_timestamp and (time.time() - float(visited_timestamp)) < REVISIT_INTERVAL:
        log_message = f"URL visited recently, skipping: {url}"
        logger.info(log_message)
        await log_redis_client.publish('log_channel', log_message)  # Publish log message to Redis channel
        return Website(tld='', urls=[])  # Return an empty Website model if URL has been visited recently
    log_message = f"Visiting: {url}"
    logger.info(log_message)
    await log_redis_client.publish('response_channel', log_message)  # Publish log message to Redis channel
    
    # Add URL to Redis hash with current timestamp
    redis_client.hset("visited_urls", url, time.time())
    log_message = f"Adding URL to visited set in Redis with timestamp: {url}"  # Added detailed logging
    logger.info(log_message)
    await log_redis_client.publish('log_channel', log_message)  # Publish log message to Redis channel

    urls = set()
    domain_name = extract_tld(url)  # Replacing direct urlparse call with extract_tld function

    async with semaphore:  # Use semaphore to limit concurrency
        try:
            async with session.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}) as response:
                html_content = await response.text()
                soup = BeautifulSoup(html_content, "html.parser")
                a_tags_found = soup.findAll("a")
                for a_tag in a_tags_found:
                    href = a_tag.get("href")
                    if href and not should_exclude_link(href):
                        normalized_href = urljoin(url, href).split('#')[0].split('?')[0]
                        parsed_href = urlparse(normalized_href)
                        if parsed_href.scheme in ['http', 'https'] and is_valid(normalized_href) and parsed_href.netloc == domain_name and not redis_client.hexists("visited_urls", normalized_href):
                            urls.add(normalized_href)
        except Exception as e:
            log_message = f"Error fetching {url}: {str(e)}"  # Added detailed logging
            logger.error(log_message)
            await log_redis_client.publish('log_channel', log_message)  # Publish log message to Redis channel
            return Website(tld=domain_name, urls=list(urls))  # Return Website model with partial data on error

    await asyncio.sleep(0.05)  # Delay for rate limiting

    tasks = [asyncio.create_task(get_all_website_links(found_url, session, visited, semaphore)) for found_url in urls.copy() if not redis_client.hexists("visited_urls", found_url)]
    await asyncio.gather(*tasks)

    return Website(tld=domain_name, urls=list(urls))  # Return the Website model instance with the TLD and discovered URLs
