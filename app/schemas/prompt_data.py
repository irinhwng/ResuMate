"""
This file contains the Pydantic class data model for the prompt data
authors: Erin Hwang
"""

from typing import Optional

from pydantic import BaseModel

class PromptData(BaseModel):
    """Prompt data model"""

    prompt_name: str
    description: Optional[str] = None
    prompt_value: str
    input_parameters: list[str]
