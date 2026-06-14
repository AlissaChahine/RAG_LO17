import os

from api_config import configure_google_api_key
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from multi_query import ask_with_multi_query

configure_google_api_key()

_embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-2",
    task_type="retrieval_document",
)

_provider = os.getenv("LLM_PROVIDER", "ollama")

if _provider == "gemini":
    from langchain_google_genai import ChatGoogleGenerativeAI
    _llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
else:
    from langchain_ollama import ChatOllama
    _llm = ChatOllama(model="qwen3:8b", temperature=0)


def ask_minecraft_bot(question: str) -> str:
    return ask_with_multi_query(question, _llm, _embeddings)
