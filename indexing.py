import csv
import os
import pickle
import re
import shutil
import time
import uuid
import json
from pathlib import Path
from urllib.parse import urlparse, unquote

import os
import uuid
import time
import requests
import cloudscraper
from bs4 import BeautifulSoup
from IPython.display import Markdown

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate, format_document
from langchain_core.runnables import RunnablePassthrough
from langchain_classic.storage import LocalFileStore
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.vectorstores import Chroma

from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_classic.retrievers import MultiVectorRetriever

from langchain_ollama import ChatOllama

from langchain_google_genai import (
    ChatGoogleGenerativeAI,
    GoogleGenerativeAIEmbeddings,
)

from scrapping import scrape_fandom, scrape_wikipedia, scrape_web
from scrapping_utils import get_all_relative_filenames

# ------------------------------------------------------------CONFIG API-----------------------------------------------------------------
from api_config import configure_google_api_key

GOOGLE_API_KEY = configure_google_api_key()

# --------------------------------------------------------------CONFIG LLM-----------------------------------------------------------------

llm = ChatOllama(model="llama3.2:3b", temperature=0)

summarize_chain = PromptTemplate.from_template("""
Crée un résumé optimisé pour la recherche sémantique.

Conserve :
- les noms d'objets
- les noms de créatures
- les noms de structures
- les noms de biomes
- les mécaniques

N'invente rien.
Ne fais aucune introduction.
Ne fais aucune conclusion.

Texte :

{doc}

Résumé :
""") | llm | StrOutputParser()

gemini_embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001", task_type="retrieval_document"
)


def load_txt_documents(page_names: list[str]):
    documents = []

    for page in page_names:
        file_path = f"files/{page}.txt"
        print(f"Lecture du fichier : {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue

                    # Lecture directe du JSON de la ligne
                    data = json.loads(line)

                    metadata = {
                        "source": data.get("source", ""),
                        "section": data.get("section", ""),
                        "file_origin": file_path,
                    }

                    doc = Document(
                        page_content=data.get("page_content", ""), metadata=metadata
                    )
                    documents.append(doc)

        except Exception as e:
            print(f"Impossible de lire le fichier {file_path} : {e}")

    print(f"\n Chargement terminé ! Total de {len(documents)} Documents récupérés.")
    return documents


# ---------------------------------------------------------CHUNKING-----------------------------------------------------------------
def split_docs(all_docs):
    # Sécurité : Si la liste est vide, on s'arrête gentiment ici sans crasher
    if not all_docs:
        print("ANCIENS DOCS (Paragraphes bruts) : 0")
        print("NOUVEAUX CHUNKS ÉQUILIBRÉS : 0")
        print("Aucun nouveau document à découper (Tout est déjà à jour).")
        return []

    from langchain_text_splitters import RecursiveCharacterTextSplitter

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1800, chunk_overlap=200, separators=["\n\n", "\n", ". ", " ", ""]
    )

    split_docs = splitter.split_documents(all_docs)

    print("ANCIENS DOCS (Paragraphes bruts) :", len(all_docs))
    print("NOUVEAUX CHUNKS ÉQUILIBRÉS :", len(split_docs))

    tailles = [len(doc.page_content) for doc in split_docs]
    if tailles:
        print(
            f"Taille Min : {min(tailles)} | Taille Max : {max(tailles)} | Moyenne : {int(sum(tailles)/len(tailles))}"
        )

    return split_docs


def init_database():
    # 1. Définition des chemins sur le disque
    CHROMA_DIR = "./db/chroma_minecraft_multivec"
    STORE_DIR = "./db/local_chunks_store"

    # 2. Initialisation de la base vectorielle Chroma (Contient les résumés)
    vectorstore = Chroma(
        collection_name="minecraft_summaries",
        persist_directory=CHROMA_DIR,
        embedding_function=gemini_embeddings,
    )

    # 3. Initialisation du stockage persistant sur DISQUE (Contient les chunks bruts)
    fs_store = LocalFileStore(STORE_DIR)

    # 4. Création du Retriever Multi-Vecteurs
    retriever = MultiVectorRetriever(
        vectorstore=vectorstore,
        byte_store=fs_store,
        id_key="doc_id",
    )
    return retriever, vectorstore


