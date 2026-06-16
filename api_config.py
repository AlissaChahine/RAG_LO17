import os
from importlib import import_module
from dotenv import load_dotenv


def _load_key_from_colab() -> str | None:
    try:
        colab_module = import_module("google.colab")
        userdata = colab_module.userdata
    except Exception:
        return None

    for secret_name in ("GOOGLE_API_KEY", "api_key"):
        try:
            api_key = userdata.get(secret_name)
        except Exception:
            api_key = None

        if api_key:
            return api_key

    return None


def configure_google_api_key(env_file: str | None = ".env") -> tuple[str, str]:
    """Charge GOOGLE_API_KEY et GROQ_API_KEY depuis Colab Secrets ou un fichier .env local.

    Écrit les clés résolues dans os.environ pour LangChain, Google et Groq.
    """
    if env_file and os.path.exists(env_file):
        load_dotenv(env_file)

    google_key = _load_key_from_colab()
    if not google_key:
        google_key = os.getenv("GOOGLE_API_KEY")

    if not google_key:
        raise ValueError(
            "GOOGLE_API_KEY non trouvée. Utilisez un secret Colab ou créez un fichier .env"
        )
    os.environ["GOOGLE_API_KEY"] = google_key

    groq_key = os.getenv("GROQ_API_KEY")
    if not groq_key:
        pass

    if groq_key:
        os.environ["GROQ_API_KEY"] = groq_key
    else:
        print(
            "WARNING: GROQ_API_KEY non trouvée dans l'environnement.",
            flush=True,
        )

    return google_key, groq_key or ""
