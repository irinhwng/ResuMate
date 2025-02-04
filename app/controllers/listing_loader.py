"""
This file contains the applications API
authors: Erin Hwang
"""
from typing import Dict, Any
import os

from app.utils.logger import LoggerConfig
from app.services.scraper import JobScraperService
from app.services.extractor import FileExtractorChatGPT
import asyncio

WEBDRIVER = os.getenv("WEBDRIVER")
JOB_LISTING_PROMPT_NAME = os.getenv("JOB_LISTING_PROMPT_NAME")



class JobListingLoader:
    # TODO: add args and retuns in docstring
    """Load job listings from various sources"""

    def __init__(self, **kwargs: Dict[str, Any]):
        self.logger = LoggerConfig().get_logger(__name__)
        self.scraper = JobScraperService(driver = WEBDRIVER)
        self.extractor = None

        # extract kwargs with default
        self.company_name = kwargs.get("company_name", "default")
        self.job_title = kwargs.get("job_title", "default")
        self.job_id = kwargs.get("job_id", "default")

        self.source_type = (self.company_name + "_" + self.job_title + "_" + self.job_id).replace(" ", "")
        self.file_path = None

    async def _convert_listing(self, url: str):
        """Create PDF of a job listing content from a URL"""
        self.logger.info(f"Creating PDF from URL listing...")
        pdf_path = await self.scraper.execute(str(url), self.source_type)
        return pdf_path

    async def _extract_pdf(self, pdf_path: str):
        """Extract job listing content into str from a PDF file"""
        if self.extractor is None:
            self.extractor = FileExtractorChatGPT(prompt_name=JOB_LISTING_PROMPT_NAME, file_path=pdf_path)
        job_str = await self.extractor.extract_details()
        return job_str

    @LoggerConfig().log_execution
    async def process(self, url: str):
        """Execute job listing loading process"""
        pdf_path = await self._convert_listing(url)
        self.file_path = pdf_path
        job_str = await self._extract_pdf(pdf_path)
        return job_str

async def test_main():
    job_loader = JobListingLoader(
        **{
            "company_name": "test_comapny",
            "job_title": "test_title",
            "job_id": "test_id"
            }
            )
    test_url = "https://careers.etsy.com/jobs/senior-data-scientist-new-york-united-states-bee7221c-bf38-4b04-8557-7fdaacfc8d8d"
    job_data = await job_loader.process(test_url)

    print(job_data)

if __name__ == "__main__":
    asyncio.run(test_main())



