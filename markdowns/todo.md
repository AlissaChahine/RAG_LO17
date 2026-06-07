# 📝 TODO

- [x] **Résoudre l'ingestion des fichiers Fandom dans la Base Vectorielle** :
  - Vider la base `chroma_minecraft_db` locale.
  - Relancer l'ingestion de l'ensemble des documents offline (Wikipedia + Fandom).
- [x] **Vérifier l'alignement théorique avec le cours** :
  - Consulter les slides de cours LO17 pour voir quelles sont les consignes et types d'opérations recommandés pour le *Multi-Representation Indexing*.

- [ ] try to find a way to save tokens in indexing, hyde and future developpment

## Futurs Travaux

### 1. Multi-Representation Indexing
Pour surmonter les limites de l'indexation classique par blocs, nous envisageons d'implémenter :
* court terme ou long terme, nous explorons d'implémenter :*
* **Summary-based Indexing** (Déjà dans `RAG_indexing.ipynb`) : Générer une synthèse (Summary) de chaque document long avec un LLM, indexer vectoriellement ces résumés, puis renvoyer le document original au générateur lors de la détection du résumé correspondant.

### 2. CRAG (Corrective RAG)
Intégrer un module de classification ("Evaluator") en amont de la génération pour évaluer chaque document sélectionné : *Correct* (conservé), *Incorrect* (rejeté), ou *Ambigu* (déclenchant une recherche externe ou une reformulation).

### 3. GraphRAG
Passer d'une recherche vectorielle plane à une indexation sur **Graphe de Connaissances** afin de résoudre les problèmes de raisonnement multi-sauts (*Multi-hop Reasoning*).