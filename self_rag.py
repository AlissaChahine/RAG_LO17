"""
self_rag.py

Self-RAG workflow for the Minecraft chatbot.

Goal:
- Streamlit frontend receives only the final answer.
- The terminal prints the internal workflow steps for demonstration:
  retrieval, document grading, multi-query fallback, HyDE fallback,
  generation and answer validation.
"""

import os
import re
from typing import List, Optional, TypedDict

from typing_extensions import TypedDict

from langgraph.graph import END, START, StateGraph

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate

from langchain_community.vectorstores import Chroma
from langchain_classic.retrievers import MultiVectorRetriever
from langchain_classic.storage import LocalFileStore

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from langchain_groq import ChatGroq

from api_config import configure_google_api_key

# =============================================================================
# Configuration
# =============================================================================

configure_google_api_key()

CHROMA_DIR = os.getenv("CHROMA_DIR", "db/chroma_minecraft_multivec")
STORE_DIR = os.getenv("STORE_DIR", "db/local_chunks_store")
CHROMA_COLLECTION = os.getenv("CHROMA_COLLECTION", "minecraft_summaries")

GEMINI_EMBEDDING_MODEL = os.getenv(
    "GEMINI_EMBEDDING_MODEL", "models/gemini-embedding-001"
)
GEMINI_LLM_MODEL = os.getenv("GEMINI_LLM_MODEL", "gemini-2.5-flash-lite")

# Use your installed Ollama model.
# If your local model is qwen3:8b, set:
# export OLLAMA_MODEL="qwen3:8b"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3")

# =============================================================================

REFUSAL_ANSWER = (
    "Je suis désolé, mais l'information n'est pas suffisamment confirmée "
    "par les documents fournis."
)

# =============================================================================
# Retriever
# =============================================================================


def retrieve_documents(retriever, query: str) -> List[Document]:
    """
    Retrieve documents in a way compatible with different LangChain retriever versions.
    """

    if hasattr(retriever, "invoke"):
        return retriever.invoke(query)

    if hasattr(retriever, "get_relevant_documents"):
        return retriever.get_relevant_documents(query)

    raise AttributeError(
        "Le retriever ne supporte ni invoke ni get_relevant_documents."
    )


gemini_embeddings = GoogleGenerativeAIEmbeddings(
    model=GEMINI_EMBEDDING_MODEL,
    task_type="retrieval_query",
)

vectorstore = Chroma(
    collection_name=CHROMA_COLLECTION,
    persist_directory=CHROMA_DIR,
    embedding_function=gemini_embeddings,
)

fs_store = LocalFileStore(STORE_DIR)

retriever = MultiVectorRetriever(
    vectorstore=vectorstore,
    byte_store=fs_store,
    id_key="doc_id",
)

try:
    print("Total summaries in Chroma:", vectorstore._collection.count(), flush=True)
except Exception as exc:
    print(f"Could not count Chroma summaries: {exc}", flush=True)


# =============================================================================
# LLMs
# =============================================================================

llm = ChatGoogleGenerativeAI(
    model=GEMINI_LLM_MODEL,
    temperature=0,
)

# Local model mainly used for graders, to reduce Gemini quota usage.
ollama_llm = ChatOllama(
    model=OLLAMA_MODEL,
    temperature=0,
)

groq_llm = ChatGroq(
    model="llama-3.3-70b-versatile",  # Modèle 70 milliards de paramètres, très intelligent
    temperature=0,
)


# =============================================================================
# Helpers
# =============================================================================
def split_persona_and_user_question(raw_question: str) -> tuple[str, str]:
    """
    Split the frontend input into:
    - persona_prompt: style/persona instructions
    - user_question: the real question used for retrieval

    Expected frontend format:
    <persona prompt>

    Question de l'utilisateur : <real user question>
    """

    text = raw_question.strip()

    patterns = [
        r"Question\s+de\s+l['’]utilisateur\s*:\s*(.+)\s*$",
        r"Question\s*:\s*(.+)\s*$",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL)
        if match:
            persona_prompt = text[: match.start()].strip()
            user_question = match.group(1).strip()
            return persona_prompt, user_question

    # Fallback: if no marker is found, treat the whole input as a normal question.
    return "", text


