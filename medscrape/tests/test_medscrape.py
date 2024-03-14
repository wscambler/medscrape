import asyncio
import pytest  # Added pytest for enhanced test messages
from medscrape.main import medscrape
from medscrape.models import UserQueries


# The previously prepared UserQueries object
tld = "https://med.stanford.edu"
questions = [
    "What are the core values for this Medical School?",
    "What research has this med school performed Medical School?",
    "What is the curriculum for first year students at this Medical School?",
    "Does the Medical School have an emphasis on primary care?",
]
user_queries = UserQueries(tld=tld, questions=questions)

async def main():
    await medscrape(user_queries)

@pytest.mark.asyncio
async def test_main():
    await main()

if __name__ == "__main__":
    asyncio.run(main())