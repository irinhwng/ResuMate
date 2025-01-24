"""
This  file contains the applications API
authors: Erin Hwang
"""
import os
from app.utils.logger import LoggerConfig
from app.services.extractor import FileExtractorChatGPT

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
        self.extractor = FileExtractorChatGPT(prompt_name=RESUME_PROMPT_NAME, file_path=file_path)

    @LoggerConfig().log_execution
    async def process(self):
        """Execute resume loading process"""
        self.logger.info("Extracting uploaded resume...")
        resume_str = await self.extractor.extract_details()
        return resume_str
