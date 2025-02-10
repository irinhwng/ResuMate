"""
This file contains the controllers for the resume generator application
authors: Erin Hwang
"""
import os
import re
from app.utils.logger import LoggerConfig
from langchain.text_splitter import MarkdownHeaderTextSplitter
from datetime import datetime
from docx import Document

GENERATED_CL_PATH = os.getenv("GENERATED_CL_PATH")
CHAT_MODEL = os.getenv("CHAT_MODEL")
class CoverLetterRendererController:
    """
    Render a cover letter from a template and extracted content

    Args:
        cl_path (str): Path to base resume
        soft cos score
        extract info md
        contact_name

    Returns:
        #TODO: figure this out
    """
    pattern = r"\[[^\[\]]*\]"
    start_pattern = r"\[(?![^\[\]]*\])[^]]*$"
    end_pattern = r"^(?!.*?\[[^\[\]]*\]).*?\]"
    middle_pattern = r"^[^\[\]]*$"

    def __init__(self, cl_path: str, soft_cos_score: str, md_info: str, contact_name: str | None, source_name: str):
        self.logger = LoggerConfig().get_logger(__name__)
        self.source_name = source_name
        self.data_dir = GENERATED_CL_PATH
        self.cl_path = cl_path
        self.generated_md_content = md_info
        self.keyword_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[("#", "header"),],
            strip_headers=False)
        self.md_info = md_info
        self.soft_cos_score = soft_cos_score
        self.contact_name = contact_name
        self.data_dir = GENERATED_CL_PATH

    def align_text(self):
        """Cleanse the markdown prefix and suffix text"""
        final = {}
        keys = ["[CompanyName]", "[CityState]", "[PositionName]"]
        cleansed_text = self.md_info.replace("```markdown", "").replace("```", "").strip()
        splits = self.keyword_splitter.split_text(cleansed_text)
        assert len(splits) == 3, "Cover letter md output does not contain 3 headers"
        keywords = [each.metadata["header"] for each in splits]

        for each in list(zip(keys, keywords)):
            if "Not Available" in each[1]:
                final[each[0]] = ""
            else:
                final[each[0]] = each[1]


        return final

    def cleanse_user_input(self):
        cleansed_content = self.align_text()
        cleansed_content["[SoftCosineSimilarityScore]"] = str(self.soft_cos_score)
        cleansed_content["[Date]"] = datetime.today().strftime("%B %d, %Y")
        cleansed_content["[ModelName]"] = CHAT_MODEL

        cleansed_content["[ContactName]"] = "" if self.contact_name is None else self.contact_name
        CHAT_MODEL
        return cleansed_content

    def render_greeting(self, all_paragraphs, content_dict: dict):
        for paragraph in all_paragraphs:
            full_paragraph_text = "".join([run.text for run in paragraph.runs])

            if "Dear [" in full_paragraph_text and not content_dict["[ContactName]"]:
                all_runs = paragraph.runs
                paragraph.runs[0].text = "To whom it may concern,"
                paragraph.runs[0].font.name = "Calibri"
                paragraph.runs[0].font.size = 133350
                if len(all_runs) > 1:
                    for each_run in all_runs[1:]:
                        each_run.text = ""
                break

    def edit_paragraphs(self, all_paragraphs, i_edit_list: list[int], content_dict: dict):
        cleansed_content = content_dict
        for i_par_edit in i_edit_list:
            # print(i_par_edit)
            par = all_paragraphs[i_par_edit]
            # print(f"Paragraph {i_par} text:\n{par.text}\n-Here are the runs:")

            full_matches = []
            start_matches = []
            end_matches = []
            middle_matches = []



            for i_run, run in enumerate(par.runs):
                # print(run.text)
                full_match = [(i_run, val) for val in re.findall(self.pattern, run.text)]
                full_matches.extend(full_match)
                start_match =  [(i_run, val) for val in re.findall(self.start_pattern, run.text)]
                start_matches.extend(start_match)
                end_match =  [(i_run, val) for val in re.findall(self.end_pattern, run.text)]
                end_matches.extend(end_match)
                middle_match = [(i_run, val) for val in re.findall(self.middle_pattern, run.text)]
                middle_matches.extend(middle_match)

            if full_matches:
                # print("here")
                # print(full_matches)
                for each_full_match in full_matches:
                    # print(each_full_match[0])
                    all_paragraphs[i_par_edit].runs[each_full_match[0]].text = all_paragraphs[i_par_edit].runs[each_full_match[0]].text.replace(each_full_match[1], cleansed_content[each_full_match[1]])
                    all_paragraphs[i_par_edit].runs[each_full_match[0]].font.name = "Calibri"
                    all_paragraphs[i_par_edit].runs[each_full_match[0]].font.size = 133350

            if start_matches:
                assert len(start_matches) == len(end_matches)

                i_curr = 0
                for start, end in zip(start_matches, end_matches):

                    i_start = start[0]
                    val_start = start[1]

                    i_end = end[0]
                    val_end = end[1]

                    curr_middle_match = None if len(middle_matches) == 0 else middle_matches[i_curr]

                    if i_end - i_start >= 2:
                        assert curr_middle_match is not None
                        determined_term = val_start + curr_middle_match[1] + val_end
                        all_paragraphs[i_par_edit].runs[curr_middle_match[0]].text = all_paragraphs[i_par_edit].runs[curr_middle_match[0]].text.replace(curr_middle_match[1], "")

                        all_paragraphs[i_par_edit].runs[each_full_match[0]].font.name = "Calibri"
                        all_paragraphs[i_par_edit].runs[each_full_match[0]].font.size = 133350
                    else:
                        assert curr_middle_match is None
                        determined_term = val_start + val_start

                    # for
                    i_curr += 1

                    #replacing at the run where [ is first found
                    all_paragraphs[i_par_edit].runs[i_start].text = all_paragraphs[i_par_edit].runs[i_start].text.replace(val_start, cleansed_content[determined_term])
                    all_paragraphs[i_par_edit].runs[each_full_match[0]].font.name = "Calibri"
                    all_paragraphs[i_par_edit].runs[each_full_match[0]].font.size = 133350

                    #replace at the run where ] is found
                    all_paragraphs[i_par_edit].runs[i_end].text = all_paragraphs[i_par_edit].runs[i_end].text.replace(val_end, "")
                    all_paragraphs[i_par_edit].runs[each_full_match[0]].font.name = "Calibri"
                    all_paragraphs[i_par_edit].runs[each_full_match[0]].font.size = 133350


    @LoggerConfig().log_execution
    def execute(self):
        cleansed_content = self.cleanse_user_input()
        self.logger.info(f"Successfully cleansed both user input and model generated output. Ready to render cover letter...")

        doc = Document(self.cl_path)
        all_paragraphs = doc.paragraphs
        self.render_greeting(all_paragraphs, cleansed_content)
        self.logger.info(f"Successfully rendered greeting. Ready to render remaining inputs...")

        #collect the indices of paragraphs to edit
        i_pars_to_edit = [i_par for i_par, par in enumerate(all_paragraphs) if par.text.__contains__("[")]

        self.edit_paragraphs(all_paragraphs, i_pars_to_edit, cleansed_content)
        self.logger.info(f"Successully rendered cover letter.")

        docx_fp = f"{self.data_dir}/{self.source_name}.docx"
        docx_fp = os.path.abspath(docx_fp)

        #pprint the filepath here to determine if the correct name is bneing used

        doc.save(docx_fp)
        self.logger.info(f"Successfully saved cover letter at:\n\t\t{self.data_dir}/{self.source_name}.docx")


if __name__ == "__main__":
    t_cl_path = "/Users/erinhwang/Projects/ResuMate/experiments/base_docs/thee_cover_letter_rendrrr.docx"
    t_md = """
    ```markdown
    # Warner Bros. Discovery
    # Not Available
    # Senior Data Scientist
    ```"""
    test_render = CoverLetterRendererController(
        cl_path = t_cl_path, soft_cos_score = str(0.666), md_info = t_md, contact_name = "Sharon Ashley Poppers", source_name = "this_is_the_test"
    )

    test_render.execute()





