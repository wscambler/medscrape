import logging
import os
import lancedb
import tempfile
import requests

from typing import List, Optional
from pydantic import Field
from unstructured.partition.html import partition_html
from unstructured.partition.pdf import partition_pdf
from lancedb.embeddings import EmbeddingFunctionRegistry, get_registry
from lancedb.pydantic import Vector, LanceModel
from urllib.parse import urlparse


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# load_dotenv(override=True)

uri = os.getenv("LANCE_DB_URI")
db = lancedb.connect(uri)

# use to run OpenAI embeddings 
# openai = get_registry().get("openai")
# embed_func = openai.create(name="text-embedding-3-small")

# use local embeddings
registry = EmbeddingFunctionRegistry.get_instance()
embed_func = registry.get("sentence-transformers").create(device="cpu")

#TODO: Waiting on Ollama to release a new version with compatability for OpenAI embeddings call
# use to run ollama embeddings locally
# ollama_model="nomic-embed-text"
# base_url="http://localhost:11434"

# ollama = get_registry().get("openai")
# embed_func = ollama.create(name=ollama_model, base_url=base_url)


class ExtractedData(LanceModel):
    tld: str = Field(description="The top-level domain of the website.")
    url: str = Field(description="The URL of the website.")
    text_chunk: str = embed_func.SourceField()
    embeddings: Vector(embed_func.ndims()) = embed_func.VectorField()
    text_as_html: Optional[str] = None
    parent_id: Optional[str] = None
    category_depth: Optional[int] = None
    link_urls: Optional[List[str]] = Field(default_factory=list)
    link_texts: Optional[List[str]] = Field(default_factory=list)
    is_continuation: Optional[bool] = None

try:
    table = db.create_table("ExtractedData", schema=ExtractedData, mode="overwrite", exist_ok=True)
    logger.info("Creating ExtractedData table...")
    table.create_fts_index(["text_chunk", "text_as_html", "parent_id", "url"], replace=True)
except Exception as e:
    logger.error(f"Error during table creation or FTS index creation: {e}")
    raise

async def process_pdf_content(url, tld):
    parsed_tld = urlparse(tld).netloc if urlparse(tld).netloc else urlparse(tld).path
    extracted_data_list = []
    temp_file_path = None  # Initialize temp_file_path here
    
    try:
        # Download the PDF file
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Save the PDF to a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(response.content)
            temp_file_path = temp_file.name

        # Process the local PDF file
        elements = partition_pdf(
            filename=temp_file_path,
            url=None,  # Set url=None to run inference locally
            strategy="fast", #Can be set to "hi_res", but there are open issues in unstructured that need to be resolved
        )

        for element in elements:
            metadata = element.metadata.to_dict()
            extracted_data = {
                "tld": parsed_tld,
                "url": url,
                "text_chunk": element.text,
                "text_as_html": metadata.get("text_as_html", None),
                "parent_id": metadata.get("parent_id", None),
                "category_depth": metadata.get("category_depth", None),
                "link_urls": [],  
                "link_texts": [],
                "is_continuation": metadata.get("is_continuation", None)
            }
            extracted_data_list.append(extracted_data)

    except Exception as e:
        logger.error(f"Error processing PDF {url}: {e}")
        return
    finally:
        # Clean up the temporary file
        if temp_file_path:
            os.unlink(temp_file_path)
    
    if extracted_data_list:
        logger.info(f"Adding extracted PDF data to the table... {extracted_data_list}")
        table.add(extracted_data_list)

async def process_html_content(url, tld, include_metadata=True, ssl_verify=True, headers=None, html_assemble_articles=False):
    if headers is None:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    
    parsed_tld = urlparse(tld).netloc if urlparse(tld).netloc else urlparse(tld).path
    extracted_data_list = []
    try:
        elements = partition_html(
            url=url, 
            include_metadata=include_metadata, 
            ssl_verify=ssl_verify, 
            headers=headers, 
            html_assemble_articles=html_assemble_articles, 
            chunking_strategy="by-title",
            max_characters=1000,  
            new_after_n_chars=500,
            combine_text_under_n_chars=500,
            overlap=30
        )
        for element in elements:
            metadata = element.metadata.to_dict()
            
            extracted_data = {
                "tld": parsed_tld,
                "url": url,
                "text_chunk": element.text,
                "text_as_html": metadata.get("text_as_html", None),
                "parent_id": metadata.get("parent_id", None),
                "category_depth": metadata.get("category_depth", None),
                "link_urls": metadata.get("link_urls", []),
                "link_texts": metadata.get("link_texts", []),
                "is_continuation": metadata.get("is_continuation", None),
            }
            extracted_data_list.append(extracted_data)
            for link_url in metadata.get("link_urls", []):
                if link_url.endswith(".pdf"):
                    await process_pdf_content(link_url, tld)
    except ValueError as e:
        logger.error(f"Error processing URL {url}: {e}")
        return
    
    if extracted_data_list:
        logger.info(f"Adding extracted data to the table... {extracted_data_list}")
        table.add(extracted_data_list)

    


