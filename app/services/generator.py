"""
This file contains the applications API
authors: Erin Hwang
"""
import asyncio
import os
from app.utils.logger import LoggerConfig
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

from app.utils.prompt_loader import initialize_prompt

CHAT_MODEL = os.getenv("CHAT_MODEL")

class ChatGPTRequestService:
    def __init__(self, prompt_name: str, model_name: str = CHAT_MODEL):
        self.logger = LoggerConfig().get_logger(__name__)
        self.prompt_name = prompt_name
        load_dotenv()

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            self.logger.error("OPENAI_API_KEY not found in environment variables")
            raise ValueError("OPENAI_API_KEY not found in environment variables")

        self.model_name = model_name
        self.model = ChatOpenAI(model = self.model_name, api_key=api_key)

    async def send_request(self, **kwargs):
        """
        Send a request to the ChatGPT model with the input data
        """
        try:
            prompt = (initialize_prompt(self.prompt_name))[self.prompt_name]

            # dynamically map kwargs to prompt variables
            for key, value in kwargs.items():
                prompt.map_value(key, value)
            self.logger.info(prompt.description)

            if prompt.is_usable():
                self.logger.info("Starting generation job for %s", prompt.prompt_name)
                template = prompt.get_template()
                chain = template | self.model
                inputs = prompt.get_all_inputs() #investigate this during testing
                self.logger.debug("LLM prompt %s \n input(s): \n %s", prompt.value, inputs)
                gpt_response = await chain.ainvoke(inputs)
                gpt_json = gpt_response.model_dump()
                if gpt_json["response_metadata"]["finish_reason"] == "stop":
                    self.logger.info(
                        "%s completed it's response naturally without hitting any limits such as max tokens or stop sequence", self.model_name)
                else:
                    self.logger.info(
                        "%s completed it's response due to hitting a limit such as max tokens or stop sequence", self.model_name)
                return gpt_json["content"]

            unmapped_params = [
                parameter for parameter, value in prompt.get_all_inputs().items() if value is None
                ]
            self.logger.error(f"There is an unmapped parameter(s): {unmapped_params}")
            raise ValueError(f"There is an unmapped parameter(s): {unmapped_params}")

        except Exception as e:
            self.logger.error(f"Error extracting job details: {e}")
            raise

async def test_main():
    test_job_data = "roses are red violets are blue"
    test_resume_data = ["depressing", "violent", "boisterous"]
    # tasks = []
    tasks = {}
    prompt_names = ["test1", "test2", "test3"]
    for i, section in enumerate(prompt_names):
        service = ChatGPTRequestService(prompt_name=section)
        # tasks.append(service.send_request(resume_data=test_resume_data[i], job_data=test_job_data))
        kwargs = {"resume_data": test_resume_data[i], "job_data": test_job_data}
        tasks[section] = asyncio.create_task(service.send_request(**kwargs))
    # test_responses = await asyncio.gather(*tasks)
    test_responses = await asyncio.gather(*tasks.values())
    test_results = {section: result for section, result in zip(tasks.keys(), test_responses)}
    print(test_results)

if __name__ == "__main__":
    asyncio.run(test_main())