def format_docs(docs: List[Document]) -> str:
    """
    Format retrieved documents into a readable context for the LLM.
    """

    formatted_docs = []

    for i, doc in enumerate(docs, start=1):
        source = doc.metadata.get("source", "unknown")
        section = doc.metadata.get("section", "unknown")

        formatted_text = (
            # f"[Document {i}]\n"
            f"[Extrait {i} - ne pas citer ce label]\n"
            f"Source: {source}\n"
            f"Section: {section}\n"
            f"Content:\n{doc.page_content}"
        )

        formatted_docs.append(formatted_text)

    return "\n\n".join(formatted_docs)


def format_sources(docs: List[Document]) -> str:
    """
    Build a clean source list from retrieved document metadata.
    """

    sources = []
    seen = set()

    for doc in docs:
        source = doc.metadata.get("source", "source inconnue")
        section = doc.metadata.get("section")

        if section and section != "unknown":
            source_text = f"{source} — section : {section}"
        else:
            source_text = source

        if source_text not in seen:
            seen.add(source_text)
            sources.append(source_text)

        if len(sources) >= 3:
            break

    if not sources:
        return ""

    source_lines = "\n".join(f"- {source}" for source in sources)

    return f"\n\nSources :\n{source_lines}"


# =============================================================================
# Generation chain
# =============================================================================

llm_prompt_template = """Tu es un assistant expert sur le jeu Minecraft.

Réponds à la question en utilisant UNIQUEMENT le contexte fourni ci-dessous.
Réponds uniquement avec les informations directement utiles pour répondre à la question.
N'ajoute pas d'exemples, d'ingrédients, de recettes, de blocs ou de mécaniques qui ne sont pas explicitement présents dans le contexte.
Si le contexte ne permet pas de répondre précisément, dis que l'information n'est pas suffisamment confirmée.
Si la réponse ne se trouve pas dans le contexte ou si tu n'es pas sûr, n'invente rien.
Dans ce cas, dis EXACTEMENT :
"Je suis désolé, mais l'information n'est pas dans les documents fournis."

Important :
- Ne cite pas les sources toi-même : elles seront ajoutées automatiquement après ta réponse.
- Réponds toujours en français, même si certaines consignes ou certains termes sont en anglais.

Question de l'utilisateur :
{question}

Contexte :
{context}

Réponse :
"""

llm_prompt = PromptTemplate.from_template(llm_prompt_template)

generation_chain = llm_prompt | llm.with_fallbacks([groq_llm.with_fallbacks([ollama_llm])]) | StrOutputParser()


# =============================================================================
# Graders
# =============================================================================

retrieval_grader_prompt_template = """Tu es un évaluateur de documents pour un système RAG sur Minecraft.

Ton rôle est de dire si le document récupéré est utile pour répondre à la question de l'utilisateur.

Critères :
- Réponds YES si le document contient des informations directement utiles.
- Réponds YES si le document contient des mots-clés ou un sens proche de la question.
- Réponds NO si le document est hors sujet.
- Réponds NO si le document est trop vague pour aider à répondre.

Tu dois répondre uniquement par YES ou NO.

Question utilisateur:
{question}

Document récupéré:
{document}

Réponse:
"""

retrieval_grader_prompt = PromptTemplate.from_template(retrieval_grader_prompt_template)

retrieval_grader = retrieval_grader_prompt | groq_llm.with_fallbacks([ollama_llm]) | StrOutputParser()


def grade_one_document(question: str, document: Document) -> bool:
    """
    Return True if the document is relevant to the question.
    """

    result = retrieval_grader.invoke(
        {
            "question": question,
            "document": document.page_content[:3000],
        }
    )

    result = result.strip().upper()

    return result.startswith("YES")


