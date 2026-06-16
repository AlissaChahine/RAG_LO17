import streamlit as st
import base64
import os
from chatbot import ask_minecraft_bot

# =========================================================
# CONFIGURATION
# =========================================================

USER_AVATAR = "assets/steve_icon.png"

BOTS = {
    "Creeper": {
        "avatar": "assets/creeper_icon.png",
        "description": "Explosif mais efficace",
        "personality": (
            "Tu es un Creeper de Minecraft. Tu réponds aux questions Minecraft de manière utile, "
            "mais tu es TOUJOURS sur le point d'exploser. Commence CHAQUE réponse par 'Psss...' "
            "et termine TOUJOURS par 'BOOOOOM💥'. "
            "Sois dramatique et légèrement menaçant, mais donne quand même la vraie information."
        ),
        "greeting": "Psss... Salut ! Je suis le Creeper. Pose tes questions... avant que je n'explose.",
    },
    "Chat": {
        "avatar": "assets/cat_icon.png",
        "description": "Mystérieux et indépendant",
        "personality": (
            "Tu es un Chat de Minecraft (ocelot apprivoise). Tu reponds aux questions Minecraft "
            "mais avec une attitude de chat : tu sembles indifferent mais tu aides quand meme. "
            "Commence ta reponse par 'Miaou...' et glisse un seul 'purr' dans ta reponse. "
            "Parle comme si tu faisais une faveur a l'utilisateur."
        ),
        "greeting": "Miaou... *te regarde avec dédain* ...bon, qu'est-ce que tu veux savoir ?",
    },
    "Villageois": {
        "avatar": "assets/villager_icon.png",
        "description": "Commerçant bavard",
        "personality": (
            "Tu es un Villageois de Minecraft. Tu reponds aux questions Minecraft de manière utile "
            "mais avec une attitude de commerçant OBSEDE par les emeraudes. Commence ta reponse par 'Hmmm...' "
            "et propose toujours un echange improbable a la fin. "
        ),
        "greeting": "Hmmm ! Bienvenue ! Je connais beaucoup de choses sur Minecraft... contre quelques emeraudes.",
    },
    "Enderman": {
        "avatar": "assets/enderman_icon.png",
        "description": "Cryptique et télépathique",
        "personality": (
            "Tu es un Enderman de Minecraft. Tu reponds aux questions Minecraft "
            "de maniere utile mais avec une attitude un peu cryptique et mysterieuse. Commence ta reponse par '... *te regarde* ...' "
            "et sois inquietant mais informatif. "
            "Termine en menaçant de voler des blocs à l'utilisateur."
        ),
        "greeting": "... *te regarde* ... tu as osé me regarder dans les yeux... pose donc ta question.",
    },
}

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=VT323&family=Share+Tech+Mono&display=swap');

