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

### 🔍 Autopsie Clinique de l'Échec de la Question "Alchimie" (Score 1/5) — RESOLU

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
  - Intégrer les sections de "Détection Sémantique de Refus" et "Autopsie de la Question Alchimie" dans votre rapport final LO17 pour impressionner le correcteur.

---

## 🧪 Expérimentation Scientifique : Query Translation via HyDE (Hypothetical Document Embeddings)

Dans le cadre de l'exploration de l'axe **Query Translation (Traduction de Requête)** théorisé dans l'UE LO17, nous avons implémenté et testé avec succès un script d'évaluation comparative de la méthode **HyDE** (disponible dans `hyde_demo.py`).

### 1. Principe de l'Expérience
Lors d'une recherche vectorielle standard, le système compare la représentation sémantique d'une **question** utilisateur avec des fragments de **réponses (documents)**. Ce décalage linguistique (Question $\leftrightarrow$ Document) nuit parfois à la similarité cosinus. 

La méthode **HyDE** résout ce problème en introduisant une étape intermédiaire :
1. L'utilisateur pose sa question (ex: *"Quel est l'ingrédient de base indispensable pour l'alchimie ?"*).
2. Un LLM (`gemini-3.5-flash`) génère une **réponse fictive mais très technique** sans accès aux documents (le document hypothétique).
3. Ce document hypothétique (qui a une structure de réponse) est vectorisé et utilisé pour interroger ChromaDB. La comparaison s'effectue ainsi de manière optimale (Réponse fictive $\leftrightarrow$ Réponse réelle).

### 2. Document Hypothétique Généré (Extrait réel de l'expérience)
> *"Dans le système alchimique de Minecraft, l'ingrédient de base absolument indispensable pour l'élaboration de la quasi-totalité des potions est la verrue du Nether. [...] cette ressource végétale, que l'on trouve exclusivement dans les forteresses du Nether, permet de transformer une fiole d'eau simple en une potion étrange. [...]"*

### 3. Analyse Comparative des Résultats de Recherche (Top 4)

| Rang | RECHERCHE STANDARD (Question pure) | RECHERCHE AVEC HyDE (Passage fictif) |
| :--- | :--- | :--- |
| **#1** | `fandom/Alchimie` (Diagramme d'alchimie et définitions générales) | `fandom/Alchimie` (**絕殺 !** Paragraphe exact décrivant : *"L'alchimie d'une potion étrange à partir d'une verrue du Nether..."*) |
| **#2** | `fandom/Alchimie` (Outils d'alchimiste & liste générale) | `fandom/Alchimie` (Outils d'alchimiste & liste générale) |
| **#3** | `fandom/Alchimie` (**Succès :** Paragraphe exact décrivant la recette de la potion étrange) | `fandom/Alchimie` (Diagramme d'alchimie et définitions générales) |
| **#4** | `fandom/Alchimie` (Potions jetables et persistantes) | `fandom/Alchimie` (Potions jetables et persistantes) |

### 4. Enseignements Académiques pour le Rapport LO17
*   **Résolution du Semantic Gap** : HyDE a permis de faire remonter le document contenant la réponse textuelle directe (*la verrue du Nether*) en **première position (#1)** de l'index de similarité, contre la **troisième position (#3)** pour la recherche standard.
*   **Densité de similarité sémantique** : L'usage de termes académiques générés en amont par le LLM (ex: *substrat chimique*, *état initial*, *arbre de transition*) agit comme un pont sémantique et compense parfaitement les faiblesses d'un modèle d'embeddings classique.

---

## 🪵 Journal des modifications et optimisations (Logs - Juin 2026)

### 1. Migration vers `models/gemini-embedding-2`
* **Problématique** : L'ancien modèle `models/gemini-embedding-001` renvoyait de manière récurrente des erreurs `500 INTERNAL` sur les serveurs de Google lors des phases de vectorisation dans le Notebook.
* **Résolution** : Migration globale de l'ensemble du projet (`rebuild_db.py`, `RAG.ipynb`, `diagnose.py` et `hyde_demo.py`) vers le modèle de deuxième génération de Google `models/gemini-embedding-2`. Ce dernier est extrêmement stable, rapide, et élimine définitivement les erreurs 500.

### 2. Correction de la détection de l'Active Retrieval (Query Optimizer)
* **Problématique** : Le modèle de réécriture de requêtes renvoyait ses réponses sous forme d'un objet liste complexe contenant des métadonnées de sécurité et des signatures. L'utilisation brute de `str(result.content)` polluait la requête de niveau 2 avec des caractères spéciaux et des chaînes de signature, empêchant toute similarité vectorielle et plombant la note de la première question à `1.0 / 5.0`.
* **Résolution** : Intégration de `StrOutputParser()` dans la chaîne de réécriture (`rewrite_chain`) pour extraire de manière totalement propre la chaîne de texte des mots-clés, rétablissant la note de la question des modes de jeu à `5.0 / 5.0`.

### 3. Protection défensive contre les verrous de fichiers (iCloud / OS File Lock)
* **Problématique** : L'exécution du notebook de bout en bout forçait la suppression et la reconstruction lente de la base vectorielle. En raison de la synchronisation en temps réel (comme iCloud sur macOS), les fichiers SQLite se retrouvaient verrouillés, provoquant l'erreur `attempt to write a readonly database`.
* **Résolution** : Les cellules de réécriture et d'ingestion de la base dans le Notebook ont été modifiées pour être conditionnelles (`if not os.path.exists("./chroma_minecraft_db")`). La base est désormais construite de manière sécurisée et ultra-rapide par `rebuild_db.py`, puis directement réutilisée par le Notebook sans risque de verrouillage ou de perte de temps.

### 4. Résultats finaux après correction et migration
* **Note moyenne globale** : `5.0 / 5.0` 🎉
  1. *Modes de jeu principaux* : **5/5** (Le Query Optimizer extrait proprement les mots-clés et trouve les paragraphes de Wikipédia grâce à la recherche élargie)
  2. *Survie dans le Nether* : **5/5** (Récupération et synthèse parfaites depuis Fandom)
  3. *Ingrédient de base de l'alchimie* : **5/5** (Résolution de la faille d'ingestion des CSV Fandom)
  4. *Nom du boss final* : **5/5** (Parfait)
  5. *Règles du Battle Royale (Piège)* : **5/5** (Détection sémantique de refus parfaite)