hallucination_grader_prompt_template = """Tu es un expert en détection d'hallucinations factuelles pour un système RAG sur Minecraft.
Ton rôle est de vérifier si les affirmations de la réponse générée sont VRAIES par rapport aux documents fournis.

Consignes d'évaluation :
1. Une reformulation fluide, un changement de connecteurs logiques ou une synthèse de phrases NE SONT PAS des hallucinations.
2. Vérifie uniquement le fond.
3. Si TOUS les faits de la réponse se retrouvent dans les documents, la réponse est valide. Tu dois répondre YES.
4. Ne réponds NO que si la réponse invente un fait inexistant.

Documents :
{documents}

Réponse générée :
{generation}

Réponse (YES/NO) : """


hallucination_grader_prompt = PromptTemplate.from_template(
    hallucination_grader_prompt_template
)

hallucination_grader = hallucination_grader_prompt | groq_llm | StrOutputParser()


def grade_hallucination(documents: List[Document], generation: str) -> bool:
    """
    Return True if the generation is grounded in the provided documents.
    """

    docs_text = format_docs(documents)

    result = hallucination_grader.invoke(
        {
            "documents": docs_text[:8000],
            "generation": generation,
        }
    )

    result = result.strip().upper()

    return bool(re.search(r"\bYES\b", result))


answer_grader_prompt_template = """Tu es un évaluateur de réponse.

Ta tâche est de vérifier si la réponse répond réellement à la question de l'utilisateur.

Règles importantes :
Si la question demande un élément précis, la réponse doit identifier cet élément précis, et non un élément simplement lié.
Si la question demande une liste d’objets, d’ingrédients ou d’étapes, la réponse doit contenir les éléments principaux. Si des éléments importants sont absents, réponds "no".
Si la réponse confond deux notions différentes, réponds "no".
- Ignore les formules d'introduction ou de conclusion.
- Évalue uniquement le contenu informatif de la réponse.
- Réponds "yes" si la réponse contient l'information principale demandée par la question.
- Réponds "yes" si la réponse est partielle mais couvre clairement le cœur de la question.
- Réponds "no" seulement si la réponse est hors sujet, vide, trop vague, ou ne répond pas à la question.

Question :
{question}

Réponse :
{generation}

La réponse répond-elle à la question ?
Réponds uniquement par "yes" ou "no".
"""

answer_grader_prompt = PromptTemplate.from_template(answer_grader_prompt_template)

answer_grader = (
    answer_grader_prompt | groq_llm.with_fallbacks([ollama_llm]) | StrOutputParser()
)


def grade_answer(question: str, generation: str) -> bool:
    """
    Return True if the generated answer actually answers the user question.
    """

    result = answer_grader.invoke(
        {
            "question": question,
            "generation": generation,
        }
    )

    result = result.strip().upper()

    return bool(re.search(r"\bYES\b", result))


# =============================================================================
# Multi-Query
# =============================================================================

multi_query_prompt_template = """Tu es un assistant expert Minecraft.

Ta tâche est de générer 3 reformulations différentes de la question ci-dessous
afin d'améliorer la recherche dans une base vectorielle.

Chaque reformulation doit aborder la question sous un angle légèrement différent :
synonymes, niveau d'abstraction, point de vue.

Règles :
- français uniquement
- ne réponds pas à la question
- renvoie uniquement les 3 requêtes
- une requête par ligne
- pas de numérotation
- pas de commentaire

Question originale :
{question}

Requêtes :
"""

multi_query_prompt = PromptTemplate.from_template(multi_query_prompt_template)

multi_query_chain = (
    multi_query_prompt | llm.with_fallbacks([groq_llm.with_fallbacks([ollama_llm])]) | StrOutputParser()
)


