from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class Task(BaseModel):
    topic: str
    requirements: str
    max_sections: int = 5
    writing_guidelines: Optional[str] = None


class BedrockModel(Enum):
    """Enum representing different Bedrock model configurations.

    Each enum member contains:
    - value: Display name of the model
    - model_id: The Bedrock model identifier
    - inference_profile: The inference profile identifier
    """

    ANTHROPIC_HAIKU_3_5 = (
        "Claude 3.5 Haiku",
        "anthropic.claude-3-5-haiku-20241022-v1:0",
        "us.anthropic.claude-3-5-haiku-20241022-v1:0",
    )
    ANTHROPIC_SONNET_3_5_V2 = (
        "Claude 3.5 Sonnet v2",
        "anthropic.claude-3-5-sonnet-20241022-v2:0",
        "us.anthropic.claude-3-5-sonnet-20241022-v2:0",
    )

    def __new__(
        cls, value: str, model_id: str, inference_profile: str
    ) -> "BedrockModel":
        """Create a new BedrockModel instance with the specified attributes."""
        obj = object.__new__(cls)
        obj._value_ = value
        obj.model_id = model_id
        obj.inference_profile = inference_profile
        return obj

    @classmethod
    def list(cls) -> List[str]:
        """Returns a list of all model display names."""
        return [model.value for model in cls]

    @classmethod
    def list_inference_profiles(cls) -> List[str]:
        """Returns a list of all model inference profiles.
        It returns the model id if not inference profile is not available."""
        return [
            model.inference_profile
            if model.inference_profile is not None
            else model.model_id
            for model in cls
        ]

    @classmethod
    def get_by_value(cls, value: str) -> "BedrockModel":
        """Returns BedrockModel enum by its display name.

        Args:
            value: The display name of the model to find

        Returns:
            BedrockModel: The matching enum member

        Raises:
            ValueError: If no matching model is found
        """
        try:
            return next(model for model in cls if model.value == value)
        except StopIteration:
            raise ValueError(f"No BedrockModel found for value: {value}")

    @classmethod
    def get_by_model_id(cls, model_id: str) -> Optional["BedrockModel"]:
        """Returns BedrockModel enum by its model_id.

        Args:
            model_id: The Bedrock model identifier to find

        Returns:
            Optional[BedrockModel]: The matching enum member or None if not found
        """
        return next(
            (
                model
                for model in cls
                if model.model_id == model_id or model.inference_profile == model_id
            ),
            None,
        )


@dataclass
class Section:
    title: str
    content: str
    references: List[str]


@dataclass
class Article:
    title: str
    date: str
    introduction: str
    conclusions: str
    sections: List[Section]

    def render_outline(self) -> str:
        sections_content = "\n".join(
            f"{i+1}. {section.title}" for i, section in enumerate(self.sections)
        )
        return f"""
Title: {self.title}

{sections_content}
"""

    def render_full_article(self) -> str:
        sections_content = "\n".join(
            f"\n{section.content}\n" for section in self.sections
        )

        references = "\n".join(
            f"- {ref}" for section in self.sections for ref in section.references
        )

        return f"""# {self.title}
#### Date: {self.date}

## Introduction
{self.introduction}

{sections_content}

## Conclusions
{self.conclusions}

## References
{references}
"""
