"""
This file contains the application's API with Swagger documentation
authors: Erin Hwang
"""
# TODO: do this later - subject to be deleted

from pydantic import BaseModel, HttpUrl

# Request model
class ScrapeRequest(BaseModel):
    url: HttpUrl
    source_type: str = "generic"

# Response model
class ScrapeResponse(BaseModel):
    url: str
    status: str
    content: str | None = None

class ErrorResponse(BaseModel):
    status: str = "error"
    message: str
    details: dict | None = None
