"""
This file contains the application's API with Swagger documentation
authors: Erin Hwang
"""

from fastapi import FastAPI, Query, HTTPException
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from pydantic import HttpUrl

# from app.services.scraper import JobScraperService
from app.controllers.listing_loader import JobListingLoader

tags_metadata = [
    {
        "name": "health",
        "description": "Health check endpoints"
    },
    {
        "name": "scraper",
        "description": "Job listing scraping operations"
    }
]

app = FastAPI(
    title="ResuMate API",
    description="API for job listing scraping and analysis",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=tags_metadata
)

# Custom OpenAPI schema configuration
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Resumate API",
        version="1.0.0",
        description="API documentation for job listing analysis",
        routes=app.routes,
        tags=tags_metadata
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

@app.post(
    "/scrape",
    tags=["scraper"],
    # response_model=ScrapeResponse, #TODO
    summary="Scrape job listing content",
    description="Scrapes content from provided job listing URL"
)
async def scrape_url(
    url: HttpUrl = Query(
        ...,
        description="URL of the job listing to scrape",
        example="https://example.com/job-posting"
    ),
    company_name: str = Query(
        default="generic",
        description="Type of job listing source",
        example="linkedin"
    ),
    job_title: str = Query(
        default="generic",
        description="Job title",
        example="staff data scientist"
    ),
    job_id: str = Query(
        default="generic",
        description="Job ID",
        example="123456"
    )
):
    """
    Scrape job listing content from URL

    Args:
        request (ScrapeRequest): URL and metadata for scraping

    Returns:
        ScrapeResponse: Scraped content and status
    """
    try:
        job_data_loader = JobListingLoader(
            url,
            **{
                "company_name": company_name,
                "job_title": job_title,
                "job_id": job_id
                }
                )
        result = job_data_loader.execute()

        if "error" in result:
            raise HTTPException(
                status_code=500,
                detail={
                    "status": "error",
                    "message": "Scraping failed",
                    "details": result
                }
            )

        return {
            "status": "success",
            "url": str(url),
            "content": result
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": str(e)
            }
        )

@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "online"}

#TODO: checks if making calls is even worth it? lets not waste ppls time
