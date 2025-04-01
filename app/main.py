"""
This file contains the application's API with Swagger documentation
authors: Erin Hwang
"""
import os
import asyncio
from fastapi import FastAPI, Query, HTTPException, File, UploadFile
from fastapi.openapi.docs import get_swagger_ui_html #remove later
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from pydantic import HttpUrl
import PyPDF2
from pathlib import Path
from app.utils.logger import LoggerConfig
from uuid import uuid4

from app.controllers.listing_loader import JobListingLoader
from app.controllers.resume_loader import ResumeLoader
from app.controllers.threshold_evaluator import SemanticSimilarityEvaluator
from app.controllers.resume_generator import ResumeGeneratorController
from app.controllers.resume_renderer import ResumeRendererController
from app.controllers.cl_generator import CoverLetterGeneratorController
from app.controllers.cl_renderer import CoverLetterRendererController
import re
from typing import Optional

# TODO:tmp storage --> use opensearch later on (close to production)
resume_storage = {"erin": "/Users/erinhwang/Projects/ResuMate/data/uploaded_resumes/thee_resume_rendrr_ace.docx"} #key is uuiid, val is filepath
cl_storage = {"erin": "/Users/erinhwang/Projects/ResuMate/data/uploaded_cls/thee_cover_letter_rendrrr_noSim.docx"}

logger = LoggerConfig().get_logger(__name__)

UPLOADED_RESUME_PATH = os.getenv("UPLOADED_RESUME_PATH")
UPLOADED_CL_PATH = os.getenv("UPLOADED_CL_PATH")
COSINE_THRESHOLD = float(os.getenv("COSINE_THRESHOLD")) #TODO: possibly remove
SOFT_COSINE_THRESHOLD = float(os.getenv("SOFT_COSINE_THRESHOLD"))

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

@app.post(
    "/upload-cover-letter",
    tags = ["cover_letter"],
    # response_model = str, #TODO
    summary="Upload a cover letter DOCX file",
    description="Upload a DOCX file containing cover letter content"
    )
async def upload_cover_letter(file: UploadFile):
    """
    Upload a cover letter DOCX file as prerequisite for cover letter rendering

    Args:
        file (UploadFile): cover letter DOCX file

    Returns:
        str: Uploaded file name
    """
    if file.content_type not in ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"]:
        return JSONResponse(
            status_code=400,
            content={
                "message": "Invalid file type. Only DOCX files are allowed."
                }
                )

    file_location = (Path(UPLOADED_CL_PATH) / file.filename).resolve()
    #generate unique id for pdf or docx
    _file_uid = str(uuid4())

    try:
        # save the uploaded file to the resume directory
        with open(str(file_location), "wb") as f:
            f.write(await file.read())
        logger.info(f"Uploaded cover letter file: {file.filename}")
        cl_storage[_file_uid] = str(file_location)
        return JSONResponse(status_code=200, content = {
            "message": "cover letter uploaded successfully",
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
async def get_current_storage():
    """
    Returns the current state of the PDF or DOCX storage
    """
    return JSONResponse(status_code=200, content={"resume": resume_storage, "cover_letter": cl_storage})

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
    ),
    cl_uuid = Query(
        default = None
    ),
    contact_name: str = Query(
        default = None,
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
            job_loader_task = job_loader.process(url)
            resume_loader_task = ResumeLoader(resume_storage[resumate_uuid]).process()

            job_data, resume_data = await asyncio.gather(job_loader_task, resume_loader_task)
            match = re.search(r"(.*?)# Additional Information", job_data, re.DOTALL)
            job_data_result = match.group(1).strip()

            semantic_scores = SemanticSimilarityEvaluator().process(resume_data, job_data_result)

            if semantic_scores["soft_cosine_similarity"] >= SOFT_COSINE_THRESHOLD:
                logger.info("Semantic similarity threshold met:\n\t%s", semantic_scores)
                #generate the content for the resume and cover letter

                #TODO: figure out the optional cover letter here - how can we determine if the cl should be rendered?
                resume_generator_task = ResumeGeneratorController(resume_data, job_data).generate_content()

                cl_keyword_extractor_task = CoverLetterGeneratorController(job_loader.file_path).process()
                resume_content, cl_keyword_md = await asyncio.gather(resume_generator_task, cl_keyword_extractor_task)

                if cl_uuid in cl_storage and cl_uuid is not None:
                    #then render cover letter as well
                    cl_renderer = CoverLetterRendererController(
                        cl_path = cl_storage[cl_uuid],
                        soft_cos_score= semantic_scores["soft_cosine_similarity"],
                        md_info = cl_keyword_md,
                        contact_name= contact_name,
                        source_name = "cl_" + job_loader.source_type,
                        )

                    cl_fp = cl_renderer.execute()
                else:
                    cl_fp = "No cover letter rendered"

                #TODO: add cl keyword (only position name here)
                resume_renderer = ResumeRendererController(
                    resume_path=resume_storage[resumate_uuid],
                    generated_content=resume_content,
                    source_name = job_loader.source_type,
                    md_info = cl_keyword_md
                    )

                resume_fp =resume_renderer.execute()



            else:
                logger.info("Semantic similarity threshold NOT met:\n\t%s", semantic_scores)
                #TODO: maybe add a response that says "not enough similarity"
                return {
                    "status": "Semantic similarity threshold NOT met",
                    "url": str(url),
                    # "content": semantic_scores["soft_cosine_similarity"], #figure out how to raise this.. jsondecode error
                    # "semantic_similarity": semantic_scores
                }
            return {
                "status": "success",
                "url": str(url),
                "resume_filepath": resume_fp,
                "cover_letter_filepath": cl_fp,
            }
        else:
            return JSONResponse(
                status_code=404,
                content={
                    "message": "Resume UUID not found. Please upload a resume first."
                }
            )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "status": "error",
                "message": str(e) #this may be json encodable
            }
        )

@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint"""
    return {"status": "online"}

#TODO: checks if making calls is even worth it? lets not waste ppls time........