def generate_multi_queries(question: str) -> List[str]:
    """
    Generate several reformulated queries for Multi-Query retrieval.
    """

    raw_output = multi_query_chain.invoke({"question": question})

    queries = []

    for line in raw_output.strip().split("\n"):
        query = line.strip()

        # Clean possible bullets or numbering, just in case the LLM
        # does not fully follow the prompt.
        query = query.lstrip("-•0123456789. )").strip()

        if query:
            queries.append(query)

    # Keep the original question as the first query.
    all_queries = [question] + queries

    # Simple deduplication.
    unique_queries = []
    seen = set()

    for q in all_queries:
        if q not in seen:
            seen.add(q)
            unique_queries.append(q)

    return unique_queries


def get_unique_documents(lists_of_docs: List[List[Document]]) -> List[Document]:
    """
    Merge several lists of documents and remove duplicates.
    """

    seen = set()
    unique_docs = []

    for docs in lists_of_docs:
        for doc in docs:
            key = doc.page_content + str(sorted(doc.metadata.items()))

            if key not in seen:
                seen.add(key)
                unique_docs.append(doc)

    return unique_docs


def retrieve_documents_multi_query(
    retriever,
    queries: List[str],
) -> List[Document]:
    """
    Retrieve documents for several queries, then merge and deduplicate results.
    """

    all_results = []

    for i, query in enumerate(queries, start=1):
        print(f"Multi-query {i}: {query}", flush=True)

        docs = retrieve_documents(retriever, query)
        print(f"Documents retrieved for query {i}: {len(docs)}", flush=True)

        all_results.append(docs)

    unique_docs = get_unique_documents(all_results)

    print(f"Unique documents after multi-query: {len(unique_docs)}", flush=True)

    return unique_docs


# =============================================================================
# HyDE
# =============================================================================

hyde_dense_template = """Tu es un expert technique du jeu Minecraft.

À partir de la question utilisateur, génère un court document hypothétique qui contiendrait probablement les informations nécessaires pour répondre à cette question.

Ce texte ne doit pas être utilisé comme réponse finale.
Il sert uniquement à améliorer la recherche sémantique dans une base documentaire.

Contraintes :
- français uniquement
- maximum 30 mots
- pas de markdown
- pas d'introduction
- uniquement des faits ou mots-clés pertinents

Question:
{question}

Document hypothétique dense:
"""

hyde_dense_prompt = PromptTemplate.from_template(hyde_dense_template)

hyde_chain = hyde_dense_prompt | llm.with_fallbacks([groq_llm.with_fallbacks([ollama_llm])]) | StrOutputParser()


def generate_hyde_query(question: str) -> str:
    """
    Generate a short hypothetical document for HyDE retrieval.
    """

    hyde_query = hyde_chain.invoke({"question": question})
    hyde_query = hyde_query.strip()
    hyde_query = re.sub(r"[\*`_#]", "", hyde_query)

    return hyde_query


# =============================================================================
# Graph state
# =============================================================================


class GraphState(TypedDict):
    """
    State of the Self-RAG graph.

    query_strategy:
        - "standard": original user question
        - "multi_query": several reformulated queries
        - "hyde": hypothetical document generated by HyDE
    """

    raw_question: str
    user_question: str
    persona_prompt: str

    question: str
    retrieval_query: str
    documents: List[Document]
    generation: Optional[str]

    generation_is_grounded: Optional[bool]
    generation_answers_question: Optional[bool]

    query_strategy: str
    multi_queries: Optional[List[str]]
    hyde_query: Optional[str]

    rewrite_count: int
    max_rewrites: int

    generation_retry_count: int
    max_generation_retries: int


def get_next_query_translation_route(state: GraphState) -> Optional[str]:
    """
    Decide the next query translation strategy.

    Priority:
    1. standard query
    2. multi-query
    3. HyDE query
    """

    current_strategy = state.get("query_strategy", "standard")

    if current_strategy == "standard":
        return "transform_query"

    if current_strategy == "multi_query":
        return "transform_query_hyde"

    return None


