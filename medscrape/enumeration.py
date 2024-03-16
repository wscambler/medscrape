import re
import asyncio
import logging
import redis
import os

from pydantic import BaseModel, Field
from typing import List
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin

# Initialize Redis client (adjust parameters as needed for your Redis setup)
redis_client = redis.Redis(host=os.getenv('REDIS_HOST', 'localhost'), port=int(os.getenv('REDIS_PORT', 6379)), db=0, decode_responses=True)

class Website(BaseModel):
    tld: str = Field(..., description="The top-level domain of the website.")
    urls: List[str] = Field(..., description="The sub pages collected from the website.")

# Adjust concurrency limit based on environment variable or default to 10
CONCURRENCY_LIMIT = int(os.getenv('CONCURRENCY_LIMIT', 10))

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
    return parsed_url.netloc

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def get_all_website_links(url, session, visited=set(), semaphore=None):
    """
    Recursively finds all URLs within the same domain as the starting URL, with improved error handling and caching of visited URLs using Redis.
    """
    if semaphore is None:
        semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)  # Use environment variable or default

    # logging.info(f"Starting to fetch URLs from: {url}")  # Added detailed logging

    # Check if URL has already been visited using Redis
    if redis_client.sismember("visited_urls", url):
        logging.info(f"URL already visited, skipping: {url}")  # Added detailed logging
        return Website(tld='', urls=[])  # Return an empty Website model if URL has been visited
    logging.info(f"Visiting: {url}")
    
    # Add URL to Redis set of visited URLs
    redis_client.sadd("visited_urls", url)
    logging.info(f"Adding URL to visited set in Redis: {url}")  # Added detailed logging

    urls = set()
    domain_name = extract_tld(url)  # Replacing direct urlparse call with extract_tld function

    async with semaphore:  # Use semaphore to limit concurrency
        try:
            # logging.info(f"Fetching content for: {url}")  # Added detailed logging
            async with session.get(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}) as response:
                html_content = await response.text()
                # logging.info(f"Fetched HTML content for {url}: {html_content[:1000]}")  # Log the first 1000 characters of the HTML content
                soup = BeautifulSoup(html_content, "html.parser")
                a_tags_found = soup.findAll("a")
                # logging.info(f"Found {len(a_tags_found)} <a> tags in {url}")  # Log the number of <a> tags found
                for a_tag in a_tags_found:
                    href = a_tag.get("href")
                    if href and not should_exclude_link(href):
                        normalized_href = urljoin(url, href).split('#')[0].split('?')[0]
                        parsed_href = urlparse(normalized_href)
                        # logging.info(f"Processing URL: {normalized_href}")  # Log the URL being processed
                        if parsed_href.scheme in ['http', 'https'] and is_valid(normalized_href) and parsed_href.netloc == domain_name and not redis_client.sismember("visited_urls", normalized_href):
                            # logging.info(f"Found URL: {normalized_href}")  # Added detailed logging
                            urls.add(normalized_href)
        except Exception as e:
            logging.error(f"Error fetching {url}: {str(e)}")  # Added detailed logging
            # Implement retry logic here if needed
            return Website(tld=domain_name, urls=list(urls))  # Return Website model with partial data on error

    await asyncio.sleep(1)  # Delay for rate limiting

    tasks = []
    for found_url in urls.copy():
        if not redis_client.sismember("visited_urls", found_url):
            # logging.info(f"Making recursive call to fetch URLs from: {found_url}")  # Added detailed logging
            task = asyncio.create_task(get_all_website_links(found_url, session, visited, semaphore))
            tasks.append(task)

    if tasks:
        await asyncio.gather(*tasks)

    
    return Website(tld=domain_name, urls=list(urls))  # Return the Website model instance with the TLD and discovered URLs
