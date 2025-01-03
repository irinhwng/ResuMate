"""
This file contains the application's API with Swagger documentation
authors: Erin Hwang
"""
import os
from fastapi import FastAPI, Query, HTTPException, File, UploadFile
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from pydantic import HttpUrl
import PyPDF2
from pathlib import Path
from app.utils.logger import LoggerConfig
from uuid import uuid4

# TODO: tmp storage --> use opensearch later on (close to production)
pdf_storage = {} #key is uuiid, val is filepath

logger = LoggerConfig().get_logger(__name__)

UPLOADED_RESUME_PATH = os.getenv("UPLOADED_RESUME_PATH")
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
        title="ResuMate API",
        version="1.0.0",
        description="API documentation for job listing analysis",
        routes=app.routes,
        tags=tags_metadata
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

@app.post(
    "/upload-resume",
    tags = ["resume"],
    # response_model = str, #TODO
    summary="Upload a resume PDF file",
    description="Upload a PDF file containing resume content for generation"
    )
async def upload_resume(file: UploadFile):
    """
    Upload a resume PDF file for analysis

    Args:
        file (UploadFile): Resume PDF file

    Returns:
        str: Uploaded file name
    """
    if file.content_type != "application/pdf":
        return JSONResponse(status_code=400, content={"message": "Invalid file type. Only PDF files are allowed."})

    file_location = (Path(UPLOADED_RESUME_PATH) / file.filename).resolve()
    #generate unique id for pdf
    _file_uid = str(uuid4())

    try:
        # save the uploaded file to the resume directory
        with open(str(file_location), "wb") as f:
            f.write(await file.read())
        logger.info(f"Uploaded resume file: {file.filename}")
        pdf_storage[_file_uid] = str(file_location)
        return JSONResponse(status_code=200, content = {
            "message": "Resume uploaded successfully",
            "resumate_uuid": _file_uid
            }
            ) #TODO: response model
    except Exception as e:
        return JSONResponse(status_code=500, content={"message": f"An error occurred: {str(e)}"})

@app.get(
        "/current_resume_storage",
        tags=["resume_storage"], #TODO: this is using tmp storage
        summary="Get current resume storage",
        description="Get the current resume storage for internal testing purposes"
        )
async def get_current_resume_storage():
    """
    Returns the current state of the PDF storage
    """
    return JSONResponse(status_code=200, content=pdf_storage)

@app.post(
    "/scrape",
    tags=["scraper"],
    # response_model=ScrapeResponse, #TODO
    summary="Scrape job listing content",
    description="Scrapes content from provided job listing URL"
)
async def scrape_url(
    resumate_uuid: str = Query(
        ...,
        description = "ResuMate UUID of the uploaded resume (retrieved using /upload-resume)",
    ),
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

    if resumate_uuid not in pdf_storage:
        logger.error(f"ResuMate UUID not found in storage - please upload resume first")
        return JSONResponse(
            status_code=404,
            content={
                "message": "ResuMate UUID not found in storage - please upload resume first"
                }
                )
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
