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


def configure_google_api_key(env_file: str | None = ".env") -> str:
    """Charge GOOGLE_API_KEY depuis Colab Secrets ou depuis un fichier .env local.

    La fonction commence par essayer les secrets Google Colab quand ils sont
    disponibles, puis elle se rabat sur un fichier .env local ou sur une
    variable d'environnement déjà définie. La clé résolue est aussi écrite dans
    os.environ pour que LangChain et les clients Google puissent l'utiliser.
    """
    api_key = _load_key_from_colab()

    if not api_key and env_file:
        load_dotenv(env_file)
        api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        api_key = os.getenv("GOOGLE_API_KEY")

    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY non trouvée. Utilisez un secret Colab nommé GOOGLE_API_KEY ou créez un fichier .env à la racine du projet."
        )

    os.environ["GOOGLE_API_KEY"] = api_key
    return api_key
