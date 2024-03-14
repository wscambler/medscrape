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
    tld: str = Field(description="The top-level domain of the website.")
    url: str = Field(description="The URL of the website.")
    text_chunk: str = Field(description="The text chunk text from the DB website.")

class Fact(BaseModel):
    fact: str = Field(...)
    substring_quote: List[str] = Field(...)

    @model_validator(mode="after")
    def validate_sources(self, info: ValidationInfo) -> "Fact":
        if info.context is None:
            return self
        text_chunks = info.context.get("text_chunk", None)
        spans = list(self.get_spans(text_chunks))
        self.substring_quote = [text_chunks[span[0] : span[1]] for span in spans]
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
    answer: List[Fact] = Field(...)

    @model_validator(mode="after")
    def validate_sources(self) -> "QuestionAnswered":
        self.answer = [fact for fact in self.answer if len(fact.substring_quote) > 0]
        return self
