import pydantic
import re
from typing import List
from pydantic import BaseModel, Field, model_validator, ValidationInfo
from lancedb.pydantic import LanceModel


# Retrieval Models

class UserQueries(BaseModel):
    tld: str = Field(..., description="The top-level domain to pre-filter the search.")
    questions: List[str] = Field(..., description="The questions to query the language model.")

class ResponseData(LanceModel):
    url: str = Field(description="The URL of the website.")
    text_chunk: str = Field(description="The text chunk text from the DB website.")

class Fact(BaseModel):
    flag: bool = Field(..., description="Whether there was enough information to answer the question.")
    response: str = Field(..., description="The answer to the question")
    fact: str = Field(..., description="The fact that was retrieved for the question.")
    reasoning: str = Field(..., description="The reasoning for why this supports the response.")
    substring_quote: List[str] = Field(...,description="Keywords supporting the fact")
    source_url: str = Field(...)

    @model_validator(mode="after")
    def validate_sources(self, info: ValidationInfo) -> "Fact":
        if info.context is None:
            return self
        text_chunks = info.context.get("text_chunks", None)  # Corrected key from "text_chunk" to "text_chunks"
        if text_chunks is not None:
            spans = list(self.get_spans(text_chunks))
            found_quotes = [text_chunks[span[0] : span[1]] for span in spans]
            self.substring_quote = found_quotes if found_quotes else self.substring_quote
        return self

    def get_spans(self, context):
        for quote in self.substring_quote:
            yield from self._get_span(quote, context)

    def _get_span(self, quote, context):
        for match in re.finditer(re.escape(quote), context):
            yield match.span()

class QuestionAnswered(BaseModel):
    tld: str = Field(...)
    question: str = Field(...)
    answer: List[Fact] = Field(..., description="if not enough information was found to answer the question, the fact will be empty and you should note that there was not enough information to answer the question with factual proof")

    @model_validator(mode="after")
    def validate_sources(self) -> "QuestionAnswered":
        self.answer = [fact for fact in self.answer if len(fact.substring_quote) > 0]
        return self
