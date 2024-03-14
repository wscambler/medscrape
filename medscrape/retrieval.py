import os
from urllib.parse import urlparse
import lancedb
import logging

from typing import List

from .models import UserQueries, QuestionAnswered, ResponseData
from .inference import query_llm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

uri = os.getenv("LANCE_DB_URI")
db = lancedb.connect(uri)

# Move the table opening logic inside the lance_search function
async def lance_search(user_queries: UserQueries) -> List[QuestionAnswered]:
    """
    Performs a hybrid search in LanceDB with pre-filtering by tld and queries the language model for answers to each question.
    
    :param user_queries: UserQueries model containing the tld and questions for the search.
    :return: A list of QuestionAnswered models with the language model's responses for each question.
    """
    # Logging at the beginning of lance_search to confirm when it's called
    print("lance_search function is called")
    
    # Check if tld is already parsed
    if not urlparse(user_queries.tld).scheme:
        parsed_tld = urlparse(user_queries.tld)
        user_queries.tld = parsed_tld.netloc
    else:
        user_queries.tld = urlparse(user_queries.tld).netloc

    # Open the table here, ensuring it's done after it has been created
    table = db.open_table("ExtractedData")

    answers = []
    # Pre-filter by tld and perform a hybrid search for each question
    for question in user_queries.questions:
        search_results = table.search(question, query_type="hybrid", vector_column_name="embeddings") \
                                 .where(f"tld = '{user_queries.tld}'", prefilter=True) \
                                 .limit(20) \
                                 .to_pydantic(ResponseData)
        
        # Combine text chunks from search results for context
        combined_context = " ".join([result.text_chunk for result in search_results])
        
        # Query the language model with the combined context and the question
        question_answers = await query_llm(question, combined_context, user_queries.tld)
        answers.append(question_answers)
    
    return answers
