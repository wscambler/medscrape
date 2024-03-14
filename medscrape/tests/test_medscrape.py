import asyncio
import pytest  # Added pytest for enhanced test messages
from medscrape.main import medscrape
from medscrape.models import UserQueries


# The previously prepared UserQueries object
tld = "https://mdschool.tcu.edu/"
questions = [
    "Is there a dedicated orthopaedics clerkship mentioned for this Medical School?",
    "Are there any dedicated orthopaedics electives mentioned for this Medical School?",
    "What is the dedicated musculoskeletal curriculum for this Medical School?",
    "Does the Medical School have an emphasis on primary care?",
    "Is there a dedicated family medicine clerkship mentioned for this Medical School?",
]
user_queries = UserQueries(tld=tld, questions=questions)

async def main():
    await medscrape(user_queries)

@pytest.mark.asyncio
async def test_main():
    await main()

if __name__ == "__main__":
    asyncio.run(main())