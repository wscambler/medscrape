import os
from urllib.parse import urlparse
import lancedb
import logging

from typing import List
from lancedb.rerankers import ColbertReranker

from .models import UserQueries, QuestionAnswered, ResponseData
from .inference import query_llm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

uri = os.getenv("LANCE_DB_URI")
db = lancedb.connect(uri)

# Move the table opening logic inside the lance_retrieval function
async def lance_retrieval(user_queries: UserQueries) -> List[QuestionAnswered]:
    """
    Performs a hybrid search in LanceDB with pre-filtering by tld and queries the language model for answers to each question.
    
    :param user_queries: UserQueries model containing the tld and questions for the search.
    :return: A list of QuestionAnswered models with the language model's responses for each question.
    """
    
    parsed_tld = urlparse(user_queries.tld)
    user_queries.tld = parsed_tld.netloc if parsed_tld.netloc else parsed_tld.path

    # Open the table here, ensuring it's done after it has been created
    table = db.open_table("ExtractedData")
    reranker = ColbertReranker(column="text_chunk")
    answers = []
    # Pre-filter by tld and perform a hybrid search for each question
    for question in user_queries.questions:
        search_results = table.search(question, query_type="hybrid", vector_column_name="embeddings") \
                                 .rerank(reranker=reranker) \
                                 .where(f"tld = '{user_queries.tld}'", prefilter=True) \
                                 .limit(10) \
                                 .to_pydantic(ResponseData)
        
        if search_results:
            combined_context = " ".join([result.model_dump_json() for result in search_results])
        else:
            default_response_data = ResponseData(text_chunk="no context found in the data for this query", url="none")
            combined_context = default_response_data.model_dump_json()
        
        question_answers = await query_llm(question, combined_context, user_queries.tld)
        answers.append(question_answers)
    
    return answers
# New method as per instructions
async def lance_search(user_queries: UserQueries) -> List[ResponseData]:
    """
    Performs a hybrid search in LanceDB with pre-filtering by tld without interacting with the query_llm function.
    
    :param user_queries: UserQueries model containing the tld and questions for the search.
    :return: A list of lists of ResponseData models with the search results for each question.
    """
    parsed_tld = urlparse(user_queries.tld)
    user_queries.tld = parsed_tld.netloc if parsed_tld.netloc else parsed_tld.path

    table = db.open_table("ExtractedData")
    reranker = ColbertReranker(column="text_chunk")
    search_results_list = []
    # Pre-filter by tld and perform a hybrid search for each question
    for question in user_queries.questions:
        search_results = table.search(question, query_type="hybrid", vector_column_name="embeddings") \
                                 .rerank(reranker=reranker) \
                                 .limit(20) \
                                 .to_pydantic(ResponseData)
        # Check if search_results list is empty before adding to search_results_list
        if search_results:
            combined_context = " ".join([result.model_dump_json() for result in search_results])
        else:
            default_response_data = ResponseData(text_chunk="no context found in the data for this query", url="none")
            combined_context = default_response_data.model_dump_json()
    
    return combined_context

