"""
Agent Factory module for production-grade agent initialization.

This module provides factory functions to create PydanticAI agents configured
for OpenRouter, with standardized model settings and provider configurations.
"""
import os
from typing import Any
from dotenv import load_dotenv
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIModel
from pydantic_ai.providers.openai import OpenAIProvider
from pydantic_ai.settings import ModelSettings

def create_openrouter_model(model_name: str = "openai/gpt-4o-mini"):
    """Creates an OpenAIModel configured for OpenRouter.

    Loads API credentials from environment variables and sets up the 
    OpenRouter API as an OpenAI-compatible provider.

    Args:
        model_name: The slug for the model on OpenRouter (e.g., 'openai/gpt-4o').
            Defaults to "openai/gpt-4o-mini".

    Returns:
        OpenAIModel: The configured PydanticAI model instance.

    Raises:
        ValueError: If OPENROUTER_API_KEY is not found in the environment.
    """
    load_dotenv()
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise ValueError("OPENROUTER_API_KEY not found in environment")
        
    return OpenAIModel(
        model_name,
        provider=OpenAIProvider(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        ),
    )

def create_agent(
    model_name: str = "openai/gpt-4o-mini", 
    system_prompt: str = "",
    deps_type: Any = None,
    result_type: Any = str
):
    """Standard factory for creating production-ready PydanticAI agents.

    Applies strict production settings (low temperature, 60s timeout) and
    initializes the agent with the specified types and prompt.

    Args:
        model_name: The OpenRouter model slug. Defaults to "openai/gpt-4o-mini".
        system_prompt: Initial instruction for the agent. Defaults to "".
        deps_type: The Type/Class for dependency injection. Defaults to None.
        result_type: The expected output Type (e.g., Pydantic model). 
            Defaults to str.

    Returns:
        Agent: A fully configured PydanticAI Agent instance.
    """
    model = create_openrouter_model(model_name)
    
    # Standard production settings
    settings = ModelSettings(
        temperature=0.1,  # Low temperature for analytical consistency
        max_tokens=2000,
        timeout=60.0,
    )
    
    return Agent(
        model,
        system_prompt=system_prompt,
        deps_type=deps_type,
        output_type=result_type,
        model_settings=settings,
    )
