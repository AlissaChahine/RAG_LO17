from scrapping_utils import (
    parse_wikipedia_sections,
    write_txt,
    remove_empty_sections,
    remove_noise_lines,
    clean_wiki_text,
    STOP_HEADINGS,
    extract_list,
    extract_table,
    page_loaded,
)
import requests
from bs4 import BeautifulSoup
import cloudscraper
import re
from urllib.parse import urlparse, unquote
from langchain_core.documents import Document

scraper = cloudscraper.create_scraper()
WIKI_PAGES = "Minecraft"

FANDOM_URLS = [
    "https://minecraft.fandom.com/fr/wiki/Fabrication/Nourriture",
    "https://minecraft.fandom.com/fr/wiki/Enchantement",
    "https://minecraft.fandom.com/fr/wiki/Survie",
    "https://minecraft.fandom.com/fr/wiki/Cr%C3%A9atif",
    "https://minecraft.fandom.com/fr/wiki/Hardcore",
    "https://minecraft.fandom.com/fr/wiki/Fabrication",
    "https://minecraft.fandom.com/fr/wiki/Cuisson",
    "https://minecraft.fandom.com/fr/wiki/Alchimie",
    "https://minecraft.fandom.com/fr/wiki/La_Foire_aux_Questions",
    "https://minecraft.fandom.com/fr/wiki/Tutoriels/Choses_%C3%A0_ne_PAS_faire",
    "https://minecraft.fandom.com/fr/wiki/Tutoriels/Survie_dans_le_Nether",
    "https://minecraft.fandom.com/fr/wiki/Tutoriels/L%27End_et_l%27Ender_Dragon",
    "https://minecraft.fandom.com/fr/wiki/Cr%C3%A9atures",
    "https://minecraft.fandom.com/fr/wiki/Structures",
    "https://minecraft.fandom.com/fr/wiki/Fabrication/Outils",
    "https://minecraft.fandom.com/fr/wiki/Commerce",
    "https://minecraft.fandom.com/fr/wiki/Biome",
    "https://minecraft.fandom.com/fr/wiki/Minage",
    "https://minecraft.fandom.com/fr/wiki/Tutoriels/Guide_de_survie ",
    "https://minecraft.fandom.com/fr/wiki/Tutoriels/Le_deuxi%C3%A8me_jour",
    "https://minecraft.fandom.com/fr/wiki/Tutoriels/Les_jours_suivants",
    "https://minecraft.fandom.com/fr/wiki/Creeper ",
    "https://minecraft.fandom.com/fr/wiki/Enderman ",
    "https://minecraft.fandom.com/fr/wiki/Squelette ",
    "https://minecraft.fandom.com/fr/wiki/Zombie ",
    "https://minecraft.fandom.com/fr/wiki/Tutoriels/Combat",
    "https://minecraft.fandom.com/fr/wiki/%C3%89levage",
    "https://minecraft.fandom.com/fr/wiki/Tutoriels/Agriculture",
    "https://minecraft.fandom.com/fr/wiki/Chat",
    "https://minecraft.fandom.com/fr/wiki/Villageois",
    "https://minecraft.fandom.com/fr/wiki/Ender_Dragon",
    "https://minecraft.fandom.com/fr/wiki/Wither",
    "https://minecraft.fandom.com/fr/wiki/Tutoriels/Succ%C3%A8s",
    "https://minecraft.fandom.com/fr/wiki/Tutoriels/Loups",
]


# ---------------------------------------------------WIKIPEDIA----------------------------------------------------
def scrape_wikipedia(title: str):

    url = "https://fr.wikipedia.org/w/api.php"

    params = {
        "action": "parse",
        "page": title,
        "format": "json",
        "prop": "text",
        "redirects": True,
    }

    r = requests.get(url, params=params, headers={"User-Agent": "Mozilla/5.0"})

    data = r.json()

    html = data["parse"]["text"]["*"]
    soup = BeautifulSoup(html, "html.parser")
    docs = parse_wikipedia_sections(soup, f"wikipedia:{title}")

    docs = [
        {
            "page_content": doc.page_content,
            "source": doc.metadata.get("source"),
            "section": doc.metadata.get("section"),
        }
        for doc in docs
    ]

    write_txt(f"files/wikipedia.txt", docs)
    return docs


# ------------------------------------------------------------------FANDOM---------------------------------------------------------------


