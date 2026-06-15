import streamlit as st
from chatbot import ask_minecraft_bot

# =========================================================
# CONFIG
# =========================================================

LOGO = "assets/minecraft_logo.png"
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
    },
    "Chat": {
        "avatar": "assets/cat_icon.png",
        "description": "Mysterieux et independant",
        "personality": (
            "Tu es un Chat de Minecraft (ocelot apprivoise). Tu reponds aux questions Minecraft "
            "mais avec une attitude de chat : tu sembles indifferent mais tu aides quand meme. "
            "Commence CHAQUE reponse par 'Miaou...' et glisse un 'purr' dans ta reponse. "
            "Parle comme si tu faisais une faveur a l'utilisateur."
        ),
    },
    "Villageois": {
        "avatar": "assets/villager_icon.png",
        "description": "Commercant bavard",
        "personality": (
            "Tu es un Villageois de Minecraft. Tu reponds aux questions Minecraft de manière utile "
            "mais avec une attitude de commerçant OBSEDE par les emeraudes. Commence CHAQUE reponse par 'Hmmm...' "
            "et propose toujours un echange improbable a la fin. "
        ),
    },
    "Enderman": {
        "avatar": "assets/enderman_icon.png",
        "description": "Cryptique et telepathique",
        "personality": (
            "Tu es un Enderman de Minecraft. Tu reponds aux questions Minecraft "
            "de maniere utile mais avec une attitude un peu cryptique et mysterieuse. Commence CHAQUE reponse par '... *te regarde* ...' "
            "et sois inquietant mais informatif. "
            "Termine en menaçant de voler des blocs à l'utilisateur."
        ),
    },
}

GREETINGS = {
    "Creeper": "Psss... Salut ! Je suis le Creeper. Pose tes questions... avant que je n'explose.",
    "Chat": "Miaou... *te regarde avec dédain* ...bon, qu'est-ce que tu veux savoir ?",
    "Villageois": "Hmmm ! Bienvenue ! Je connais beaucoup de choses sur Minecraft... contre quelques emeraudes.",
    "Enderman": "... *te regarde* ... tu as osé me regarder dans les yeux... pose donc ta question.",
}

# =========================================================
# PAGE CONFIG
# =========================================================

st.set_page_config(page_title="Minecraft Chatbot", page_icon="⛏️", layout="centered")

# =========================================================
# STYLE
# =========================================================

st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=VT323&family=Share+Tech+Mono&display=swap');

