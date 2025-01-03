"""
This file contains the applications API
authors: Erin Hwang
"""
import json
from app.utils.logger import LoggerConfig
from app.schemas.prompt import Prompt
from app.schemas.prompt_data import PromptData

logger = LoggerConfig().get_logger(__name__)

def initialize_prompt(prompt_name: str, prompt_config_filepath: str = "app/config/prompts.json") -> dict[str]:
    """Returns dictionary of prompts

    Args:
        prompt_name (str): Name of the prompt to initialize
        prompt_config_filepath (str, optional): Config file that contains the prompt data.
            Defaults to "config/prompts.json".

    Returns:
        dict[str]: A dictionary of prompts, initialized against the prompt config

    """
    # pull data from file
    with open(prompt_config_filepath, "r", encoding="utf-8") as f:
        prompt_list = json.load(f)
    initialized_prompts: dict[str, Prompt] = {}

    # Parse the prompt data
    for prompt_dict in prompt_list:
        if prompt_dict["prompt_name"] == prompt_name:
            initialized_prompts[prompt_dict["prompt_name"]] = Prompt(
                prompt_data=PromptData(**prompt_dict))
            logger.info(f"Prompt {prompt_name} initialized from config file")
            return initialized_prompts
    logger.error(f"Prompt {prompt_name} not found in config file")
    raise ValueError(f"Prompt {prompt_name} not found in config file")

if __name__ == "__main__":
    test_initialized_prompt = initialize_prompt("job_listing_extractor")
    print('test ends here')
    # print(test_initialized_prompt["prompt_value"])
