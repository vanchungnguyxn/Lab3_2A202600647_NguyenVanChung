import os
from dotenv import load_dotenv


def create_provider(provider_name=None, model=None):

    load_dotenv()

    provider_name = provider_name or os.getenv("DEFAULT_PROVIDER", "openrouter")
    model = model or os.getenv("DEFAULT_MODEL", "openai/gpt-4o-mini")

    provider_name = provider_name.lower().strip()

    if provider_name == "openrouter":
        from src.core.openrouter_provider import OpenRouterProvider

        return OpenRouterProvider(
            model_name=model,
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )

    if provider_name == "openai":
        from src.core.openai_provider import OpenAIProvider

        return OpenAIProvider(
            model_name=model,
            api_key=os.getenv("OPENAI_API_KEY"),
        )

    if provider_name in ["google", "gemini"]:
        from src.core.gemini_provider import GeminiProvider

        return GeminiProvider(
            model_name=model if model else "gemini-1.5-flash",
            api_key=os.getenv("GEMINI_API_KEY"),
        )

    if provider_name == "local":
        from src.core.local_provider import LocalProvider

        return LocalProvider(
            model_path=os.getenv(
                "LOCAL_MODEL_PATH",
                "./models/Phi-3-mini-4k-instruct-q4.gguf",
            )
        )

    raise ValueError(
        f"Unsupported DEFAULT_PROVIDER: {provider_name}. "
        "Use one of: openrouter, openai, google, gemini, local."
    )