.stApp {
    background: linear-gradient(180deg, #1b1f1b 0%, #0f1410 100%);
}
.block-container {
    max-width: 860px;
    padding-top: 1.5rem;
}
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

.mc-title {
    text-align: center;
    font-family: 'VT323', monospace;
    font-size: 52px;
    color: #7ec850;
    text-shadow: 3px 3px 0px #000, 0 0 20px #3a7a1a;
    margin-bottom: 0px;
    letter-spacing: 2px;
}
.mc-subtitle {
    text-align: center;
    font-family: 'Share Tech Mono', monospace;
    color: #8fa885;
    margin-bottom: 20px;
    font-size: 14px;
}

/* Selecteur de bot */
.bot-selector-label {
    font-family: 'Share Tech Mono', monospace;
    color: #7ec850;
    font-size: 13px;
    margin-bottom: 8px;
    letter-spacing: 1px;
}

/* Boutons de selection de bot */
div[data-testid="column"] .stButton > button {
    background-color: #1a2e1a !important;
    color: #c8e6b0 !important;
    border: 2px solid #3a5c2a !important;
    border-radius: 4px !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 13px !important;
    width: 100% !important;
    padding: 10px 8px !important;
    transition: all 0.15s ease;
}
div[data-testid="column"] .stButton > button:hover {
    background-color: #2d4d22 !important;
    border-color: #7ec850 !important;
    color: #ffffff !important;
}

/* Bouton reset */
.reset-btn .stButton > button {
    background-color: #0d150d !important;
    color: #5a7a50 !important;
    border: 1px solid #2a3c2a !important;
    font-family: 'Share Tech Mono', monospace !important;
    font-size: 12px !important;
    border-radius: 4px !important;
    width: 100% !important;
}
.reset-btn .stButton > button:hover {
    color: #c8e6b0 !important;
    border-color: #4f7a3a !important;
}

/* Expander sélecteur de bot */
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
[data-testid="stExpander"] summary:hover {
    color: #ffffff !important;
}

/* Separateur */
.mc-divider {
    border: none;
    border-top: 1px solid #2a3c2a;
    margin: 12px 0 16px 0;
}

/* Messages */
.stChatMessage {
    background-color: rgba(20, 30, 20, 0.9) !important;
    border: 2px solid #3a5c2a !important;
    border-radius: 4px !important;
}
.stChatMessage p, .stChatMessage li {
    font-family: 'Share Tech Mono', monospace;
    color: #d0e8c0;
    font-size: 14px;
    line-height: 1.6;
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
[data-testid="stChatInput"] textarea::placeholder {
    color: #4a6a3a !important;
    font-style: italic;
}
[data-testid="stChatInput"] button {
    background-color: #4f7a3a !important;
    border-radius: 4px !important;
}
[data-testid="stChatInput"] button:hover {
    background-color: #7ec850 !important;
}
</style>
""",
    unsafe_allow_html=True,
)

# =========================================================
# SESSION STATE
# =========================================================

if "current_bot" not in st.session_state:
    st.session_state.current_bot = "Creeper"

if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": GREETINGS["Creeper"]}]

# =========================================================
# HEADER
# =========================================================

try:
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image(LOGO, width=420)
except Exception:
    pass

st.markdown('<div class="mc-title">Minecraft Chatbot</div>', unsafe_allow_html=True)

current_bot_name = st.session_state.current_bot
current_bot = BOTS[current_bot_name]

st.markdown(
    f'<div class="mc-subtitle">Guide actuel : '
    f'<strong style="color:#7ec850">{current_bot_name}</strong>'
    f' — {current_bot["description"]}</div>',
    unsafe_allow_html=True,
)

# =========================================================
# SELECTEUR DE BOT
# =========================================================

with st.expander(f"Changer de guide  [ actif : {current_bot_name} ]", expanded=False):
    cols = st.columns(len(BOTS))
    for i, (bot_name, bot_data) in enumerate(BOTS.items()):
        with cols[i]:
            is_selected = st.session_state.current_bot == bot_name
            label = f"{bot_name}{' [actif]' if is_selected else ''}"
            if st.button(label, key=f"select_{bot_name}"):
                st.session_state.current_bot = bot_name
                st.session_state.messages = [
                    {"role": "assistant", "content": GREETINGS[bot_name]}
                ]
                st.rerun()
            st.markdown(
                f"<p style='font-family:Share Tech Mono,monospace;color:#5a7a50;"
                f"font-size:11px;text-align:center;margin-top:-6px;'>{bot_data['description']}</p>",
                unsafe_allow_html=True,
            )

st.markdown('<hr class="mc-divider">', unsafe_allow_html=True)

# =========================================================
# CHAT
# =========================================================

BOT_AVATAR = current_bot["avatar"]

for msg in st.session_state.messages:
    avatar = USER_AVATAR if msg["role"] == "user" else BOT_AVATAR
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

question = st.chat_input(f"Pose ta question a {current_bot_name}...")

if question:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(question)

    with st.chat_message("assistant", avatar=BOT_AVATAR):
        with st.spinner(f"{current_bot_name} cherche..."):
            try:
                personality = current_bot["personality"]
                enriched_question = (
                    f"{personality}\n\nQuestion de l'utilisateur : {question}"
                )
                answer = ask_minecraft_bot(enriched_question)
            except Exception as e:
                answer = f"Erreur : {e}"
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})

# =========================================================
# RESET (en bas)
# =========================================================

st.markdown("<br>", unsafe_allow_html=True)
col_reset = st.columns([3, 1, 3])
with col_reset[1]:
    st.markdown('<div class="reset-btn">', unsafe_allow_html=True)
    if st.button("Nouvelle conversation", key="reset"):
        st.session_state.messages = [
            {"role": "assistant", "content": GREETINGS[current_bot_name]}
        ]
        st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)
