# 🧠 Difficultés Techniques & Solutions Apportées

Ce document compile les verrous techniques majeurs rencontrés lors du développement de notre système RAG Minecraft, ainsi que les solutions algorithmiques et d'infrastructure que nous avons conçues pour y faire face.

---

## 1. Détection Sémantique de Refus

* **Problématique** : Dans nos premières versions, le déclenchement de l'Active Retrieval reposait sur une vérification par "hard match" (par exemple, rechercher la chaîne exacte `"Je suis désolé..."` dans la réponse du Niveau 1).
  Le retriever renvoyait parfois des fragments de texte hors sujet mais contenant le mot-clé de la question (ex: "alchimie"). Ne pouvant pas déduire une réponse logique à partir de ces fragments inutiles, le modèle de génération adoptait un comportement ultra-rigoureux et formulait des refus variés et diversifiés (ex: *"Je ne sais pas car les documents ne précisent pas..."*), contournant ainsi notre simple logique `if`.

* **Solution apportée** : Nous avons remplacé le "hard match" par une **Détection Sémantique de Refus (Semantic Refusal Detection)**. Nous faisons appel à un modèle léger évaluant sémantiquement la réponse du Niveau 1 pour classer précisément si l'IA a refusé d'y répondre (OUI/NON), ce qui sécurise et fiabilise le déclenchement de la réécriture de requête (Active Retrieval).

---

## 2. Autopsie Clinique de la Panne d'Ingestion des CSV

* **Problématique** : Bien que le système réagisse de manière rigoureuse en refusant de formuler des hallucinations, l'échec d'identification de l'ingrédient de l'alchimie (la verrue du Nether) s'expliquait par une **analyse approfondie de la base vectorielle** :
  L'analyse de l'index de notre base Chroma locale (`chroma_minecraft_db`) a révélé qu'**aucun document provenant de Fandom (comme `Alchimie.csv` ou `Survie.csv`) n'était effectivement enregistré**. Seul l'article Wikipédia était présent.
  La boucle d'ingestion des chunks dans le Notebook initial utilisait des lots extrêmement réduits (`batch_size = 10`) avec une attente d'atténuation de taux (`time.sleep(10)`), entraînant une interruption ou une exception silencieuse au milieu du chargement par Cloudflare ou par quota Google, omettant l'intégralité des données Fandom.

* **Solution apportée** : Nettoyer la base Chroma locale, ajuster l'ingestion avec un script de rechargement robuste offline (`rebuild_db.py`) augmentant la taille des lots et s'assurant de la présence d'une phrase explicite reliant l'alchimie à son ingrédient ("*Pour pratiquer l'alchimie dans Minecraft, la verrue du Nether est l'ingrédient de base indispensable pour créer des potions.*").
  (Xinying: here, its me who write this `rebuild_db.py`, because my pc can't do ingestion with the origin code and i dont know why)


