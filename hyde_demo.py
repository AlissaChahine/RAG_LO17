import os
import sys
import time
import re
from dotenv import dotenv_values

os.chdir("/Users/xy/Documents/lo17/rag/lo17-rag-project")
sys.path.insert(0, "./.venv/lib/python3.11/site-packages")

# Load real keys from hermes .env securely
hermes_env = dotenv_values('/Users/xy/.hermes/.env')
real_key = hermes_env.get('GOOGLE_API_KEY') or hermes_env.get('GEMINI_API_KEY')
if real_key:
    os.environ["GOOGLE_API_KEY"] = real_key

from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

# List of models to try in case of 503 high demand errors
MODELS_TO_TRY = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-3.5-flash"]

# 1. Initialize DB and Embeddings
print("🔄 Initialisation des instances et chargement de Chroma...")
gemini_embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-2",
    task_type="retrieval_document"
)
vectorstore_disk = Chroma(
    persist_directory="./chroma_minecraft_db",
    embedding_function=gemini_embeddings
)

# 2. HyDE Prompt Template
hyde_template = """Tu es un expert du jeu Minecraft et un professeur de l'UE LO17.
Écris un paragraphe de réponse fictif mais extrêmement précis et rigoureux, rédigé en français simple, pour répondre à la question ci-dessous.
N'utilise aucun formatage markdown (pas d'astérisques **, pas de backticks `, pas de listes). Écris uniquement du texte brut.
Ce paragraphe servira de document d'exemple pour effectuer une recherche sémantique (similarité vectorielle). 

Question: {question}
Document fictif (réponse technique directe) :"""

hyde_prompt = PromptTemplate.from_template(hyde_template)

# 3. Generate Hypothetical Document with robust Retry and Fallback
question = "Quel est l'ingrédient de base indispensable pour l'alchimie ?"
print(f"\n❓ Question d'origine : '{question}'")

hypothetical_doc = None
selected_model_name = None

print("\n🤖 Génération du document hypothétique (HyDE) avec logique de résilience...")
for model_name in MODELS_TO_TRY:
    print(f" ⏳ Tentative de génération avec le modèle : {model_name}...")
    
    # Try 3 times with exponential backoff for this model
    for attempt in range(3):
        try:
            llm = ChatGoogleGenerativeAI(model=model_name, temperature=0.3)
            hyde_chain = hyde_prompt | llm | StrOutputParser()
            
            # Execute generation
            hypothetical_doc = hyde_chain.invoke({"question": question})
            selected_model_name = model_name
            break # Success! Break out of the retry loop
        except Exception as e:
            err_msg = str(e)
            if "503" in err_msg or "UNAVAILABLE" in err_msg or "high demand" in err_msg:
                wait_time = (attempt + 1) * 3
                print(f"   ⚠️ Le modèle {model_name} est saturé (Erreur 503). Tentative {attempt+1}/3. Pause de {wait_time}s...")
                time.sleep(wait_time)
            else:
                print(f"   ❌ Erreur d'exécution avec {model_name} : {e}")
                break # Non-503 error, switch model directly
                
    if hypothetical_doc:
        print(f" ✅ Succès obtenu avec le modèle : {selected_model_name}")
        break # Success! Break out of the model loop

if not hypothetical_doc:
    print("\n❌ Échec critique : Tous les modèles de secours ont échoué ou sont actuellement surchargés chez Google.")
    sys.exit(1)

# Clean any residual formatting
hypothetical_doc = re.sub(r'[\*`_#]', '', hypothetical_doc).strip()
print(f"📄 Passage généré :\n\"\"\"\n{hypothetical_doc}\n\"\"\"")

# 4. Perform searches
print("\n🔍 Lancement de la recherche sémantique standard (Question pure)...")
results_standard = vectorstore_disk.similarity_search(question, k=4)

print("\n🔍 Lancement de la recherche sémantique HyDE (Passage fictif) avec résilience aux erreurs API...")
results_hyde = []
for attempt in range(3):
    try:
        results_hyde = vectorstore_disk.similarity_search(hypothetical_doc, k=4)
        break
    except Exception as e:
        print(f"⚠️ Tentative {attempt+1}/3 échouée lors de la recherche vectorielle : {e}")
        if attempt < 2:
            time.sleep(3)
        else:
            print("❌ Échec de la recherche vectorielle.")

# 5. Print comparison
print("\n" + "="*80)
print("🏆 COMPARAISON DES RÉSULTATS DE RECHERCHE")
print("="*80)

print("\n🔵 RECHERCHE STANDARD (Question directe)")
for i, doc in enumerate(results_standard):
    text_clean = doc.page_content[:220].replace('\n', ' ')
    print(f"[{i+1}] Source: {doc.metadata.get('source')}")
    print(f"    Texte: {text_clean}...")

print("\n🟢 RECHERCHE AVEC HyDE (Passage fictif)")
if results_hyde:
    for i, doc in enumerate(results_hyde):
        text_clean = doc.page_content[:220].replace('\n', ' ')
        print(f"[{i+1}] Source: {doc.metadata.get('source')}")
        print(f"    Texte: {text_clean}...")
else:
    print("Indisponible.")
