import asyncio
import pytest  # Added pytest for enhanced test messages
from medscrape.models import UserQueries
from medscrape.retrieval import lance_retrieval
from medscrape.inference import query_llm


# The previously prepared UserQueries object
tld = "https://med.stanford.edu"
questions = [
    "What are the core values for this Medical School?",
    "What research has this med school performed Medical School?",
    "What is the curriculum for first year students at this Medical School?",
    "Does the Medical School have an emphasis on primary care?",
]
user_queries = UserQueries(tld=tld, questions=questions)


@pytest.mark.asyncio
async def test_lance_retrieval_and_query_llm():
    # Call the functions with the test data
    answers = await lance_retrieval(user_queries)
    for question, answer in zip(user_queries.questions, answers):
        print(f"Q: {question}\nA: {answer}\n")

    # Assertions to verify the expected outcomes
    assert answers is not None, "lance_retrieval did not return results"
        

