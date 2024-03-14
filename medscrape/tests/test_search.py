import asyncio
import pytest  # Added pytest for enhanced test messages
from medscrape.models import UserQueries
from medscrape.retrieval import lance_search
from medscrape.inference import query_llm


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


@pytest.mark.asyncio
async def test_lance_search_and_query_llm():
    # Call the functions with the test data
    answers = await lance_search(user_queries)
    for question, answer in zip(user_queries.questions, answers):
        print(f"Q: {question}\nA: {answer}\n")

    # Assertions to verify the expected outcomes
    assert answers is not None, "lance_search did not return results"
        

