from webagent.models import ProviderEnum
from langchain_together import Together
from pydantic import SecretStr
import os
from browser_use import ChatGoogle, ChatOpenAI, ChatAnthropic, ChatGroq


def get_llm(provider: ProviderEnum, model: str):
    """
    Returns the appropriate LLM based on the provider and model.
    """
    if provider == ProviderEnum.openai:
        llm = ChatOpenAI(model=model)
    elif provider == ProviderEnum.deepseek:
        api_key = os.getenv("DEEPSEEK_API_KEY")
        llm = ChatOpenAI(base_url='https://api.deepseek.com/v1', model=model, api_key=SecretStr(api_key))
    elif provider == ProviderEnum.anthropic:
        llm = ChatAnthropic(model_name=model)
    elif provider == ProviderEnum.google:
        llm = ChatGoogle(model=model)
    elif provider == ProviderEnum.groq:
        llm = ChatGroq(model=model)
    elif provider == ProviderEnum.together:
        llm = Together(model=model)
    else:
        llm = ChatOpenAI(model=model)

    return llm