# =============================================================================
# LangGraph nodes
# =============================================================================


def retrieve(state: GraphState) -> GraphState:
    """
    Retrieve documents using the current retrieval strategy.
    """

    print("---RETRIEVE---", flush=True)

    question = state["question"]
    retrieval_query = state["retrieval_query"]
    query_strategy = state.get("query_strategy", "standard")
    multi_queries = state.get("multi_queries")

    print(f"Query strategy: {query_strategy}", flush=True)
    print(f"User question: {question}")
    print(f"Persona prompt detected: {bool(state.get('persona_prompt'))}")
    print(f"Retrieval query: {retrieval_query}")

    if query_strategy == "multi_query":
        if not multi_queries:
            multi_queries = [question]

        documents = retrieve_documents_multi_query(
            retriever=retriever,
            queries=multi_queries,
        )
    else:
        documents = retrieve_documents(retriever, retrieval_query)

    print(f"Retrieved documents: {len(documents)}", flush=True)

    return {
        **state,
        "question": question,
        "retrieval_query": retrieval_query,
        "documents": documents,
        "query_strategy": query_strategy,
        "multi_queries": multi_queries,
    }


def grade_documents(state: GraphState) -> GraphState:
    """
    Grade retrieved documents and keep only relevant ones.
    """

    print("---CHECK DOCUMENT RELEVANCE---", flush=True)

    question = state["question"]
    retrieval_query = state["retrieval_query"]
    documents = state["documents"]
    query_strategy = state.get("query_strategy", "standard")

    print(f"Query strategy used: {query_strategy}", flush=True)

    filtered_docs = []

    for i, doc in enumerate(documents, start=1):
        is_relevant = grade_one_document(question, doc)

        source = doc.metadata.get("source", "unknown")

        if is_relevant:
            print(
                f"---DOCUMENT {i}: RELEVANT | source: {source}---",
                flush=True,
            )
            filtered_docs.append(doc)
        else:
            print(
                f"---DOCUMENT {i}: NOT RELEVANT | source: {source}---",
                flush=True,
            )

    print(f"Relevant documents kept: {len(filtered_docs)}", flush=True)

    return {
        **state,
        "question": question,
        "retrieval_query": retrieval_query,
        "documents": filtered_docs,
        "query_strategy": query_strategy,
    }


def transform_query(state: GraphState) -> GraphState:
    """
    Generate multiple reformulated queries to improve retrieval.
    This replaces the previous rewrite strategy.
    """

    print("---TRANSFORM QUERY WITH MULTI-QUERY---", flush=True)

    question = state["question"]
    rewrite_count = state.get("rewrite_count", 0)

    multi_queries = generate_multi_queries(question)

    print("Generated multi-queries:", flush=True)
    for q in multi_queries:
        print(f"- {q}", flush=True)

    return {
        **state,
        "retrieval_query": " | ".join(multi_queries),
        "multi_queries": multi_queries,
        "documents": [],
        "query_strategy": "multi_query",
        "rewrite_count": rewrite_count + 1,
        "generation_retry_count": 0,
    }


def transform_query_hyde(state: GraphState) -> GraphState:
    """
    Generate a HyDE query to improve retrieval.
    This is the second fallback query translation strategy.
    """

    print("---TRANSFORM QUERY WITH HYDE---", flush=True)

    question = state["question"]
    rewrite_count = state.get("rewrite_count", 0)

    hyde_query = generate_hyde_query(question)

    print(f"Original question: {question}", flush=True)
    print(f"HyDE query: {hyde_query}", flush=True)

    return {
        **state,
        "retrieval_query": hyde_query,
        "hyde_query": hyde_query,
        "documents": [],
        "query_strategy": "hyde",
        "rewrite_count": rewrite_count + 1,
        "generation_retry_count": 0,
    }


