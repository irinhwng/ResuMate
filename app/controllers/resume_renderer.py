"""
This file contains the controllers for the resume generator application
authors: Erin Hwang
"""

from app.utils.logger import LoggerConfig
from langchain.text_splitter import MarkdownHeaderTextSplitter
from docx import Document
import re
import json

#needs to read in docx file pertaining to UUID in main.py

class ResumeRendererController:
    ALLOWED_SECTIONS = {
        "core_expertise": r"(Core Expertise: )(.*)",
        "technical_snapshot": r"(Technical Snapshot: )(.*)",
        }
    """
    Render a resume from a template and extracted content

    Args:
        resume_path (str): Path to base resume
        extracted_content (str): Generated content from ResumeGeneratorController

    Returns:
        #TODO: figure this out
    """

    def __init__(self, resume_path: str, generated_content: dict):
        self.logger = LoggerConfig().get_logger(__name__)
        self.resume_path = resume_path
        self.generated_content = generated_content
        self.keyword_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[("#", "keywords"),],
            strip_headers=True)


    def cleanse_text(self, text: str):
        """Cleanse the markdown prefix and suffix text"""
        cleansed_text = text.replace("```markdown", "").replace("```", "").strip()
        split_text = self.keyword_splitter.split_text(cleansed_text)
        return split_text[0].page_content

    def render_keywords(self, main_doc: Document, section_name: str, new_text: str):
        """Render the keywords section of the resume"""
        if section_name not in self.ALLOWED_SECTIONS:
            self.logger.error(f"Invalid driver: {section_name}")
            raise ValueError(f"Invalid driver: {section_name}")

        for paragraph in main_doc.paragraphs:
            # Reconstruct the full text of the paragraph
            full_text = "".join([run.text for run in paragraph.runs])

            # Search for "Core Expertise: " pattern in the paragraph
            pattern = self.ALLOWED_SECTIONS[section_name]
            matches = re.search(pattern, full_text)

            if matches:
                # Extract the static part and replaceable part
                static_part = matches.group(1)
                replaceable_part = matches.group(2)

                # Iterate over runs to find and replace the replaceable part
                updated = False
                current_text = ""  # Track cumulative text in the paragraph
                for run in paragraph.runs:
                    # if not run.text.isspace():
                    current_text = current_text + run.text

                    if run.text.isspace() and static_part in current_text:
                        continue
                    if replaceable_part in current_text:
                        # if found, we need to traverse back to the previous run to make initiate the head of the run
                        # Calculate the index of the replaceable part in the current run
                        run.text = new_text
                        # start_index = current_text.find(replaceable_part)
                        # end_index = start_index + len(replaceable_part)

                        # # # Split the current run's text to replace only the match
                        # pre_text = current_text[:start_index]
                        # post_text = current_text[end_index:]

                        # # Update the run's text
                        # run.text = pre_text + new_text + post_text
                        # run.text = run.text.replace(replaceable_part, new_text)
                        # updated = True
                        return main_doc


    @LoggerConfig().log_execution
    def execute(self):
        """Execute resume rendering process"""
        doc = Document(self.resume_path)

        new_core = self.cleanse_text(self.generated_content["core_expertise"])
        new_technical = self.cleanse_text(self.generated_content["technical_snapshot"])

        doc_iter_1 = self.render_keywords(doc, "core_expertise", new_core)
        doc_iter_2 = self.render_keywords(doc_iter_1, "technical_snapshot", new_technical)

        doc_iter_2.save("/Users/erinhwang/Projects/ResuMate/experiments/rendr_test_000.docx")
        return True



if __name__ == "__main__":
    generated_content_fp = "/Users/erinhwang/Projects/ResuMate/experiments/generator_content.json"
    with open(generated_content_fp, "r") as f:
        content = json.load(f)

    resume_fp = "/Users/erinhwang/Projects/ResuMate/experiments/resume_renderer.docx"
    renderer = ResumeRendererController(resume_fp, content)
    test = renderer.execute()
