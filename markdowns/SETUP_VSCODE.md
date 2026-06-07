# Configuration du Notebook RAG pour VSCode

## Étapes d'installation

### 1. Créer et activer un environnement Python virtuel

```powershell
# Créer l'environnement
python -m venv venv

# Activer l'environnement
venv\Scripts\Activate.ps1
```

### 2. Installer les dépendances

```powershell
pip install \
  langchain \
  langchain-community \
  chromadb \
  google-generativeai \
  python-dotenv \
  beautifulsoup4 \
  lxml
```

### 3. Configurer votre clé API Gemini

1. **Obtenir une clé API** : Allez sur [Google AI Studio](https://aistudio.google.com/app/apikey)
2. **Copier votre clé** et la mettre dans le fichier `.env` :
   ```
   GOOGLE_API_KEY=votre_clé_api_ici
   ```

### 4. Configurer VSCode

1. **Installer l'extension Jupyter** : 
   - Ouvrez VSCode
   - Allez dans Extensions (Ctrl+Shift+X)
   - Cherchez "Jupyter" et installez l'extension officielle Microsoft

2. **Sélectionner le kernel Python** :
   - Ouvrez le notebook
   - Cliquez sur "Select Kernel" (en haut à droite)
   - Choisissez le Python de votre `venv` (./venv/Scripts/python.exe)

### 5. Exécuter le notebook

- Cliquez sur ▶️ pour exécuter chaque cellule
- Ou utilisez `Ctrl+Shift+Enter` pour exécuter la cellule actuelle

## Troubleshooting

### Erreur : "No module named 'google.colab'"
✅ C'est normal ! Le code a été adapté pour VSCode.

### Erreur : "GOOGLE_API_KEY not found"
✅ Vérifiez que le fichier `.env` existe et contient votre clé API.

### Les dépendances ne s'installent pas
✅ Assurez-vous que l'environnement virtuel est activé :
```powershell
venv\Scripts\Activate.ps1
```

## Notes importantes

- ⚠️ Ne committez JAMAIS votre `.env` sur Git (il est dans `.gitignore`)
- 🔒 Gardez votre clé API secrète
- 📦 Le dossier `venv/` est ignoré par Git automatiquement