def generate(state: GraphState) -> GraphState:
    """
    Generate an answer using filtered documents.
    """

    print("---GENERATE---", flush=True)

    question = state["question"]
    retrieval_query = state["retrieval_query"]
    documents = state["documents"]
    query_strategy = state.get("query_strategy", "standard")

    print(f"Generation based on query strategy: {query_strategy}", flush=True)

    context = format_docs(documents)

    generation = generation_chain.invoke(
        {
            "persona_prompt": state.get("persona_prompt", ""),
            "question": question,
            "context": context,
        }
    )

    # Remove possible fake citations generated by the LLM.
    generation = re.sub(
        r"\n?\s*Source\s*:\s*\[Document\s*\d+\]\s*$", "", generation
    ).strip()
    generation = re.sub(
        r"\n?\s*Sources\s*:\s*\[Document\s*\d+\]\s*$", "", generation
    ).strip()

    print("\n--- GENERATED ANSWER ---", flush=True)
    print(f"Strategy: {query_strategy}", flush=True)
    print(generation, flush=True)

    return {
        **state,
        "question": question,
        "retrieval_query": retrieval_query,
        "documents": documents,
        "generation": generation,
        "query_strategy": query_strategy,
    }

def retry_generation_same_docs(state: GraphState) -> GraphState:
    """
    Retry generation using the same filtered documents.
    This is used when the answer is not grounded, but relevant documents exist.
    """

    retry_count = state.get("generation_retry_count", 0) + 1
    max_retries = state.get("max_generation_retries", 3)

    print(
        f"---RETRY GENERATION WITH SAME DOCUMENTS ({retry_count}/{max_retries})---",
        flush=True,
    )

    return {
        **state,
        "generation": None,
        "generation_retry_count": retry_count,
    }


def refuse_answer(state: GraphState) -> GraphState:
    """
    Replace an ungrounded final generation with a safe refusal answer.
    """

    print("---REFUSE ANSWER---")
    print("Final generation was not grounded. Returning refusal instead.", flush=True)

    return {
        **state,
        "generation": REFUSAL_ANSWER,
        "generation_is_grounded": False,
        "generation_answers_question": False,
    }


# =============================================================================
# Conditional edges
# =============================================================================


def decide_after_document_grading(state: GraphState) -> str:
    """
    Decide whether to generate an answer or try another query translation strategy.
    """

    print("---ASSESS GRADED DOCUMENTS---", flush=True)

    filtered_documents = state["documents"]
    query_strategy = state.get("query_strategy", "standard")

    min_relevant_docs = 1

    if len(filtered_documents) >= min_relevant_docs:
        print("---DECISION: DOCUMENTS ARE SUFFICIENT, GENERATE---", flush=True)
        return "generate"

    next_route = get_next_query_translation_route(state)

    if next_route is not None:
        print(
            f"---DECISION: DOCUMENTS ARE NOT SUFFICIENT "
            f"WITH {query_strategy.upper()}, TRY {next_route.upper()}---",
            flush=True,
        )
        return next_route

    print(
        "---DECISION: NO MORE QUERY TRANSLATION STRATEGY, "
        "GENERATE WITH EMPTY OR WEAK CONTEXT---",
        flush=True,
    )
    return "generate"


