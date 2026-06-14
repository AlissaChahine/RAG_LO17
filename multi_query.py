import warnings
warnings.filterwarnings("ignore")

from operator import itemgetter

from langchain_community.vectorstores import Chroma
from langchain_classic.storage import LocalFileStore
from langchain_classic.retrievers import MultiVectorRetriever
from langchain_core.load import dumps
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

CHROMA_DIR = "db/chroma_minecraft_multivec"
STORE_DIR = "db/local_chunks_store"


def _build_retriever(embeddings):
    vectorstore = Chroma(
        collection_name="minecraft_summaries",
        persist_directory=CHROMA_DIR,
        embedding_function=embeddings,
    )
    fs_store = LocalFileStore(STORE_DIR)
    return MultiVectorRetriever(
        vectorstore=vectorstore,
        byte_store=fs_store,
        id_key="doc_id",
    )


def _get_unique_union(lists_of_docs):
    seen = set()
    unique = []
    for docs in lists_of_docs:
        for doc in docs:
            key = dumps(doc)
            if key not in seen:
                seen.add(key)
                unique.append(doc)
    return unique


def _format_docs(docs):
    parts = []
    for doc in docs:
        source = doc.metadata.get("source", "inconnu")
        parts.append(f"[{source}]\n{doc.page_content}")
    return "\n\n".join(parts)


_MULTI_QUERY_PROMPT = ChatPromptTemplate.from_template("""
Tu es un assistant expert Minecraft. Ta tâche est de générer 5 reformulations différentes
de la question ci-dessous afin d'améliorer la recherche dans une base vectorielle.
Chaque reformulation doit aborder la question sous un angle légèrement différent
(synonymes, niveau d'abstraction, point de vue).
Renvoie uniquement les 5 questions, une par ligne, sans numérotation ni commentaire.

Question originale : {question}
""")

_ANSWER_PROMPT = ChatPromptTemplate.from_template("""
Tu es un expert du jeu Minecraft. Réponds en français à la question suivante en t'appuyant
uniquement sur les documents fournis. Si l'information est absente, dis-le clairement.

Contexte :
{context}

Question : {question}
""")


def build_multi_query_chain(llm, embeddings):
    """Construit et retourne la chaîne Multi-Query RAG."""
    retriever = _build_retriever(embeddings)

    generate_multi_queries = (
        _MULTI_QUERY_PROMPT
        | llm
        | StrOutputParser()
        | (lambda x: [q.strip() for q in x.strip().split("\n") if q.strip()])
    )

    retrieval_chain = generate_multi_queries | retriever.map() | _get_unique_union

    rag_chain = (
        {
            "context": retrieval_chain | _format_docs,
            "question": itemgetter("question"),
        }
        | _ANSWER_PROMPT
        | llm
        | StrOutputParser()
    )

    return rag_chain


def ask_with_multi_query(question: str, llm, embeddings) -> str:
    """Répond à une question Minecraft via Multi-Query RAG."""
    chain = build_multi_query_chain(llm, embeddings)
    return chain.invoke({"question": question})


if __name__ == "__main__":
    import os
    from api_config import configure_google_api_key
    from langchain_google_genai import GoogleGenerativeAIEmbeddings

    configure_google_api_key()

    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-2",
        task_type="retrieval_document",
    )

    provider = os.getenv("LLM_PROVIDER", "ollama")
    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
    else:
        from langchain_ollama import ChatOllama
        llm = ChatOllama(model="qwen3:8b", temperature=0)

    question = "Quel est l'ingrédient de base indispensable pour l'alchimie ?"
    print(f"Question : {question}\n")
    print(f"LLM provider : {provider}\n")
    reponse = ask_with_multi_query(question, llm, embeddings)
    print(f"Réponse :\n{reponse}")
