import os
import asyncio
from urllib.parse import urlparse
from dotenv import load_dotenv  # Import load_dotenv

from ..processing import process_html_content

# Call load_dotenv at the beginning of the script
load_dotenv()

async def test_process_html_content():
    url = "https://mdschool.tcu.edu/"  # Use a real URL relevant to your project
    tld = urlparse(url).netloc  # Extracts the domain name (tld) from the URL
    await process_html_content(url, tld)
    print("Test completed successfully.")

if __name__ == "__main__":
    asyncio.run(test_process_html_content())