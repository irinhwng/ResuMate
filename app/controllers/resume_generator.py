"""
This file contains the controllers for the resume generator application
authors: Erin Hwang
"""
import re
import asyncio
from app.utils.logger import LoggerConfig
from langchain.text_splitter import MarkdownHeaderTextSplitter
from app.services.generator import ChatGPTRequestService
import os

N_PRIMARY_BULLETS= os.getenv("N_PRIMARY_BULLETS")
N_SECONDARY_BULLETS= os.getenv("N_SECONDARY_BULLETS")

class ResumeGeneratorController:
    """
    Generates a resume from a given set of skills and job descriptions

    Args:
        resume_data (str): The base resume data to generate the resume from
        job_data (str): The job descriptions to generate the resume from
    """

    def __init__(self, resume_data: str, job_data: str):
        self.logger = LoggerConfig().get_logger(__name__)
        self.resume_data = self.cleanse_text(resume_data)
        self.job_data = self.cleanse_text(job_data)
        self.splitter =  MarkdownHeaderTextSplitter(headers_to_split_on=[
            ("#", "Core Expertise"), #TODO: bring it to config file?
            ("#", "Technical Snapshot"),
            ("##", "Professional Experience")
            ], strip_headers=False)

    def cleanse_text(self, text: str):
        """Cleanse the markdown prefix and suffix text"""
        return text.replace("```markdown", "").replace("```", "").strip()

    def split_md_text(self):
        """Split the markdown text into sections"""
        sections = self.splitter.split_text(self.resume_data)
        results = {}
        for section in sections:
            if section.page_content.startswith("# Core Expertise"):
                results["core_expertise"] = section.page_content
            elif section.page_content.startswith("# Technical Snapshot"):
                results["technical_snapshot"] = section.page_content
            else:
                if "professional_experience" not in results:
                    results['professional_experience'] = [section.page_content]
                else:
                    results["professional_experience"].append(section.page_content)
        professional_data = '\n\n'.join(results["professional_experience"])
        return results, professional_data

    def extract_title(self, text: str):
        """Extract the title from the markdown text"""
        pattern = r"##\s*(.*)"
        match = re.search(pattern, text)
        if match:
            return match.group(1)
        else:
            self.logger.error("Title not found in resume text")
            raise ValueError("Title not found in resume text")

    @LoggerConfig().log_execution
    async def generate_content(self):
        """Execute resume generation process"""
        resume_sections, professional_data = self.split_md_text()
        tasks = {}

        #start the async generations here
        for prompt_name, base_section in resume_sections.items():
            #define prompt kwargs here
            service = ChatGPTRequestService(prompt_name = prompt_name)

            if prompt_name in ["core_expertise", "technical_snapshot"]:
                kwargs = {
                    "job_data": self.job_data,
                    "professional_data": professional_data,
                    "base_section": base_section
                    }
                tasks[prompt_name] = asyncio.create_task(service.send_request(**kwargs))
                self.logger.info("Creating generation task for %s", prompt_name)
            elif prompt_name == "professional_experience":
                # iterate over each section in professional experience
                for idx, exp_section in enumerate(base_section, start=1):
                    task_name = self.extract_title(exp_section)
                    n_bullets = N_PRIMARY_BULLETS if "AI Center of Competence" in task_name else N_SECONDARY_BULLETS #TODO: highest priority if others are interested in usnig this
                    kwargs = {
                        "job_data": self.job_data,
                        "base_section": exp_section,
                        "n_bullets": n_bullets
                    }
                    tasks[task_name] = asyncio.create_task(service.send_request(**kwargs))
                    self.logger.info("Creating generation task for %s", task_name)
            else:
                self.logger.error(
                    "Prompt name %s not found - ensure prompt %s exists in the config file",
                    prompt_name,
                    prompt_name
                    )
                raise ValueError("Prompt name %s not found", prompt_name)

        responses = await asyncio.gather(*tasks.values())
        results = {section: result for section, result in zip(tasks.keys(),responses)}
        return results

    # 1: Core Expertise
        # full job_data
        # entire professional experience
        # base section (core expertise)
    # 2: Technical Snapshot
        # full job_data
        # entire professional experience
        # base section (technical snapshot)
    # 3: Professional Experience n
        # full job_data
        # base section (professional experience n)
    # 4: Professional Experience 2
    # 5: Professional Experience 3
        print("DA!")


