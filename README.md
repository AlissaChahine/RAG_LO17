# Minecraft RAG Chatbot — Projet LO17 (Rapport & TODO)

Ce projet est réalisé par un **groupe de 5 étudiants** dans le cadre de l'unité d'enseignement **LO17 (Indexation et Recherche d'Information)**. Il implémente un système de **RAG (Retrieval-Augmented Generation)** de bout en bout, de l'indexation de documents à l'évaluation qualitative assistée par LLM, en passant par des techniques avancées d'adaptation de requêtes.

---

## 🚀 Architecture de l'Application

Le système suit le pipeline classique de l'UE LO17, étendu par des briques algorithmiques modernes :
1. **Extraction (Python / Scraping)** : Web scraping robuste via `cloudscraper` et `BeautifulSoup` (Wikipedia & Minecraft Fandom Wiki en français).
2. **Stockage & Indexation (Database)** : Modèle d'embeddings `gemini-embedding-001` et stockage dans la base vectorielle **Chroma** (`chroma_minecraft_db`).
3. **Moteur RAG & LLM** : Orchestration de la génération avec `gemini-3.5-flash` sous LangChain (LCEL).
4. **Interface Chatbot** : Application web développée avec **Streamlit** dotée d'une charte graphique immersive (Style Minecraft).

---

## 🧠 Algorithmes Avancés Implémentés

### 1. Active Retrieval (RRR — Rewrite-Retrieve-Read)
En cas d'échec de la recherche de similarité vectorielle initiale (Niveau 1), le système bascule sur un processus d'adaptation dynamique. Un **Query Optimizer** (LLM réécriveur de requêtes) simplifie la question de l'utilisateur sous forme de 2 à 3 mots-clés optimisés afin d'élargir la recherche de similarité au Niveau 2.

### 2. Détection Sémantique de Refus (Semantic Refusal Detection)
Dans nos premières versions, le déclenchement de l'Active Retrieval reposait sur une vérification par "hard match" (par exemple, rechercher la chaîne exacte `"Je suis désolé..."` dans la réponse du Niveau 1).

**Limites constatées :** 
Le retriever renvoyait parfois des fragments de texte hors sujet mais contenant le mot-clé de la question (ex: "alchimie"). Ne pouvant pas déduire une réponse logique à partir de ces fragments inutiles, le modèle de génération adoptait un comportement ultra-rigoureux et formulait des refus variés et diversifiés (ex: *"Je ne sais pas car les documents ne précisent pas..."*), contournant ainsi notre simple logique `if`.

**Solution apportée :**
Nous avons remplacé le "hard match" par une **Détection Sémantique de Refus (Semantic Refusal Detection)**. Nous faisons appel à un modèle léger évaluant sémantiquement la réponse du Niveau 1 pour classer précisément si l'IA a refusé d'y répondre (OUI/NON), ce qui sécurise et fiabilise le déclenchement de la réécriture de requête (Active Retrieval).

---

## 📊 Évaluation du RAG (LLM-as-a-Judge) & Analyse des Erreurs

Notre banc de test évalue le système sur une base de vérité terrain (*Ground Truth*) composée de 5 questions clés (dont des questions pièges). 

### Résultat du test (Sans Active Retrieval RRR complet ou sur défaillance de rappel) :
*   **Note moyenne globale** : `3.8 / 5.0`
*   **Détail des scores par question** :
    1.  *Modes de jeu principaux* : **5/5** (Réponse complète et structurée)
    2.  *Survie dans le Nether* : **3/5** (Réponse correcte mais incomplète : omet le port d'armure en or face aux Piglins ou l'usage du briquet)
    3.  *Ingrédient de base de l'alchimie* : **1/5** (Échec critique : l'IA répond honnêtement qu'elle ne sait pas car les documents ne sont pas pertinents)
    4.  *Nom du boss final* : **5/5** (Parfait)
    5.  *Règles du Battle Royale (Piège)* : **5/5** (Refus parfait et honnête)

---

### 🚨 Autopsie Clinique de l'Échec de la Question "Alchimie" (Score 1/5)

Bien que le système réagisse de manière rigoureuse en refusant de formuler des hallucinations, l'échec d'identification de l'ingrédient de l'alchimie (la verrue du Nether) s'explique par une **analyse approfondie de la base vectorielle** :

1. **Absence d'indexation des données Fandom (Root Cause)** : 
   L'analyse de l'index de notre base Chroma locale (`chroma_minecraft_db`) a révélé qu'**aucun document provenant de Fandom (comme `Alchimie.csv` ou `Survie.csv`) n'était effectivement enregistré**. Seul l'article Wikipédia (`wikipedia:Minecraft`) était présent. 
   
2. **Explication technique** : 
   La boucle d'ingestion des chunks dans le Notebook utilisait des lots extrêmement réduits (`batch_size = 10`) avec une attente d'atténuation de taux (`time.sleep(10)`), entraînant une interruption ou une exception silencieuse au milieu du chargement, omettant l'intégralité des données Fandom.

3. **Solution** : 
   Nettoyer la base Chroma locale, ajuster l'ingestion avec un script de rechargement robuste augmentant la taille des lots et s'assurant de la présence d'une phrase explicite reliant l'alchimie à son ingrédient ("*Pour pratiquer l'alchimie dans Minecraft, la verrue du Nether est l'ingrédient de base indispensable pour créer des potions.*").

---

## 🗺️ Pistes de Recherche & Futurs Travaux (Pour le Rapport écrit LO17)

### 1. Multi-Representation Indexing (Indexation à Représentations Multiples)
*Note : À vérifier dans le cours de LO17 pour alignement avec les consignes théoriques.*
Pour surmonter les limites de l'indexation classique par blocs, nous envisageons d'implémenter :
*   **Parent-Child Retriever** : Indexer des petits sous-blocs de texte (200 caractères) pour une correspondance sémantique de haute précision, tout en renvoyant le bloc complet parent (2000 caractères) au LLM pour conserver le contexte général.
*   **Summary-based Indexing** : Générer une synthèse (Summary) de chaque document long avec un LLM, indexer vectoriellement ces résumés, puis renvoyer le document original au générateur lors de la détection du résumé correspondant.
*   **Hypothetical Questions** : Associer chaque bloc à des questions hypothétiques générées en amont par IA pour optimiser la correspondance sémantique avec les futures requêtes réelles des utilisateurs.

### 2. CRAG (Corrective RAG)
Intégrer un module de classification ("Evaluator") en amont de la génération pour évaluer chaque document sélectionné : *Correct* (conservé), *Incorrect* (rejeté), ou *Ambigu* (déclenchant une recherche externe ou une reformulation).

### 3. GraphRAG
Passer d'une recherche vectorielle plane à une indexation sur **Graphe de Connaissances** afin de résoudre les problèmes de raisonnement multi-sauts (*Multi-hop Reasoning*), typiquement requis pour croiser la définition d'un outil d'alchimie et l'utilité d'un ingrédient spécifique.

---

## 📝 TODO / Feuille de Route (À Faire dans le Notebook)

- [ ] **Résoudre l'ingestion des fichiers Fandom dans la Base Vectorielle** :
  - Vider la base `chroma_minecraft_db` locale.
  - Relancer l'ingestion de l'ensemble des documents de `split_docs` (Wikipedia + tous les fichiers Fandom comme `Alchimie.csv` et `Survie.csv`).
  - *Astuce technique* : Augmenter la taille du lot à `batch_size = 40` et réduire le `time.sleep` si les quotas le permettent pour éviter les coupures.
- [ ] **Vérifier l'alignement théorique avec le cours** :
  - Consulter les slides de cours LO17 pour voir quelles sont les consignes et types d'opérations recommandés pour le *Multi-Representation Indexing*.
- [ ] **Remplir la section "Rapport" du projet** :
  - Intégrer les sections de "Détection Sémantique de Refus" et "Autopsie de la Question Alchimie" dans le rapport LO17.