def indexing(retriever, vectorstore, all_docs):

    try:
        existing_data = vectorstore.get()

        existing_sections = set(
            f"{meta.get('source')}_{meta.get('section')}"
            for meta in existing_data.get("metadatas", [])
            if meta
        )

        print(
            f"Base de données trouvée : "
            f"{len(existing_sections)} sections uniques déjà présentes dans Chroma."
        )

    except Exception:
        existing_sections = set()
        print("Base vectorielle vierge ou inaccessible. " "Première indexation.")

    docs_to_index = [
        doc
        for doc in all_docs
        if f"{doc.metadata.get('source')}_{doc.metadata.get('section')}"
        not in existing_sections
    ]

    if not docs_to_index:
        print(
            "Tous les documents sont déjà à jour sur le disque. "
            "ZÉRO crédit consommé !"
        )

    else:
        print(
            f"{len(docs_to_index)} nouveaux chunks à traiter "
            f"(Génération Ollama + Embedding Gemini)..."
        )

        for i, doc in enumerate(docs_to_index):
            text_len = len(doc.page_content)

            print(
                f"[{i+1}/{len(docs_to_index)}] "
                f"Analyse du chunk ({text_len} caractères)...",
                end="",
            )

            # ==========================================
            # RÉSUMÉ OLLAMA
            # ==========================================
            if text_len < 700:
                summary_text = doc.page_content
            else:
                try:
                    summary_text = summarize_chain.invoke(
                        {"doc": doc.page_content}
                    ).strip()
                except Exception as e:
                    print(f"\nErreur Ollama sur le chunk {i}: {e}")
                    summary_text = doc.page_content

            # ==========================================
            # ENRICHISSEMENT PAGE + SECTION
            # ==========================================
            section = doc.metadata.get("section", "")
            file_origin = doc.metadata.get("file_origin", "")
            page_name = os.path.basename(file_origin)
            page_name = os.path.splitext(page_name)[0]

            summary_text = f"""
    Page : {page_name}

    Section : {section}

    Résumé :
    {summary_text}
    """.strip()

            # ==========================================
            # ID UNIQUE
            # ==========================================
            chunk_id = str(uuid.uuid4())
            summary_doc = Document(
                page_content=summary_text, metadata={**doc.metadata, "doc_id": chunk_id}
            )

            # ==========================================
            # SAUVEGARDE AVEC RETRY AUTOMATIQUE POUR GEMINI
            # ==========================================
            max_gemini_retries = 5
            saved_successfully = False

            for gemini_attempt in range(max_gemini_retries):
                try:
                    # Étape 1 : Appel API Gemini Embedding + Ajout Chroma
                    retriever.vectorstore.add_documents([summary_doc])

                    # Étape 2 : Sauvegarde locale du chunk brut
                    retriever.docstore.mset([(chunk_id, doc)])

                    print(" -> Sauvegardé !")
                    saved_successfully = True
                    break  # On sort de la boucle de retry interne si tout est OK

                except Exception as e:
                    # Si c'est un problème d'API (comme la 503), on attend et on réessaie
                    if gemini_attempt < max_gemini_retries - 1:
                        wait_time = 5 * (gemini_attempt + 1)
                        print(
                            f"\n⚠️ [Gemini 503] Erreur d'embedding au chunk {i}. Réessai dans {wait_time}s... (Erreur : {e})"
                        )
                        time.sleep(wait_time)
                    else:
                        print(
                            f"\n❌ Erreur persistante après {max_gemini_retries} essais sur le chunk {i} : {e}"
                        )

            # Si après les retries ça n'a pas fonctionné, on arrête proprement le script complet
            if not saved_successfully:
                print(
                    "Arrêt de sécurité. Relance la cellule plus tard quand l'API Gemini sera stable."
                )
                break

    print("\n--- STATISTIQUES ---")
    print("Total Chunks générés ce run (split_docs):", len(all_docs))
    print("Total Résumés actuellement dans Chroma:", vectorstore._collection.count())


def main():
    new_pages = scrape_web(platform="mac")

    new_pages = get_all_relative_filenames()
    print(len(new_pages))
    print(new_pages)
    all_docs = load_txt_documents(new_pages)
    all_docs = split_docs(all_docs)
    retriever, vectorstore = init_database()
    indexing(retriever, vectorstore, all_docs)
