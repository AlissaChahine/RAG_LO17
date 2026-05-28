# Projet RAG (LO17) - Groupe D1-G7

## Membres du groupe 

Alissa Chahine, Rayssa Ghostine Abi Nassif, Juliette Van Poulle, Yiyang Huang, Xinying Sun


## Description du projet 

Définition d'un RAG + utilité de notre RAG 

[Gemini](https://ai.google.dev/models/gemini) is a family of generative AI models that lets developers generate content and solve problems. These models are designed and trained to handle both text and images as input.

[LangChain](https://www.langchain.com/) is a data framework designed to make integration of Large Language Models (LLM) like Gemini easier for applications.

[Chroma](https://docs.trychroma.com/) is an open-source embedding database focused on simplicity and developer productivity. Chroma allows users to store embeddings and their metadata, embed documents and queries, and search the embeddings quickly.

LLMs are trained offline on a large corpus of public data. Hence they cannot answer questions based on custom or private data accurately without additional context.

If you want to make use of LLMs to answer questions based on private data, you have to provide the relevant documents as context alongside your prompt. This approach is called Retrieval Augmented Generation (RAG).

You will use this approach to create a question-answering assistant using the Gemini text model integrated through LangChain. The assistant is expected to answer questions about the Gemini model. To make this possible you will add more context to the assistant using data from a website.

## Installation 

### Dépendances et librairies : 
Dépendances / librairies 
pip install langchain-core langchain langchain-google-genai 
pip install -U langchain-community chromadb

### Configuration de la clé API : 
To run the following cell, your API key must be stored in a Colab Secret named `GOOGLE_API_KEY`. If you don't already have an API key, or you're not sure how to create a Colab Secret, see [Authentication](https://github.com/google-gemini/cookbook/blob/main/quickstarts/Authentication.ipynb) for an example.

### Easy start : 
commandes principales ...

## Architecture du projet 

