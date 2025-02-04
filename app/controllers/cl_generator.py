"""
This file contains the controllers for the reusme generator application
authors: Erin Hwang
"""

import asyncio
import os
from dotenv import load_dotenv
from app.utils.logger import LoggerConfig
from app.services.extractor import FileExtractorChatGPT

load_dotenv()
CL_EXTRACTOR_PROMPT_NAME = os.getenv("CL_PROMPT_NAME")

class CoverLetterGeneratorController:
    """
    Generates keywords based on the raw string of the job listing.
    The primary use is for the cover letter. The only content being generated is the ability for
    the model to extract the following information:

    - Company Name
    - City, State
    - Position Name

    Args:
        file_path: file path to the interested job listing

    Returns:
        str: The extracted job listing content
    """

    def __init__(self, file_path:str):
        self.file_path = file_path
        self.logger = LoggerConfig().get_logger(__name__)
        self.extractor = FileExtractorChatGPT(
            prompt_name = CL_EXTRACTOR_PROMPT_NAME,
            file_path = file_path
            )

    @LoggerConfig().log_execution
    async def process(self):
        """Execute the cover letter loading process"""
        self.logger.info("Extracting job listing keywords for cover letter...")
        cl_str = await self.extractor.extract_details()
        return cl_str

async def test_cl_extractor():
    """testing the cover letter extractor"""

    test_path = "/Users/erinhwang/Projects/ResuMate/data/job_listings/testCompany_test_jobTitle_000.pdf"
    # test_path = "/Users/erinhwang/Projects/ResuMate/data/job_listings/verizon_srdatascientist_000.pdf"
    worker = CoverLetterGeneratorController(test_path)
    cl_str = await worker.process()
    print('FIN!')

if __name__ == "__main__":
    asyncio.run(test_cl_extractor())



