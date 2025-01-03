"""
This  file contains the applications API
authors: Erin Hwang
"""
import os
from app.utils.logger import LoggerConfig
from app.services.extractor import PDFExtractorChatGPT

RESUME_PROMPT_NAME = os.getenv("RESUME_PROMPT_NAME")

class ResumeLoader:
    """
    Loads resume content from a PDF file to extract relevant skills verbatim

    Args:
        file_path (str): Path to the PDF file to load

    Returns:
        str: The extracted resume content
    """

    def __init__(self, file_path: str):
        self.logger = LoggerConfig().get_logger(__name__)
        self.extractor = PDFExtractorChatGPT(prompt_name=RESUME_PROMPT_NAME, file_path=file_path)

    @LoggerConfig().log_execution
    def execute(self):
        """Execute resume loading process"""
        resume_str = self.extractor.lazy_load()
        return resume_str
