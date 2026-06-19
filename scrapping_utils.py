from pathlib import Path
import os
import json
import shutil
import re
from bs4 import BeautifulSoup
from langchain_core.documents import Document


# -----------------------------------------------------------GENERAL-------------------------------------------------------------
def get_all_relative_filenames(directory_path: str = "files/") -> list[str]:
    """Retourne les chemins relatifs de tous les fichiers (sans l'extension .txt)

    en conservant la structure des sous-dossiers.
    """
    root = Path(directory_path)

    paths = []
    for f in root.rglob("*"):
        if f.is_file():
            # 1. On obtient le chemin relatif par rapport au dossier racine
            #    Ex: "files/jeux/zelda.txt" -> "jeux/zelda.txt"
            relative_path = f.relative_to(root)

            # 2. On retire l'extension .txt (ou autre) en prenant le parent + le stem
            #    Ex: "jeux/zelda.txt" -> "jeux/zelda"
            if relative_path.parent != Path("."):
                # Si le fichier est dans un sous-dossier
                clean_path = f"{relative_path.parent}/{relative_path.stem}"
            else:
                # Si le fichier est directement à la racine de "files/"
                clean_path = relative_path.stem

            paths.append(clean_path)

    return paths


def page_loaded(page_name: str) -> bool:
    file_name = Path(f"files/{page_name}.txt")
    return file_name.exists()


def write_txt(file_name, paragraphs):
    # Crée le dossier parent automatiquement s'il n'existe pas
    folder = os.path.dirname(file_name)
    if folder:
        os.makedirs(folder, exist_ok=True)

    # Sauvegarde au format JSON Lines (JSONL) pour éviter les corruptions de texte
    with open(file_name, "w", encoding="utf-8") as f:
        for p in paragraphs:
            f.write(json.dumps(p, ensure_ascii=False) + "\n")


def reset_vector_db(
    chroma_dir="./chroma_minecraft_multivec", store_dir="./local_chunks_store"
):
    """
    Supprime complètement Chroma et le LocalFileStore.
    """

    # Supprimer Chroma
    if os.path.exists(chroma_dir):
        shutil.rmtree(chroma_dir)
        print(f"Supprimé : {chroma_dir}")

    # Supprimer les chunks bruts
    if os.path.exists(store_dir):
        shutil.rmtree(store_dir)
        print(f"Supprimé : {store_dir}")

    # Recréer dossiers vides
    os.makedirs(chroma_dir, exist_ok=True)
    os.makedirs(store_dir, exist_ok=True)

    print("Base réinitialisée.")


# ----------------------------------------------------------------WIKIPEDIA-----------------------------------------------------------------
def parse_wikipedia_sections(soup, source):

    docs = []
    h2 = None
    h3 = None
    h4 = None
    current_text = []

    def save_section():
        nonlocal current_text
        text = "\n".join(current_text).strip()
        # ignorer sections vides
        if not text:
            current_text = []
            return
        title_parts = [x for x in [h2, h3, h4] if x]
        section_title = " > ".join(title_parts)
        if section_title in ["", " "]:
            section_title_title = "Introduction"
        docs.append(
            Document(
                page_content=text, metadata={"source": source, "section": section_title}
            )
        )
        current_text = []

    for tag in soup.find_all(["h2", "h3", "h4", "p", "li"]):
        txt = tag.get_text(" ", strip=True)
        if not txt:
            continue
        # arrêt avant les sections inutiles
        if tag.name == "h2" and any(
            x in txt
            for x in [
                "Références",
                "Notes et références",
                "Voir aussi",
                "Liens externes",
                "Accueil",
                "Autres versions",
            ]
        ):
            break
        if tag.name == "h3" and any(x in txt for x in ["Autres versions"]):
            break
        if tag.name == "h2":
            save_section()
            h2 = txt
            h3 = None
            h4 = None
        elif tag.name == "h3":
            save_section()
            h3 = txt
            h4 = None
        elif tag.name == "h4":
            save_section()
            h4 = txt
        else:
            current_text.append(txt)
    save_section()
    return docs


# ----------------------------------------------------------------WIKI MINECRAFT-----------------------------------------------------------------


