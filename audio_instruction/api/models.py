"""API models for the audio instruction service."""
from typing import Any, ClassVar, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field, HttpUrl, model_validator


class WorkoutInstruction(BaseModel):
    """A single workout instruction with text and duration."""
    text: str = Field(..., description="The instruction text", max_length=256)
    duration_seconds: int = Field(..., description="Duration in seconds", ge=10)


class WorkoutGuideRequest(BaseModel):
    """Request model for workout guide generation."""
    instructions: List[WorkoutInstruction] = Field(
        ..., 
        description="List of workout instructions"
    )
    model_config = {
        "json_schema_extra": {
            "minItems": 1
        }
    }
    
    language: str = Field(
        "en", 
        description="Language code for text-to-speech"
    )
    background_urls: Optional[List[HttpUrl]] = Field(
        None, 
        description="Optional list of YouTube URLs for background music"
    )
    
    @model_validator(mode='after')
    def check_total_duration(self) -> 'WorkoutGuideRequest':
        """Validate that total duration doesn't exceed 4 hours."""
        if not self.instructions:
            raise ValueError("At least one instruction is required")
            
        total_seconds = sum(i.duration_seconds for i in self.instructions)
        max_seconds = 4 * 60 * 60  # 4 hours
        
        if total_seconds > max_seconds:
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            
            raise ValueError(
                f"Total workout duration of {hours}h {minutes}m {seconds}s exceeds maximum of 4 hours."
            )
        
        return self


class ErrorResponse(BaseModel):
    """Error response model."""
    detail: str = Field(..., description="Error detail message")


# Convert between API models and core function parameters
def convert_request_to_core_format(request: WorkoutGuideRequest) -> Tuple[List[Tuple[str, int]], str, Optional[List[str]]]:
    """Convert API request model to core function parameters."""
    instructions = [(i.text, i.duration_seconds) for i in request.instructions]
    background_urls = [str(url) for url in request.background_urls] if request.background_urls else None
    
    return instructions, request.language, background_urls 