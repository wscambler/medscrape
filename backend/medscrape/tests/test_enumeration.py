import asyncio
import aiohttp
from ..enumeration import get_all_website_links

async def test_enumeration():
    async with aiohttp.ClientSession() as session:
        website = await get_all_website_links("https://mdschool.tcu.edu/", session)
        print(f"Collected URLs from TLD: {website.tld}")
        for url in website.urls:
            print(url)

if __name__ == "__main__":
    asyncio.run(test_enumeration())
