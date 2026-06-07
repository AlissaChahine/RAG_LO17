# ⛏️ Minecraft RAG Chatbot — Projet LO17

Ce projet est réalisé par un **groupe de 5 étudiants** dans le cadre de l'UE **LO17 (Indexation et Recherche d'Information)** à l'Université de Technologie de Compiègne (UTC).

Il implémente un système de **RAG (Retrieval-Augmented Generation)** de bout en bout, de l'indexation de documents au LLM-as-a-Judge, doté d'une interface immersive Streamlit style Minecraft.

---

## 🗺️ Carte de la Documentation

Pour faciliter la lecture, notre documentation a été structurée de manière modulaire :

*   [**Rapport de Projet (`rapport.md`)**](./markdowns/rapport.md) : L'architecture complète du RAG, le pipeline d'indexation, les théories algorithmiques (Active Retrieval, RRR) et les résultats de notre expérimentation comparative de la méthode **HyDE** (Query Translation).
*   [**Difficultés Techniques & Solutions (`difficultes_solutions.md`)**](./markdowns/difficultes_solutions.md) : Les verrous technologiques majeurs rencontrés lors du développement (Détection Sémantique de Refus, autopsie clinique de la panne d'ingestion) et leurs résolutions.
*   [**Journal des Modifications & Optimisations (`log.md`)**](./markdowns/log.md) : Historique technique détaillé de nos migrations d'infrastructure, de la transition vers `models/gemini-embedding-2` et de la correction des variables d'Active Retrieval.
*   [**Feuille de Route & TODO (`todo.md`)**](./markdowns/todo.md) : L'état d'avancement des livrables et la feuille de route pour le rendu écrit final de l'UE.

---

## 💻 Guide de Démarrage Rapide

### 1. Installation des dépendances
Configurez votre environnement virtuel Python et installez les dépendances :
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Configuration de la clé API
Créez un fichier `.env` à la racine du projet et collez-y votre clé Gemini :
```env
GOOGLE_API_KEY=votre_api_key
```

### 3. Reconstruction de la base vectorielle
Pour initialiser ou nettoyer votre base vectorielle locale Chroma de manière ultra-rapide, sécurisée et alignée sur le nouveau modèle gemini-embedding-2, lancez :
```bash
python rebuild_db.py
```

### 4. Lancement de l'interface Chatbot Streamlit
Pour lancer l'application web immersive avec le style visuel de Minecraft :
```bash
streamlit run app.py
```
