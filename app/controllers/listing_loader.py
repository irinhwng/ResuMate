"""
This  file contains the applications API
authors: Erin Hwang
"""
from typing import Dict, Any
import os

from app.utils.logger import LoggerConfig
from app.services.scraper import JobScraperService
from app.services.extractor import FileExtractorChatGPT

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

    def _convert_listing(self, url: str):
        """Create PDF of a job listing content from a URL"""
        self.logger.info(f"Creating PDF from URL listing...")
        pdf_path = self.scraper.execute(str(url), self.source_type) #TODO
        return pdf_path

    def _extract_pdf(self, pdf_path: str):
        """Extract job listing content into str from a PDF file"""
        if self.extractor is None:
            self.extractor = FileExtractorChatGPT(prompt_name=JOB_LISTING_PROMPT_NAME, file_path=pdf_path)
        job_str = self.extractor.lazy_load()
        return job_str

    def _extract_text(self, job_str): #TODO: remove
        """Extract text from job listing content"""

    @LoggerConfig().log_execution
    def process(self, url: str):
        """Execute job listing loading process"""
        pdf_path = self._convert_listing(url)
        job_str = self._extract_pdf(pdf_path)
        return job_str


