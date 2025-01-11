"""
This file contains the application's API with Swagger documentation
authors: Erin Hwang
"""
import os
import asyncio
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
resume_storage = {} #key is uuiid, val is filepath

logger = LoggerConfig().get_logger(__name__)

UPLOADED_RESUME_PATH = os.getenv("UPLOADED_RESUME_PATH")
# from app.services.scraper import JobScraperService
from app.controllers.listing_loader import JobListingLoader
from app.controllers.resume_loader import ResumeLoader
from app.controllers.threshold_evaluator import SemanticSimilarityEvaluator

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
    summary="Upload a resume PDF or DOCX file",
    description="Upload a PDF or DOCX file containing resume content for AI generation"
    )
async def upload_resume(file: UploadFile):
    """
    Upload a resume PDF or DOCX file as prerequisite for resume analysis and generation

    Args:
        file (UploadFile): Resume PDF or DOCX file

    Returns:
        str: Uploaded file name
    """
    if file.content_type not in ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
        return JSONResponse(
            status_code=400,
            content={
                "message": "Invalid file type. Only PDF or DOCX files are allowed."
                }
                )

    file_location = (Path(UPLOADED_RESUME_PATH) / file.filename).resolve()
    #generate unique id for pdf or docx
    _file_uid = str(uuid4())

    try:
        # save the uploaded file to the resume directory
        with open(str(file_location), "wb") as f:
            f.write(await file.read())
        logger.info(f"Uploaded resume file: {file.filename}")
        resume_storage[_file_uid] = str(file_location)
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
    Returns the current state of the PDF or DOCX storage
    """
    return JSONResponse(status_code=200, content=resume_storage)

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
    try:
        if resumate_uuid in resume_storage:


            job_loader = JobListingLoader(
                **{
                    "company_name": company_name,
                    "job_title": job_title,
                    "job_id": job_id
                    }
                    )
            job_data = job_loader.process(url)
            resume_data = ResumeLoader(resume_storage[resumate_uuid]).process()
            print(" ERIN "*10)
            semantic_evaluator = SemanticSimilarityEvaluator().process(resume_data, job_data)
            (semantic_scores) = await asyncio.gather(semantic_evaluator)
            print(semantic_scores)
            #TODO: create threshold controller
            # pseudo code ThresholdEvaluatorController.evaluate(job_data, resume_data)
            return {
                "status": "success",
                "url": str(url),
                "content": job_data
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