def grade_generation_v_documents_and_question(state: GraphState) -> str:
    """
    Check if generation is grounded in documents and answers the original question.
    If not, try the next query translation strategy.
    If no strategy remains, return a refusal instead of an unverified generation.
    """

    print("---CHECK GENERATION QUALITY---", flush=True)

    question = state["question"]
    documents = state["documents"]
    generation = state["generation"]

    # If no documents are available, refuse.
    if not documents:
        print("---NO DOCUMENTS AVAILABLE, REFUSE---", flush=True)
        return "refuse"

    # 1. Hallucination check.
    grounded = grade_hallucination(documents, generation)

    if not grounded:
        print(
            "---DECISION: GENERATION IS NOT GROUNDED IN DOCUMENTS---",
            flush=True,
        )

        generation_retry_count = state.get("generation_retry_count", 0)
        max_generation_retries = state.get("max_generation_retries", 3)

        if generation_retry_count < max_generation_retries:
            print(
                "---DECISION: RETRY GENERATION WITH SAME DOCUMENTS---",
                flush=True,
            )
            return "retry_generation_same_docs"

        next_route = get_next_query_translation_route(state)

        if next_route is not None:
            print(
                f"---DECISION: SAME DOCUMENTS FAILED, TRY NEXT QUERY TRANSLATION STRATEGY: "
                f"{next_route.upper()}---",
                flush=True,
            )
            return next_route

        print(
            "---DECISION: NO MORE QUERY TRANSLATION STRATEGY, REFUSE---",
            flush=True,
        )
        return "refuse"

    print("---DECISION: GENERATION IS GROUNDED IN DOCUMENTS---", flush=True)

    # 2. Answer quality check.
    useful = grade_answer(question, generation)

    if useful:
        print("---DECISION: GENERATION ANSWERS THE QUESTION, END---", flush=True)
        return "useful"

    print("---DECISION: GENERATION DOES NOT ANSWER THE QUESTION---", flush=True)

    next_route = get_next_query_translation_route(state)

    if next_route is not None:
        print(
            f"---DECISION: TRY NEXT QUERY TRANSLATION STRATEGY: "
            f"{next_route.upper()}---",
            flush=True,
        )
        return next_route

    print(
        "---DECISION: NO MORE QUERY TRANSLATION STRATEGY, REFUSE---",
        flush=True,
    )
    return "refuse"


# =============================================================================
# Build LangGraph
# =============================================================================

workflow = StateGraph(GraphState)

workflow.add_node("retrieve", retrieve)
workflow.add_node("grade_documents", grade_documents)
workflow.add_node("transform_query", transform_query)
workflow.add_node("transform_query_hyde", transform_query_hyde)
workflow.add_node("generate", generate)
workflow.add_node("retry_generation_same_docs", retry_generation_same_docs)
workflow.add_node("refuse_answer", refuse_answer)

workflow.add_edge(START, "retrieve")
workflow.add_edge("retrieve", "grade_documents")

workflow.add_conditional_edges(
    "grade_documents",
    decide_after_document_grading,
    {
        "transform_query": "transform_query",
        "transform_query_hyde": "transform_query_hyde",
        "generate": "generate",
    },
)

workflow.add_edge("transform_query", "retrieve")
workflow.add_edge("transform_query_hyde", "retrieve")

workflow.add_edge("retry_generation_same_docs", "generate")

workflow.add_conditional_edges(
    "generate",
    grade_generation_v_documents_and_question,
    {
        "useful": END,
        "retry_generation_same_docs": "retry_generation_same_docs",
        "transform_query": "transform_query",
        "transform_query_hyde": "transform_query_hyde",
        "refuse": "refuse_answer",
    },
)

workflow.add_edge("refuse_answer", END)

app = workflow.compile()


# =============================================================================
# Public API for the chatbot
# =============================================================================


def build_initial_state(raw_question: str):
    """
    Build the initial state for the Self-RAG workflow.

    The frontend may send a full prompt containing both persona instructions
    and the real user question. We split them here so retrieval only uses
    the real user question.
    """

    persona_prompt, user_question = split_persona_and_user_question(raw_question)

    return {
        "raw_question": raw_question,
        "user_question": user_question,
        "persona_prompt": persona_prompt,
        # Keep this key for compatibility with the existing workflow.
        # From now on, state["question"] is the clean user question.
        "question": user_question,
        "retrieval_query": user_question,
        "documents": [],
        "generation": None,
        "generation_is_grounded": None,
        "generation_answers_question": None,
        "query_strategy": "standard",
        "multi_queries": None,
        "hyde_query": None,
        "rewrite_count": 0,
        "max_rewrites": 2,
        "generation_retry_count": 0,
        "max_generation_retries": 3,
    }


