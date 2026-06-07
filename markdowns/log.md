# 🪵 Journal des modifications et optimisations (Logs - Juin 2026)

### 1. Migration vers `models/gemini-embedding-2`
* **Problématique** : L'ancien modèle `models/gemini-embedding-001` renvoyait de manière récurrente des erreurs `500 INTERNAL` sur les serveurs de Google lors des phases de vectorisation dans le Notebook.
* **Résolution** : Migration globale de l'ensemble du projet (`rebuild_db.py`, `RAG.ipynb`, `diagnose.py` et `hyde_demo.py`) vers le modèle de deuxième génération de Google `models/gemini-embedding-2`. Ce dernier est extrêmement stable, rapide, et élimine définitivement les erreurs 500.

### 2. Correction de la détection de l'Active Retrieval / 修复主动检索（Query Optimizer）的签名污染
* **Problématique** : Le modèle de réécriture de requêtes (Query Optimizer) renvoyait ses réponses sous forme d'un objet liste complexe contenant des métadonnées de sécurité et des signatures. L'utilisation brute de `str(result.content)` polluait la requête de niveau 2 avec des caractères spéciaux et des chaînes de signature, empêchant toute similarité sémantique et plombant la note de la première question à `1.0 / 5.0`.
* **Résolution** : Intégration de `StrOutputParser()` dans la chaîne de réécriture (`rewrite_chain`) pour extraire de manière totalement propre la chaîne de texte des mots-clés.