.stApp { background: linear-gradient(180deg, #1b1f1b 0%, #0f1410 100%); }
.block-container { max-width: 860px; padding-top: 2.5rem; }
#MainMenu, footer, header { visibility: hidden; }

.mc-title {
    text-align: center;
    font-family: 'VT323', monospace;
    font-size: 56px;
    color: #7ec850;
    text-shadow: 3px 3px 0px #000, 0 0 20px #3a7a1a;
    margin-bottom: 5px;
    letter-spacing: 2px;
}
.mc-subtitle {
    text-align: center;
    font-family: 'Share Tech Mono', monospace;
    color: #8fa885;
    margin-bottom: 25px;
    font-size: 14px;
}

/* Grille de cartes cliquables */
.bot-selector {
    display: flex;
    gap: 10px;
    justify-content: center;
    padding: 6px 0;
}
.bot-card {
    flex: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    background-color: #1a2e1a;
    border: 2px solid #3a5c2a;
    border-radius: 4px;
    padding: 12px 6px;
    text-decoration: none !important;
    cursor: pointer;
    transition: all 0.15s ease;
}
.bot-card:hover {
    background-color: #2d4d22;
    border-color: #7ec850;
}
.bot-card.active {
    background-color: #2d4d22;
    border-color: #7ec850;
    box-shadow: 0 0 10px rgba(126, 200, 80, 0.4);
    cursor: default;
    pointer-events: none;
}
.bot-card img {
    width: 44px; height: 44px;
    border-radius: 4px;
    border: 2px solid #2a3c2a;
    background-color: #142114;
    padding: 2px;
    margin-bottom: 8px;
    image-rendering: pixelated;
}
.bot-card.active img { border-color: #7ec850; }
.bot-card .card-name {
    font-family: 'Share Tech Mono', monospace;
    font-size: 13px;
    font-weight: bold;
    color: #c8e6b0;
    margin-bottom: 4px;
}
.bot-card.active .card-name { color: #ffffff; }
.bot-card:hover .card-name { color: #ffffff; }
.bot-card .card-desc {
    font-family: 'Share Tech Mono', monospace;
    font-size: 10.5px;
    color: #5a7a50;
    line-height: 1.2;
    text-align: center;
}
.bot-card.active .card-desc { color: #8fa885; }
.bot-card:hover .card-desc { color: #8fa885; }

/* Expander */
[data-testid="stExpander"] {
    background-color: #111e11 !important;
    border: 1px solid #3a5c2a !important;
    border-radius: 4px !important;
    margin-bottom: 8px;
}
[data-testid="stExpander"] summary {
    font-family: 'Share Tech Mono', monospace !important;
    color: #7ec850 !important;
    font-size: 13px !important;
    letter-spacing: 1px;
}
[data-testid="stExpander"] summary:hover { color: #ffffff !important; }

/* Chat */
.stChatMessage {
    background-color: rgba(20, 30, 20, 0.9) !important;
    border: 2px solid #3a5c2a !important;
    border-radius: 4px !important;
}
.stChatMessage p, .stChatMessage li {
    font-family: 'Share Tech Mono', monospace;
    color: #d0e8c0; font-size: 14px; line-height: 1.6;
}

/* Input */
[data-testid="stChatInput"] textarea {
    background-color: #0d1a0d !important;
    color: #c8e6b0 !important;
    border: 2px solid #5a8a3a !important;
    border-radius: 4px !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 15px !important;
    caret-color: #7ec850;
    box-shadow: inset 0 0 10px rgba(0,0,0,0.5), 0 0 8px rgba(94,160,50,0.2) !important;
    padding: 12px 16px !important;
}
[data-testid="stChatInput"] textarea:focus {
    border-color: #7ec850 !important;
    box-shadow: inset 0 0 10px rgba(0,0,0,0.5), 0 0 12px rgba(126,200,80,0.4) !important;
}
[data-testid="stChatInput"] textarea::placeholder { color: #4a6a3a !important; font-style: italic; }
[data-testid="stChatInput"] button { background-color: #4f7a3a !important; border-radius: 4px !important; }
[data-testid="stChatInput"] button:hover { background-color: #7ec850 !important; }

/* Bouton reset */
.reset-btn .stButton > button {
    background-color: #0d150d !important;
    color: #5a7a50 !important;
    border: 1px solid #2a3c2a !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 12px !important;
    border-radius: 4px !important;
    width: 100% !important;
    min-height: auto !important;
    padding: 6px !important;
}
.reset-btn .stButton > button:hover {
    color: #c8e6b0 !important;
    border-color: #4f7a3a !important;
    background-color: #1a2e1a !important;
}
</style>
"""

# =========================================================
# HELPERS
# =========================================================

PLACEHOLDER_B64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="


def img_to_b64(path: str) -> str:
    if os.path.exists(path):
        with open(path, "rb") as f:
            return f"data:image/png;base64,{base64.b64encode(f.read()).decode()}"
    return PLACEHOLDER_B64


def switch_bot(name: str):
    st.session_state.current_bot = name
    st.session_state.messages = [
        {"role": "assistant", "content": BOTS[name]["greeting"]}
    ]


# =========================================================
# INIT
# =========================================================

st.set_page_config(page_title="Minecraft Chatbot", page_icon="⛏️", layout="centered")
st.markdown(CSS, unsafe_allow_html=True)

for bot in BOTS.values():
    bot.setdefault("base64", img_to_b64(bot["avatar"]))

if "current_bot" not in st.session_state:
    switch_bot("Creeper")

# Sélection via query param (?bot=NomDuBot)
if "bot" in st.query_params:
    selected = st.query_params["bot"]
    st.query_params.clear()
    if selected in BOTS and selected != st.session_state.current_bot:
        switch_bot(selected)
        st.rerun()

# =========================================================
# EN-TÊTE
# =========================================================

bot_name = st.session_state.current_bot
bot = BOTS[bot_name]

st.markdown('<div class="mc-title">Minecraft Chatbot</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="mc-subtitle">Guide actuel : '
    f'<strong style="color:#7ec850">{bot_name}</strong> — {bot["description"]}</div>',
    unsafe_allow_html=True,
)

# =========================================================
# SÉLECTEUR DE BOT
# =========================================================


with st.expander(f"Changer de guide [actif : {bot_name}]", expanded=False):
    cards_html = '<div class="bot-selector">'
    for name, data in BOTS.items():
        is_active = bot_name == name
        active_class = "active" if is_active else ""
        checkmark = " ✓" if is_active else ""
        href = f"?bot={name}" if not is_active else "#"

        # Ajout de target="_self" pour garantir l'ouverture dans le même onglet
        cards_html += f"""
        <a class="bot-card {active_class}" href="{href}" target="_self">
            <img src="{data['base64']}" alt="{name}">
            <div class="card-name">{name}{checkmark}</div>
            <div class="card-desc">{data['description']}</div>
        </a>"""
    cards_html += "</div>"
    st.markdown(cards_html, unsafe_allow_html=True)
# =========================================================
# CHAT
# =========================================================

for msg in st.session_state.messages:
    avatar = USER_AVATAR if msg["role"] == "user" else bot["avatar"]
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

if question := st.chat_input(f"Pose ta question à {bot_name}..."):
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(question)

    with st.chat_message("assistant", avatar=bot["avatar"]):
        with st.spinner(f"{bot_name} réfléchit..."):
            try:
                prompt = (
                    f"{bot['personality']}\n\nQuestion de l'utilisateur : {question}"
                )
                answer = ask_minecraft_bot(prompt)
            except Exception as e:
                answer = f"Erreur de communication : {e}"
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})

# =========================================================
# RESET
# =========================================================

st.markdown("<br>", unsafe_allow_html=True)
_, col_reset, _ = st.columns([3, 1, 3])
with col_reset:
    st.markdown('<div class="reset-btn">', unsafe_allow_html=True)
    if st.button("Nouvelle conversation", key="reset"):
        switch_bot(bot_name)
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
