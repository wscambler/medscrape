import json
import instructor
import logging
import redis.asyncio as redis
import os

from openai import OpenAI
from .models import QuestionAnswered

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Redis setup for publishing logs
REDIS_URL = os.getenv('REDIS_URL', 'redis://redis:6379/0')
log_redis_client = redis.from_url(REDIS_URL, encoding="utf-8", decode_responses=True)

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
    log_message = f"Querying LLM with question: '{question}' and using context: '{context}'"
    logger.info(log_message)
    await log_redis_client.publish('log_channel', log_message)
    
    response = client.chat.completions.create(
        model="gpt-4",
        response_model=QuestionAnswered,
        temperature=0,
        messages=[
            {
                "role": "system",
                "content": """ You are a world class medical research algorithm designed to answer questions with correct and exact citations.
                        Provide the most accurate and relevant information for the question provided.
                        """,
            },
            {"role": "user", "content": f"{context}"},
            {"role": "user", "content": f"Question: {question}"},
        ],
        validation_context={"text_chunk": context},
    )
    # Ensure the response is unpacked correctly
    answer = response.answer
    return QuestionAnswered(tld=tld, question=question, answer=answer)
