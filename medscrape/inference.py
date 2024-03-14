from openai import OpenAI
import instructor
import logging

from .models import QuestionAnswered

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


client = instructor.patch(OpenAI())

#Local Processing through Ollama — replace model with "<ollama-model-name>" in the response call
# client = instructor.patch(
#     OpenAI(
#         base_url="http://localhost:11434/v1", 
#         api_key="ollama",
#     ),
#     mode=instructor.Mode.JSON,
# )

async def query_llm(question: str, context: str, tld: str) -> QuestionAnswered:
    logger.info(f"Querying LLM with question: {question}")
    # logger.info(f"API Key being used: {api_key[:4]}...")  # Log the first few characters of the API key for security
    
    response = client.chat.completions.create(
        model="gpt-4",
        response_model=QuestionAnswered,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": "You are a world class medical research algorithm to answer questions with correct and exact citations.",
            },
            {"role": "user", "content": f"{context}"},
            {"role": "user", "content": f"Question: {question}"},
        ],
        validation_context={"text_chunk": context},
    )
    # Ensure the response is unpacked correctly
    answer = response.answer
    return QuestionAnswered(tld=tld, question=question, answer=answer)
