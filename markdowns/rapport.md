# 📊 Rapport de Projet — RAG Minecraft

Ce document compile les fondements théoriques, l'architecture algorithmique et les expérimentations scientifiques menées dans le cadre de l'UE LO17.

---

## 🚀 Architecture de l'Application

Le système suit le pipeline classique de l'UE LO17, étendu par des briques algorithmiques modernes :

1. **Extraction (Python / Scraping)** : Web scraping robuste via `cloudscraper` et `BeautifulSoup` (Wikipedia & Minecraft Fandom Wiki en français).
2. **Stockage & Indexation (Database)** : Modèle d'embeddings `models/gemini-embedding-2` et stockage dans la base vectorielle **Chroma** (`chroma_minecraft_db`).
3. **Moteur RAG & LLM** : Orchestration de la génération avec `gemini-2.5-flash` sous LangChain (LCEL).
4. **Interface Chatbot** : Application web développée avec **Streamlit** dotée d'une charte graphique immersive (Style Minecraft).

---

## 🧠 Algorithmes Avancés Implémentés

### 1. Active Retrieval (RRR — Rewrite-Retrieve-Read)
En cas d'échec de la recherche de similarité vectorielle initiale (Niveau 1), le système bascule sur un processus d'adaptation dynamique. Un **Query Optimizer** (LLM réécriveur de requêtes) simplifie la question de l'utilisateur sous forme de 2 à 3 mots-clés optimisés afin d'élargir la recherche de similarité au Niveau 2.

---

## 🧪 Query Translation via HyDE

Dans le cadre de l'exploration de l'axe **Query Translation (Traduction de Requête)** théorisé dans l'UE LO17, nous avons implémenté et testé avec succès un script d'évaluation comparative de la méthode **HyDE** (disponible dans `hyde_demo.py`).

### 1. Principe de l'Expérience
Lors d'une recherche vectorielle standard, le système compare la représentation sémantique d'une **question** utilisateur avec des fragments de **réponses (documents)**. Ce décalage linguistique (Question <-> Document) nuit parfois à la similarité cosinus. 

La méthode **HyDE** résout ce problème en introduisant une étape intermédiaire :
1. L'utilisateur pose sa question (ex: *"Quel est l'ingrédient de base indispensable pour l'alchimie ?"*).
2. Un LLM (`gemini-2.5-flash`) génère une **réponse fictive mais très technique** sans accès aux documents (le document hypothétique).
3. Ce document hypothétique (qui a une structure de réponse) est vectorisé et utilisé pour interroger ChromaDB. La comparaison s'effectue ainsi de manière optimale (Réponse fictive <-> Réponse réelle).

### 2. Document Hypothétique Généré
> *"Dans le système alchimique de Minecraft, l'ingrédient de base absolument indispensable pour l'élaboration de la quasi-totalité des potions est la verrue du Nether. [...] cette ressource végétale, que l'on trouve exclusivement dans les forteresses du Nether, permet de transformer une fiole d'eau simple en une potion étrange. [...]"*

### 3. Analyse Comparative des Résultats

| Rang | RECHERCHE STANDARD (Question pure) | RECHERCHE AVEC HyDE (Passage fictif) |
| :--- | :--- | :--- |
| **#1** | `fandom/Alchimie` (Diagramme d'alchimie général) | `fandom/Alchimie` (Paragraphe exact décrivant : *"L'alchimie d'une potion étrange à partir d'une verrue du Nether..."*) |
| **#2** | `fandom/Alchimie` (Outils d'alchimiste & liste) | `fandom/Alchimie` (Outils d'alchimiste & liste) |
| **#3** | `fandom/Alchimie` (**Succès :** Paragraphe exact décrivant la recette de la potion étrange) | `fandom/Alchimie` (Diagramme d'alchimie général) |
| **#4** | `fandom/Alchimie` (Potions jetables) | `fandom/Alchimie` (Potions jetables) |

### 4. Enseignements Académiques
* **Résolution du Semantic Gap** : HyDE a permis de faire remonter le document contenant la réponse sémantique directe (*la verrue du Nether*) en **première position (#1)** de l'index de similarité, contre la **troisième position (#3)** pour la recherche standard.
* **Densité de similarité sémantique** : L'usage de termes académiques générés en amont par le LLM (ex: *substrat chimique*, *état initial*, *arbre de transition*) agit comme un pont sémantique et compense parfaitement les faiblesses d'un modèle d'embeddings classique.

