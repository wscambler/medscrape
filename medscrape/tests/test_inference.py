import os
import pytest
from dotenv import load_dotenv
from medscrape.inference import query_llm
from medscrape.models import QuestionAnswered

# Load environment variables
load_dotenv()

@pytest.mark.asyncio
async def test_query_llm_with_api_call():
    # Ensure the API key is correctly set from .env
    api_key = os.getenv("OPENAI_API_KEY")
    assert api_key is not None, "API key is not set in .env file"

    # Call the function with test data
    # Note: Replace "What causes rain?" and the context with a suitable test case for your application
    question_answered = await query_llm("What causes rain?", "Rain is water from the sky.", "com")

    # Assertions to ensure the function behaves as expected
    # Note: These assertions might need to be adjusted based on the actual response from OpenAI
    assert isinstance(question_answered, QuestionAnswered), "The response should be an instance of QuestionAnswered"
    assert question_answered.tld == "com"
    assert question_answered.question == "What causes rain?"
    # You might want to add more assertions here based on the actual content of the response
