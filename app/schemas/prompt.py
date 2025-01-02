"""
This file contains the prompt class and its methods used across the application
authors: Erin Hwang
"""
from langchain_core.prompts import PromptTemplate
from app.schemas.prompt_data import PromptData

class Prompt:
    """Prompt Class
    A simple interface for prompt template handling
    """

    def __init__(self, prompt_data: PromptData) -> None:
        """Initializes the Prompt Class

        Args:
            prompt_data (PromptData): A PromptData Pydantic class holding the information (name, prompt, input parameters, description) about the prompt
        """
        self._prompt_name = prompt_data.prompt_name
        self._description = prompt_data.description
        self._value = prompt_data.prompt_value
        self.input_parameters = prompt_data.input_parameters
        self.mapped_values = {param: None for param in self.input_parameters}

    @property
    def prompt_name(self) -> str:
        """Return the prompt_name for this prompt

        Returns:
            str: The prompt name
        """
        return self._prompt_name

    @property
    def description(self) -> str | None:
        """
        Return the description for this prompt

        Returns:
            str: The prompt description
        """
        return self._description

    @property
    def value(self) -> str:
        """
        Returns the prompt text string


        Returns:
            str: The prompt text
        """
        return self._value

    def get_template(self) -> PromptTemplate:
        """Returns the Prompt template

        Returns:
            PromptTemplate: the prompt template object
        """
        prompt_template = PromptTemplate(
            input_variables=self.input_parameters,
            template=self.value,
        )
        return prompt_template

    def get_all_inputs(self) -> dict:
        """Returns all the mapped and non mapped values

        Returns:
            dict: The model's dictionary of input variables/values
        """
        return self.mapped_values

    def get_mapped_values(self) -> list[str]:
        """
        Get list of mapped values

        Returns:
            list[str]: The input variables with values associated to them
        """
        ret = []
        for param in self.mapped_values:
            if self.mapped_values[param] is not None:
                ret.append(param)
        return ret

    def is_usable(self) -> bool:
        """
        Tests if prompt is fully mapped
        If any parameter is not mapped, returns false

        Returns:
            bool: A boolean indicating the all the prompt inputs are mapped
        """
        return None not in self.mapped_values.values()

    def map_value(self, key: str, value: str) -> None:
        """
        Map value to input param (key)

        Args:
            key (str): Input parameter name
            value (str): Input parameter Value

        Raises:
            TypeError: If the input value is not a string
            ValueError: If the key name is not a valid input parameter
            ValueError: If the input parameter is already mapped
        """
        if not isinstance(value, str):
            raise TypeError(f"Error: Input value must be a str, you passed {type(value)}")
        if key not in self.mapped_values:
            raise ValueError(
                f"Error: Attempting to map value to non-existent input parameter. Input parameters are: {self.input_parameters}. Provided parameter was {key}"
            )
        if self.mapped_values[key] is not None:
            raise ValueError(
                f"Error: Attempting to map value to mapped input parameter. Input parameters set are: {self.mapped_values}"
            )
        self.mapped_values[key] = value

    def remap_value(self, key: str, value: str) -> None:
        """
        Re-map an input param to a new value

        Args:
            key (str): Input parameter name
            value (str): Input parameter Value

        Raises:
            TypeError: If the input value is not a string
        """
        if not isinstance(value, str):
            raise TypeError(f"Error: Input value must be a str, you passed {type(value)}")
        self.mapped_values[key] = value