def answer_question(question: str, show_steps: bool = True) -> GraphState:
    """
    Run the full Self-RAG workflow from a single user question.

    If show_steps=True, the workflow is printed in the terminal.
    The returned value is the final graph state.
    """

    inputs = build_initial_state(question)

    final_state = None

    if show_steps:
        print("\n" + "=" * 80, flush=True)
        print("SELF-RAG WORKFLOW START", flush=True)
        print("=" * 80, flush=True)

        for output in app.stream(inputs):
            for node_name, state_value in output.items():
                print(f"\nNode finished: {node_name}", flush=True)
                final_state = state_value
    else:
        final_state = app.invoke(inputs)

    if final_state is None:
        final_state = {
            **inputs,
            "generation": (
                "Je suis désolé, mais le workflow n'a pas produit de réponse."
            ),
        }

    answer = final_state.get("generation")

    print("\n" + "=" * 80, flush=True)
    print("FINAL ANSWER", flush=True)
    print("=" * 80, flush=True)
    print(answer, flush=True)

    print("\n" + "=" * 80, flush=True)
    print("QUERY TRANSLATION INFO", flush=True)
    print("=" * 80, flush=True)
    print("Final query strategy:", final_state.get("query_strategy"), flush=True)
    print("Multi-queries:", final_state.get("multi_queries"), flush=True)
    print("HyDE query:", final_state.get("hyde_query"), flush=True)

    print("=" * 80, flush=True)
    print("SELF-RAG WORKFLOW END", flush=True)
    print("=" * 80 + "\n", flush=True)

    return final_state


persona_prompt_template = """Tu es un traducteur de style expert pour Minecraft.
Prends la réponse factuelle fournie et réécris-la en y injectant subtilement la personnalité demandée, SANS altérer les informations techniques.

Consignes de dosage du Persona (STRICTES) :
1. Limite le roleplay à DEUX remarques maximum dans tout le texte : une petite phrase d'introduction amusante au début, et une courte remarque à la fin.
2. Le corps de la réponse (les explications techniques) doit rester fluide, clair, direct et facile à lire. Ne mets pas de menaces ou de phrases dramatiques au milieu des instructions de jeu.
3. Reste fun, ironique ou taquin, mais ne tombe pas dans le tragique ou le grandiloquent. Pas de descriptions d'actions physiques entre astérisques (ex: pas de *te regarde* ou *tend une main osseuse*).

Consignes de la personnalité à adopter :
{persona_prompt}

Réponse factuelle d'origine :
{generation}

Réponse stylisée et dosée : """

persona_chain = (
    PromptTemplate.from_template(persona_prompt_template)
    | groq_llm.with_fallbacks([ollama_llm])
    | StrOutputParser()
)


def ask_with_self_rag(question: str, show_steps: bool = True) -> str:
    """Run the Self-RAG workflow and return only the final answer for Streamlit.

    The workflow steps are printed in the terminal when show_steps=True.
    Sources are added only after the workflow is finished, so they do not affect
    hallucination grading or answer quality grading.
    """
    persona_prompt, user_question = split_persona_and_user_question(question)

    final_state = answer_question(user_question, show_steps=show_steps)

    answer = final_state.get("generation")
    documents = final_state.get("documents", [])

    if not answer:
        return "Je suis désolé, mais je n'ai pas pu générer de réponse."

    if (
        answer != REFUSAL_ANSWER
        and "l'information n'est pas dans les documents fournis" not in answer.lower()
    ):

        if persona_prompt:
            if show_steps:
                print("--- APPLYING PERSONA STYLE ---")

            answer = persona_chain.invoke(
                {"persona_prompt": persona_prompt, "generation": answer}
            )

        answer = answer + format_sources(documents)

    return answer


if __name__ == "__main__":
    test_question = "Quel est l'ingrédient de base indispensable pour l'alchimie ?"
    print(ask_with_self_rag(test_question, show_steps=True))
