from typing import Literal

from pydantic import BaseModel, Field


class AppConfig(BaseModel):
    title: str = Field(description="Display title of the application.")

    description: str = Field(
        description="Brief description of the application and its purpose."
    )


class DefaultsConfig(BaseModel):
    decimal_precision: int = Field(
        default=4,  # This used to be 28, not sure why, since that's very large.
        ge=1,
        le=16,
        description="Number of decimal places used in cost and probability calculations.",
    )

    ui_theme: Literal["light", "dark"] = Field(
        default="light",
        description="UI theme. One of 'light' or 'dark'.",
    )


class Config(BaseModel):
    app: AppConfig
    defaults: DefaultsConfig


__all__ = ["Config"]
