from models import ProviderEnum
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_mistralai import ChatMistralAI
from langchain_together import Together
from pydantic import SecretStr
import os

def get_llm(provider: ProviderEnum, model: str):
    """
    Returns the appropriate LLM based on the provider and model.
    """
    if provider == ProviderEnum.openai:
        return ChatOpenAI(model=model)
    elif provider == ProviderEnum.deepseek:
        api_key = os.getenv("DEEPSEEK_API_KEY")
        return ChatOpenAI(base_url='https://api.deepseek.com/v1', model=model, api_key=SecretStr(api_key))
    elif provider == ProviderEnum.anthropic:
        return ChatAnthropic(model_name=model)
    elif provider == ProviderEnum.google:
        return ChatGoogleGenerativeAI(model=model)
    elif provider == ProviderEnum.groq:
        return ChatGroq(model=model)
    elif provider == ProviderEnum.mistral:
        return ChatMistralAI(model=model)
    elif provider == ProviderEnum.together:
        return Together(model=model)
    else:
        return ChatOpenAI(model=model)
