"""
This  file contains the applications API
authors: Erin Hwang
"""
from typing import Dict, Any
from openai import OpenAI
from dotenv import load_dotenv
import os

from app.utils.logger import LoggerConfig
from app.services.scraper import JobScraperService
from app.services.extractor import PDFExtractorDeepSearch, PDFExtractorChatGPT
from langchain.document_loaders import PyPDFLoader

DEFAULT_DRIVER = "chrome"



class JobListingLoader:
    """Load job listings from various sources"""

    def __init__(self, url: str, **kwargs: Dict[str, Any]):
        self.logger = LoggerConfig().get_logger(__name__)
        self.scraper = JobScraperService(driver = DEFAULT_DRIVER)
        self.extractor = None
        self.url = url

        # extract kwargs with default
        self.company_name = kwargs.get("company_name", "default")
        self.job_title = kwargs.get("job_title", "default")
        self.job_id = kwargs.get("job_id", "default")

        self.source_type = (self.company_name + "_" + self.job_title + "_" + self.job_id).replace(" ", "")


        # api_key = os.getenv("OPENAI_API_KEY")
        # if not api_key:
        #     raise ValueError("OPENAI_API_KEY not found in environment variables")

        # self.openai_client = OpenAI(
        #     api_key=api_key
        # )

    def _convert_listing(self):
        """Create PDF of a job listing content from a URL"""
        self.logger.info(f"Creating PDF from URL listing...")
        pdf_path = self.scraper.execute(str(self.url), self.source_type) #TODO
        return pdf_path

    def _extract_pdf(self, pdf_path: str):
        """Load job listing content into markdown str from a PDF file"""
        if self.extractor is None:
            # self.extractor = PDFExtractorDeepSearch(pdf_path) #TODO
            self.extractor = PDFExtractorChatGPT(pdf_path)
        job_str = self.extractor.lazy_load()
        return job_str

    def _extract_text(self, job_str):
        """Extract text from job listing content"""

    @LoggerConfig().log_execution
    def execute(self):
        """Execute job listing loading process"""
        pdf_path = self._convert_listing()
        job_str = self._extract_pdf(pdf_path)
        return job_str


