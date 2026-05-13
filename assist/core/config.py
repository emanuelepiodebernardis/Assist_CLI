from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class QualityConfig(BaseModel):
    threshold: float = Field(default=0.85, ge=0.0, le=1.0)
    max_self_corrections: int = Field(default=2, ge=0)


class VerificationConfig(BaseModel):
    check_syntax: bool = True
    check_placeholders: bool = True
    check_coherence: bool = True


class LoggingConfig(BaseModel):
    level: str = "INFO"


class Settings(BaseModel):
    model: str = "claude-sonnet-4-6"
    temperature: float = Field(default=0.2, ge=0.0, le=1.0)
    max_input_tokens: int = Field(default=4000, ge=1)
    output_mode: str = "concise"

    quality: QualityConfig = Field(default_factory=QualityConfig)
    verification: VerificationConfig = Field(default_factory=VerificationConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


class ConfigLoader:
    def __init__(self, config_path: str | Path = "config/settings.yaml") -> None:
        self.config_path = Path(config_path)

    def load(self) -> Settings:
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Config file not found: {self.config_path}"
            )

        with self.config_path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file) or {}

        return Settings.model_validate(data)