def scrape_fandom(url: str, page_name=str, mode: str = "windows"):
    if mode == "mac":
        r = requests.get(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"},
            timeout=30,
        )
    else:
        headers_req = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0 Safari/537.36"
            ),
            "Accept-Language": "fr-FR,fr;q=0.9",
            "Referer": "https://www.google.com/",
        }
        r = scraper.get(url, headers=headers_req)

    soup = BeautifulSoup(r.text, "html.parser")

    content = soup.find("div", {"class": "mw-parser-output"})
    if not content:
        return []

    # ==========================
    # CLEAN STATIC BLOCKS
    # ==========================
    selectors_to_remove = [
        "#toc",
        ".mw-references-wrap",
        "ol.references",
        ".navbox",
        ".vertical-navbox",
        ".portable-infobox",
        ".catlinks",
        ".mw-editsection",
        ".reference",
    ]

    for selector in selectors_to_remove:
        for element in content.select(selector):
            element.decompose()

    docs = []

    h2 = None
    h3 = None
    h4 = None

    current_content = []

    def save_section():
        nonlocal current_content

        text = "\n".join(current_content).strip()

        text = remove_empty_sections(text)
        text = remove_noise_lines(text)
        text = re.sub(r"\n{3,}", "\n\n", text).strip()

        if not text:
            current_content = []
            return

        section_parts = [x for x in [h2, h3, h4] if x]

        section_title = (
            "Introduction" if not section_parts else " > ".join(section_parts)
        )

        docs.append(
            Document(
                page_content=text, metadata={"source": url, "section": section_title}
            )
        )

        current_content = []

    # ==========================
    # MAIN LOOP
    # ==========================
    for tag in content.children:

        if not getattr(tag, "name", None):
            continue

        # ==========================
        # HEADINGS — h1 inclus pour FAQ
        # ==========================
        heading_tag = None

        if tag.name in ["h1", "h2", "h3", "h4"]:
            heading_tag = tag
        elif tag.name == "div" and "mw-heading" in tag.get("class", []):
            heading_tag = tag.find(["h1", "h2", "h3", "h4"], recursive=False)

        if heading_tag:
            raw_heading = heading_tag.get_text(" ", strip=True)
            heading = clean_wiki_text(raw_heading)
            heading = re.sub(r"\[.*?\]", "", heading).strip()

            if not heading:
                continue

            # ==========================
            # STOP SECTIONS
            # ==========================
            if heading.lower() in STOP_HEADINGS:
                save_section()
                break

            # ==========================
            # FAQ DETECTION
            # ==========================
            b_texts = [
                b.get_text(strip=True).lower() for b in heading_tag.find_all("b")
            ]
            is_faq = any(t == "q:" for t in b_texts)

            if is_faq:
                # Sauvegarder la section précédente (Q/R précédente)
                save_section()

                # Extraire le texte de la question sans le préfixe "Q:"
                question_text = clean_wiki_text(heading)
                question_text = re.sub(
                    r"^Q\s*:\s*", "", question_text, flags=re.IGNORECASE
                ).strip()

                # Chaque question devient sa propre section
                h2 = f"FAQ > {question_text}"
                h3 = None
                h4 = None

                # Ajouter la question en début de contenu
                current_content.append(f"Q: {question_text}")
                continue

            # ==========================
            # SECTION NORMALE
            # ==========================
            save_section()

            if heading_tag.name in ["h1", "h2"]:
                h2 = heading
                h3 = None
                h4 = None
            elif heading_tag.name == "h3":
                h3 = heading
                h4 = None
            elif heading_tag.name == "h4":
                h4 = heading

            continue

        # ==========================
        # PARAGRAPHS
        # ==========================
        if tag.name == "p":
            text = clean_wiki_text(tag.get_text(" ", strip=True))
            if not text or len(text) < 10:
                continue
            current_content.append(text)

        # ==========================
        # DL/DD — réponses FAQ et définitions
        # ==========================
        elif tag.name == "dl":
            for dd in tag.find_all("dd", recursive=True):
                raw = dd.get_text(" ", strip=True)
                # Supprimer le préfixe "R:" s'il existe
                raw = re.sub(r"^R\s*:\s*", "", raw, flags=re.IGNORECASE).strip()
                text = clean_wiki_text(raw)
                if not text or len(text) < 10:
                    continue
                current_content.append(text)

        # ==========================
        # LISTS
        # ==========================
        elif tag.name in ["ul", "ol"]:
            current_content.extend(extract_list(tag))

        # ==========================
        # TABLES
        # ==========================
        elif tag.name == "table":
            current_content.extend(extract_table(tag))

    save_section()

    page_name = unquote(url.split("/wiki/")[-1])

    print(f"FANDOM OK: {page_name} ({len(docs)} sections)")

    docs = [
        {
            "page_content": doc.page_content,
            "source": doc.metadata.get("source"),
            "section": doc.metadata.get("section"),
        }
        for doc in docs
    ]

    write_txt(f"files/{page_name}.txt", docs)

    return docs


def scrape_web(platform: str = "windows"):

    new_pages = []
    for url in FANDOM_URLS:
        parsed = urlparse(url)
        page_name = unquote(parsed.path.split("/wiki/")[-1])
        if not page_loaded(page_name):
            try:
                doc = scrape_fandom(url, page_name, mode=platform)
                if doc:
                    new_pages.append(page_name)
                    print(f"Chargement de la page {page_name} OK")
            except Exception as e:
                print("Soucis avec le chargement de la page wiki:", url, e)
        else:
            print(f"Wiki : {page_name} deja chargee")
    return new_pages
