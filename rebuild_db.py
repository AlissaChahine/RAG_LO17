import os
import sys
import shutil
import csv
import time
from pathlib import Path
from dotenv import dotenv_values

os.chdir("/Users/xy/Documents/lo17/rag/lo17-rag-project")
sys.path.insert(0, "./.venv/lib/python3.11/site-packages")

# Load real keys from hermes .env securely
hermes_env = dotenv_values('/Users/xy/.hermes/.env')
real_key = hermes_env.get('GOOGLE_API_KEY') or hermes_env.get('GEMINI_API_KEY')
if real_key:
    os.environ["GOOGLE_API_KEY"] = real_key

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma

# 1. Cleaning existing Chroma DB folder
persist_dir = "./chroma_minecraft_db"
if os.path.exists(persist_dir):
    print("🧹 Suppression de l'ancienne base vectorielle Chroma...")
    try:
        shutil.rmtree(persist_dir)
        print("✅ Ancienne base supprimée.")
    except Exception as e:
        print(f"⚠️ Erreur lors de la suppression de l'ancienne base : {e}")

# 2. Reading and reconstructing documents from files/ CSV files
print("\n📂 Chargement des données à partir des fichiers CSV...")
docs = []
files_dir = Path("./files")

for csv_path in files_dir.rglob("*.csv"):
    relative_path = csv_path.relative_to(files_dir)
    print(f" - Lecture de {relative_path}...")
    
    # Determine metadata source
    if csv_path.name == "wikipedia.csv":
        source = "wikipedia:Minecraft"
    else:
        # Reconstruct Fandom URL
        # e.g., files/Alchimie.csv -> https://minecraft.fandom.com/fr/wiki/Alchimie
        # files/Tutoriels/Choses_à_ne_PAS_faire.csv -> https://minecraft.fandom.com/fr/wiki/Tutoriels/Choses_à_ne_PAS_faire
        parts = list(relative_path.parts)
        # Remove extension from the last part
        parts[-1] = csv_path.stem
        page_name = "/".join(parts)
        source = f"https://minecraft.fandom.com/fr/wiki/{page_name}"
        
    paragraphs = []
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            # Skip header "text"
            next(reader, None)
            for row in reader:
                if row and row[0].strip():
                    paragraphs.append(row[0].strip())
                    
        if paragraphs:
            doc_content = "\n\n".join(paragraphs)
            docs.append(Document(
                page_content=doc_content,
                metadata={"source": source}
            ))
    except Exception as e:
        print(f"❌ Erreur lors de la lecture de {csv_path} : {e}")

print(f"\n📚 Total de documents de haut niveau chargés : {len(docs)}")

# 3. Text Splitting (Chunking)
print("\n✂️ Découpage des documents en chunks (RecursiveCharacterTextSplitter)...")
splitter = RecursiveCharacterTextSplitter(
    chunk_size=2000,
    chunk_overlap=150
)
split_docs = splitter.split_documents(docs)
print(f"🧩 Nombre total de chunks générés : {len(split_docs)}")

# 4. Meta-Enrichment (SOURCE & SOURCE_TYPE)
print("\n🏷️ Enrichissement des chunks avec les en-têtes de sources...")
def enrich_with_source(documents):
    enriched = []
    for d in documents:
        src = d.metadata.get("source", "unknown")
        source_type = "WIKIPEDIA" if "wikipedia" in src else "FANDOM"
        d.page_content = (
            f"SOURCE: {src}\n"
            f"SOURCE_TYPE: {source_type}\n\n"
            f"{d.page_content}"
        )
        enriched.append(d)
    return enriched

split_docs = enrich_with_source(split_docs)

# 5. Ingest into Chroma DB with optimized batch size and safe intervals
print("\n🚀 Indexation dans Chroma DB (Appels à Gemini Embeddings)...")
gemini_embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-2",
    task_type="retrieval_document"
)

# Initialize Chroma Store (This creates a clean database)
vectorstore = Chroma(
    persist_directory=persist_dir,
    embedding_function=gemini_embeddings
)

batch_size = 30  # Optimized batch size
total_chunks = len(split_docs)

for i in range(0, total_chunks, batch_size):
    batch = split_docs[i:i+batch_size]
    print(f" ⏳ Indexation du lot {i//batch_size + 1} / {int(total_chunks/batch_size) + 1} (Chunks {i} à {min(i+batch_size, total_chunks)})...")
    try:
        vectorstore.add_documents(batch)
        # Safe sleep to respect API Quotas
        time.sleep(3)
    except Exception as e:
        print(f"❌ Erreur critique lors de l'indexation du lot : {e}")
        print("🔄 Pause de 10 secondes et tentative de récupération...")
        time.sleep(10)
        vectorstore.add_documents(batch)

print("\n🎉 BASE VECTORIELLE COMPLÈTEMENT RECONSTRUITE ET ENREGISTRÉE ! 🎉")

# 6. Verify and query DB
print(f"\n📊 Vérification finale : Nombre total de documents dans la base : {vectorstore._collection.count()}")

# Get unique sources actually saved
all_docs = vectorstore.get()
metadatas = all_docs.get('metadatas', [])
sources_saved = set(m.get('source') for m in metadatas if m)
print("\n📍 Sources effectivement indexées :")
for s in sorted(list(sources_saved)):
    print(f" - {s}")