def clean_wiki_text(text: str) -> str:

    # Guillemets typographiques → guillemets simples
    text = text.replace("\u00ab", '"').replace("\u00bb", '"')
    text = text.replace("\u2018", "'").replace("\u2019", "'")
    text = text.replace("\u201c", '"').replace("\u201d", '"')
    text = text.replace("\u2026", "...")

    # Liens wiki [[Page|texte]] → texte, [[Page]] → Page
    text = re.sub(r"\[\[(?:[^|\]]*\|)?([^\]]+)\]\]", r"\1", text)

    # Templates simples {{nom|val}} → val, {{nom}} → supprimé
    text = re.sub(r"\{\{[^}]*\|([^}]*)\}\}", r"\1", text)
    text = re.sub(r"\{\{[^}]*\}\}", "", text)

    # Balises HTML résiduelles
    text = re.sub(r"<[^>]+>", "", text)

    # Références [1], [note 2], etc.
    text = re.sub(r"\[\d+\]", "", text)
    text = re.sub(r"\[note \d+\]", "", text)

    # Marqueurs de version [Version Java 1.x]
    text = re.sub(r"\[Version [^\]]+\]", "", text)

    # Lignes qui ne contiennent que de la ponctuation ou des caractères spéciaux
    text = re.sub(r"^[^\w\s]{1,5}$", "", text, flags=re.MULTILINE)

    # Espaces multiples sur une même ligne
    text = re.sub(r"[ \t]+", " ", text)

    # Lignes vides multiples → une seule
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def remove_empty_sections(text: str) -> str:
    """
    Supprime les titres de section qui ne sont pas suivis de contenu.
    Ex : 'SECTION: Galerie\n\nSECTION: Combat\n' → garde seulement Combat s'il a du contenu.
    """
    lines = text.split("\n")
    result = []
    i = 0

    while i < len(lines):
        line = lines[i]

        if line.startswith("SECTION:") or line.startswith("SOUS-SECTION:"):
            # Chercher si la section a du contenu
            j = i + 1
            # Sauter les lignes vides juste après le titre
            while j < len(lines) and lines[j].strip() == "":
                j += 1

            # S'il y a du contenu non-vide et que ce n'est pas une autre section
            if j < len(lines) and not (
                lines[j].startswith("SECTION:") or lines[j].startswith("SOUS-SECTION:")
            ):
                result.append(line)
            # Sinon on saute le titre de section vide
        else:
            result.append(line)

        i += 1

    return "\n".join(result)


def remove_noise_lines(text: str) -> str:
    """
    Supprime les lignes qui ne contiennent pas assez d'information :
    - moins de 20 caractères sauf si c'est un titre de section
    - lignes qui ressemblent à des noms de fichier (image, .png, .jpg)
    - lignes qui ne sont que des chiffres ou caractères spéciaux
    """
    lines = text.split("\n")
    result = []

    for line in lines:
        stripped = line.strip()

        # Toujours garder les titres de section
        if stripped.startswith("SECTION:") or stripped.startswith("SOUS-SECTION:"):
            result.append(line)
            continue

        # Supprimer les noms de fichiers image
        if re.match(r"(?i).*\.(png|jpg|jpeg|gif|svg|webp|ogg|mp3|wav)$", stripped):
            continue

        # Supprimer les lignes trop courtes (bruit)
        if len(stripped) < 20 and stripped != "":
            continue

        # Supprimer les lignes qui ne sont que des chiffres/ponctuation
        if re.match(r"^[\d\s.,;:!?()\[\]«»\"'/-]+$", stripped):
            continue

        if stripped.startswith("v d m"):
            continue

        if stripped.startswith("↑"):
            continue

        if "google.fr/search" in stripped:
            continue

        if "Version Bedrock" in stripped and len(stripped) > 100:
            continue

        if "Historique des versions" in stripped and len(stripped) > 100:
            continue

        result.append(line)

    return "\n".join(result)


STOP_HEADINGS = {
    "références",
    "notes et références",
    "notes diverses",
    "voir aussi",
    "liens externes",
    "annexes",
    "galerie",
    "historique",
    "succès",
    "créatures des autres jeux",
    "créatures de minecraft earth",
    "créatures de minecraft dungeons",
    "créatures prévues",
    "créatures inutilisées",
    "créatures supprimées",
    "créatures non implémentées",
    "créatures de la version éducation",
    "tutoriels",
    "sons",
}


def extract_list(tag) -> list:
    items = []
    for li in tag.find_all("li", recursive=False):
        text_parts = []
        for node in li.children:
            if not hasattr(node, "name"):
                text_parts.append(str(node))
            elif node.name not in ["ul", "ol"]:
                text_parts.append(node.get_text(" ", strip=True))
        text = clean_wiki_text(" ".join(text_parts))
        if text and len(text) >= 15:
            items.append(f"- {text}")
        for sub in li.find_all(["ul", "ol"], recursive=False):
            for sub_item in extract_list(sub):
                items.append(f"  {sub_item}")
    return items


def get_cell_name(td):
    td = BeautifulSoup(str(td), "html.parser")

    # Remplacer les liens par leur title
    for a in td.find_all("a"):
        title = a.get("title", "").strip()
        if title and "modifier" not in title.lower():
            a.replace_with(title)

    # Remplacer les images par leur alt
    for img in td.find_all("img"):
        alt = img.get("alt", "").strip()
        if alt:
            img.replace_with(alt)

    return td.get_text(" ", strip=True)


def extract_table(tag) -> list:
    rows = []

    # Récupérer les en-têtes
    headers = []
    header_row = tag.find("tr")
    if header_row:
        headers = [
            clean_wiki_text(th.get_text(" ", strip=True))
            for th in header_row.find_all("th")
            if len(th.get_text(strip=True)) >= 2
        ]

    for tr in tag.find_all("tr"):
        cells = []
        for td in tr.find_all("td"):
            cell_text = clean_wiki_text(get_cell_name(td))
            if cell_text and len(cell_text) >= 2:
                cells.append(cell_text)

        if not cells:
            continue

        if headers and len(headers) == len(cells):
            parts = [f"{h} : {c}" for h, c in zip(headers, cells)]
            rows.append("- " + " | ".join(parts))
        else:
            rows.append("- " + " : ".join(cells))
    return rows
