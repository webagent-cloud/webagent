from models import ProviderEnum
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_mistralai import ChatMistralAI
from langchain_together import Together
from pydantic import SecretStr
import os
from chat.chat import ChatLangchain


def get_llm(provider: ProviderEnum, model: str, callbacks: list = None) -> ChatLangchain:
    """
    Returns the appropriate LLM based on the provider and model.
    """
    if provider == ProviderEnum.openai:
        langchain_model = ChatOpenAI(model=model, callbacks=callbacks)
    elif provider == ProviderEnum.deepseek:
        api_key = os.getenv("DEEPSEEK_API_KEY")
        langchain_model = ChatOpenAI(base_url='https://api.deepseek.com/v1', model=model, api_key=SecretStr(api_key))
    elif provider == ProviderEnum.anthropic:
        langchain_model = ChatAnthropic(model_name=model)
    elif provider == ProviderEnum.google:
        langchain_model = ChatGoogleGenerativeAI(model=model)
    elif provider == ProviderEnum.groq:
        langchain_model = ChatGroq(model=model)
    elif provider == ProviderEnum.mistral:
        langchain_model = ChatMistralAI(model=model)
    elif provider == ProviderEnum.together:
        langchain_model = Together(model=model)
    else:
        langchain_model = ChatOpenAI(model=model)

    return ChatLangchain(langchain_model)