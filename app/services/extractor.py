"""
This file contains the applications API
authors: Erin Hwang
"""
import deepsearch as ds
from deepsearch.documents.core.export import export_to_markdown
from typing import Optional, Iterator
from pathlib import Path
from dotenv import load_dotenv
# from openai import OpenAI #TODO: remove later
from langchain_openai import ChatOpenAI

import glob
import json
import os
import zipfile
from tempfile import mkdtemp
import PyPDF2

from app.utils.logger import LoggerConfig
from app.utils.prompt_loader import initialize_prompt

class PDFExtractorDeepSearch:
    # TODO: add args and retuns in docstring
    """Convert PDF files to markdown using DeepSearch Developed by IBM Research"""

    def __init__(
        self,
        file_path: str,
        deepsearch_project_id: Optional[str] = "1234567890abcdefghijklmnopqrstvwyz123456",
    ):

        self.ds = ds
        self.export_to_markdown = export_to_markdown
        self.file_path = Path(file_path).resolve()
        self.api = self.ds.cps.client.api.CpsApi.from_env()
        self.deepsearch_project_id = deepsearch_project_id
        self.logger = LoggerConfig().get_logger(__name__)

    @LoggerConfig().log_execution
    def lazy_load(self):

        # yield self._ds_parse(self.file_path)
        _file_name = str(self.file_path).split("/")[-1]
        self.logger.info(f"Creating markdown from PDF using DeepSearch on file {_file_name}...")
        return self._ds_parse(self.file_path)

    def _ds_parse(self, filepath):
        try:
            temp_dir = mkdtemp()
            self.logger.info(f"Converting PDF using DeepSearch...")
            self.ds.convert_documents(
                api=self.api,
                proj_key=self.deepsearch_project_id,
                source_path=filepath,
                progress_bar=True,
            ).download_all(result_dir=temp_dir)

            self._unzip(temporary_directory=temp_dir)
            doc_md_str = self._export_to_markdown(temporary_directory=temp_dir)
            self.logger.info(f"Successfully converted to markdown")
            return doc_md_str
        except Exception as e:
            raise Exception(str(e))
        finally:
            # cleanup temp file and directory
            for filename in os.listdir(temp_dir):
                os.remove(os.path.join(temp_dir, filename))
            os.rmdir(temp_dir)

    def _unzip(self, temporary_directory):
        for fn in os.listdir(temporary_directory):
            if fn.endswith("zip"):
                fp_zip_str = os.path.join(temporary_directory, fn)
                with zipfile.ZipFile(fp_zip_str, "r") as fp_zip:
                    fp_zip.extractall(temporary_directory)
        self.logger.info(f"Unzipped DeepSearch results from tmp")

    def _export_to_markdown(self, temporary_directory):
        for fn in glob.glob(os.path.join(temporary_directory, "**json")):
            with open(fn, "r", encoding="utf-8") as json_fp:
                searched_documents = json.load(json_fp)
            doc_md = self.export_to_markdown(searched_documents)
            return {"tmp_source": fn, "doc_md": doc_md}

class PDFExtractorChatGPT:
    # TODO: add args and retuns in docstring
    """Extract job details verbatim using OpenAI's ChatGPT suite"""
    def __init__(self, prompt_name: str, file_path: str, model_name: str = "gpt-4o-mini"):
        self.logger = LoggerConfig().get_logger(__name__)
        self.prompt_name = prompt_name
        load_dotenv()

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            self.logger.error("OPENAI_API_KEY not found in environment variables")
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        self.model_name = model_name
        self.model = ChatOpenAI(model = self.model_name, api_key=api_key)
        self.file_path = Path(file_path).resolve()

    @LoggerConfig().log_execution
    def lazy_load(self):
        _file_name = str(self.file_path).split("/")[-1]
        self.logger.info(f"Extracting job details using GPT 4o model {_file_name}...")
        return self.extract_details()

    def read_pdf(self):
        """Extract text from a PDF file."""
        with open(str(self.file_path), 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ''
            for page in reader.pages:
                text += page.extract_text()
        return text

    def extract_details(self) -> str:
        """
        Extract details verbatim from a PDF file using OpenAI's ChatGPT API.

        Main assumption is there is only 1 input parameter for every prompt mentioned from config file
        """
        input_data = self.read_pdf()
        try:
            prompt = (initialize_prompt(self.prompt_name))[self.prompt_name]

            # Map the prompt input to the associated variables
            prompt.map_value("input_data", input_data)
            self.logger.info(prompt.description)

            if prompt.is_usable():
                self.logger.info("Starting generation job for %s", prompt.prompt_name)
                template = prompt.get_template()
                chain = template | self.model
                inputs = prompt.get_all_inputs()
                self.logger.info("LLM prompt %s \n input(s): \n %s", prompt.value, inputs)
                gpt_response = (chain.invoke(inputs)).model_dump() #TODO: change to async request later
                if gpt_response["response_metadata"]["finish_reason"] == "stop":
                    self.logger.info(
                        "%s completed it's response naturally without hitting any limits such as max tokens or stop sequence", self.model_name)
                else:
                    self.logger.info(
                        "%s completed it's response due to hitting a limit such as max tokens or stop sequence", self.model_name)
                return gpt_response["content"]

            unmapped_params = [
                parameter for parameter, value in prompt.get_all_inputs().items() if value is None
                ]
            raise ValueError(f"There is an unmapped parameter(s): {unmapped_params}")
            # prompt = f"""Extract the following information from a job posting verbatim, if available.
            # If any section or similar section is missing, explicitly state "Not Available."
            # Structure the output in the following Markdown format:
            # ```markdown
            # # Job Title
            # [Job Title Here in bullet points]
            # *If not available, state: Not Available.*

            # # Job Summary
            # [Job Summary Here in bullet points]
            # *If not available, state: Not Available.*

            # # Responsibilities
            # [Responsibilities Here in bullet points]
            # *If not available, state: Not Available.*

            # # Qualifications
            # [Qualifications Here in bullet points]
            # *If not available, state: Not Available.*

            # # Recommended Skills
            # [Recommended Skills Here in bullet points]
            # *If not available, state: Not Available.*

            # # Additional Information
            # [List any additional information that could improve the candidate's chances of a response.]
            # ```
            # Here is the job description:
            # {job_description}
            # """
        #     self.logger.info("Sending request to OpenAI API")
        #     response = self.openai_client.chat.completions.create(
        #         model="gpt-4o-mini",
        #         messages=[
        #             {"role": "system", "content": "You are a helpful assistant."},
        #             {"role": "user", "content": prompt_value},
        #             ]
        #             )

        #     # job_details = response['choices'][0]['message']['content']
        #     job_details = response.to_dict()['choices'][0]['message']['content']
        #     self.logger.info("Successfully extracted job details")
        #     return job_details

        except Exception as e:
            self.logger.error(f"Error extracting job details: {e}")
            raise

if __name__ == "__main__":
    # test_filepath = "/Users/erinhwang/Projects/ResuMate/data/Warnerbros_seniordatascientist_123456.pdf"
    test_filepath = "/Users/erinhwang/Projects/ResuMate/data/uploaded_resumes/Hwang_Erin_resumate_base.pdf"
    test_prompt_name = os.getenv("RESUME_PROMPT_NAME")
    test_extractor = PDFExtractorChatGPT(test_prompt_name, test_filepath)
    test_results = test_extractor.lazy_load()
    print(test_results)
