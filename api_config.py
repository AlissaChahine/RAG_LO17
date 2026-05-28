import os

from dotenv import load_dotenv


def configure_google_api_key(env_file: str | None = None) -> str:
    """Load GOOGLE_API_KEY from the environment or a .env file.

    Returns the API key and also exports it to os.environ so LangChain and
    Google SDK clients can read it automatically.
    """
    if env_file:
        load_dotenv(env_file)
    else:
        load_dotenv()

    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY non trouvée. Ajoutez-la dans un fichier .env à la racine du projet."
        )

    os.environ["GOOGLE_API_KEY"] = api_key
    return api_key