async def main():
    job_data = '```markdown\n# Job Title\n- Senior Data Scientist\n\n# Job Summary\n- We are looking for a Senior Data Scientist to join our Inventory Buyer Experience team.\n- This team’s focus is helping buyers easily evaluate key information about our listings and crafting a delightful personalized shopping experience.\n- Evaluate opportunities to improve web and app experiences for buyers and apply sophisticated analytical techniques.\n- Conduct and evaluate experiments to drive decision-making about products and features.\n- Full-time position reporting to the Manager, Product Analytics.\n\n# Responsibilities\n- Partner and work collaboratively with the cross-functional Inventory Buyer Experience team.\n- Identify opportunities to improve buyer experiences and drive decision-making with partners.\n- Design and analyze rigorous experiments, set hypotheses, and deliver robust analysis of experiment results.\n- Transform raw data into meaningful and impactful analysis with strong data governance and clear documentation.\n- Design metrics to ensure robust measurement of product performance.\n- Build foundational data sets using SQL and database skills.\n- Craft dashboards and visualizations using Looker and impactful presentations for senior leaders.\n\n# Qualifications\n- 4+ years experience as a data scientist or data analyst with experience in extracting meaning from big data sets.\n- Successful track record of guiding product teams to identify high-impact opportunities and make data-driven decisions.\n- Mastery of SQL and proficiency in R/Python.\n- Deep understanding of experimentation theory and practical experience in designing and analyzing online experiments.\n- Proficiency with Looker, Tableau, or other data visualization software.\n\n# Preferred Qualifications\n- Experience working in a two-sided marketplace environment preferred.\n- Passionate to try new approaches to advance technical skills.\n- Specialize in sophisticated analyses and regularly use statistical methods.\n- Ability to distill complex problems into concise, actionable narratives.\n\n# Additional Information\n- Salary Range: $136,000.00 - $176,000.00.\n- Eligible for an equity package, an annual performance bonus, and competitive benefits.\n- This role requires presence in Etsy’s Brooklyn Office once or twice per week.\n- Etsy values diversity, equity, and inclusion in the workplace and encourages people from all backgrounds to apply.\n```'

    resume_data = '```markdown\n# Core Expertise\nArtificial Intelligence & Machine Learning (AI/ML), Cloud Computing, Data Science, Computer Programming, Data Analysis & Modeling, Neural Networks, Software as a Service (SaaS), Cross-Functional Collaboration, Problem Solving\n\n# Technical Snapshot\nPython OOP, CouchDB, OpenShift, Docker, Scikit-Learn, Langchain, TensorFlow, Panda tools, Git/Gitlab, Stata, Jupyter\n\n# Professional Experience\n\n## Data Scientist – Security Software (AI Center of Competence) at IBM\nUtilized technical expertise to advance IBM’s data science capabilities by harnessing modern technologies, specifically AI/ML. Developed prototypes into integral components of the SaaS product roadmap. Collaborated across numerous functions to refactor code/architecture, devise the continuous training pipeline, and build model card performance, among many others.\n\n### Product Feature 1: Threat Management SaaS Traditional ML Feature\n- Designed and implemented an end-to-end backend training pipeline for a SaaS traditional ML cybersecurity feature, encompassing data engineering, model training, and automated deployment.\n- Identified and resolved disruptive server memory leak previously unsolved by the DevOps team, reducing memory usage by 30% while enabling server to scale up to concurrent calls in the ten thousands without restarting. \n- Key contributor to ML feature development for the SaaS threat management platform; constructed automated data pipelines for the ML retraining application and wrote a widely used script for database logging to track ML pipeline status. \n- Improved the recall score of the deployed model while addressing performance issues, meeting both stability and business-critical accuracy requirements.\n- Developed a compliance-driven process for generating model cards to document data lineage, training metadata, and performance metrics, ensuring regulatory transparency.\n- Automated the evaluation of model performance thresholds and data engineering tests to enable seamless integration of updated models into production.\n- Created a CouchDB-based storage solution for model cards, facilitating the development of an internal frontend for real-time monitoring and compliance verification.\n- Collaborated with DevOps to integrate Dockerized ML pipelines into an OpenShift custom operator architecture, ensuring scalable automation infrastructure.\n- Utilized Python, scikit-learn, and TensorFlow with an emphasis on object-oriented programming (OOP) to build reusable and maintainable code modules.\n\n### Product Feature 2: Threat Management SaaS GenaAI Summarization Feature\n- Built an asynchronous framework to automate case summarization workflows for a SaaS GenAI cybersecurity feature.\n- Improved cybersecurity case summary quality by 35%; allowed IBM’s large language models (LLMs) to focus on specific tasks using generative AI to manage anomalous/malicious threat incidents and artifacts during ML feature development. \n- Designed and implemented single-shot and multi-shot summarization algorithms capable of handling edge cases, including scenarios with either excessive or minimal text, ensuring consistent and accurate outputs for varying business personas.\n- Automated data preprocessing and document generation pipelines as part of the summarization algorithms, transforming raw data into structured formats for seamless integration into workflows.\n- Created APIs with middleware to support end-to-end data workflows, enabling streamlined ingestion, processing, and delivery of summarization outputs with enhanced scalability and efficiency.\n- Developed a scalable internal package with reusable and modular components tailored for adoption by other security SaaS products, enabling efficient handling of diverse data types generated by multiple security products, which served as a template for a Python package used across product development teams.\n- Utilized advanced generative AI techniques to engineer a robust summarization system, highlighting the ability to integrate algorithms and workflows into high-impact applications for diverse organizational needs.\n\n### Product Feature 3 (prototype level): Data Protection SaaS Deep Learning Feature\n- Led the prototyping development of a data compliance feature leveraging deep learning techniques for a SaaS-based data protection platform.\n- Designed and implemented a solution to identify SQL queries related to data risks, such as deletion, truncation, and obfuscation, ensuring compliance with regulations like the Sarbanes–Oxley Act and DORA.\n- Developed a core backend prototype that encoded SQL queries and descriptions of monitored changes into embeddings using Sentence Transformers, enabling efficient similarity analysis.\n- Calculated cosine similarity to identify high-probability matches between SQL queries and predefined compliance risks, achieving accurate and actionable results.\n- Advocated for and successfully demonstrated the use of embeddings and similarity distances, persuading staff engineers to adopt this cost-effective and secure approach over large language models (LLMs).\n- Proved the feasibility of deep learning techniques for compliance feature development, reducing the need for external LLM calls, thereby lowering costs and enhancing data security.\n\n## Client Success Manager (CSM) – Data & AI Chapter Lead at IBM\nContinuously evolved CSM organization by leveraging AI and broader technical expertise to build robust processes/solutions.\n- Created packaged data science asset for technical sellers with grocery and convenience store accounts, showcasing language preprocessing and modeling capabilities via streamlined Python scripts.\n- Oversaw CSMs intake forms requesting proof of concept (PoC) support; used IBM’s proprietary SDKs like Watson Machine Learning and Watson OpenScale to ensure process excellence.\n- Gained requisite OpenShift and Kubernetes knowledge to effectively communicate with cluster administrators in testing containerized data science applications.\n\n## Junior Data Scientist - Cloud Pack Acceleration Team at IBM\nOperated efficiently in a dynamic team environment focused on building solutions to expedite IBM Cloud functions. \n- Implemented web scraping pipeline for IBM Cloud by cleaning/aggregating data for multiple company name versions, reducing variability by ~30%.\n- Co-created a packaged healthcare data science project using IBM’s proprietary platform (Cloud Pak for Data) and open-source tools still widely used by technical sellers.\n- Shaped development of final image recognition model iteration for a client using satellite images to detect aircraft lots.\n```'

    import json

    test_controller = ResumeGeneratorController(resume_data, job_data)
    test = await test_controller.generate_content()
    test_filepath = "/Users/erinhwang/Projects/ResuMate/experiments/generator_content.json"
    with open(test_filepath, "w") as fp:
        json.dump(test, fp)
    print("JA!")




if __name__ == "__main__":
    asyncio.run(main())
