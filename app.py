import streamlit as st
from chatbot import ask_minecraft_bot  # ta fonction externe

# =========================================================
# CONFIG
# =========================================================

LOGO = "assets/minecraft_logo.png"
BANNER = "assets/header.jpg"
USER_AVATAR = "assets/steve_icon.png"
BOT_AVATAR = "assets/creeper_icon.png"

st.set_page_config(page_title="Minecraft Chatbot", page_icon="⛏️", layout="wide")

# =========================================================
# STYLE
# =========================================================

st.markdown(
    """
<style>

.stApp {
    background: linear-gradient(180deg, #1b1f1b 0%, #0f1410 100%);
}

/* container */
.block-container {
    max-width: 900px;
    padding-top: 1.5rem;
}

/* cacher UI streamlit */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* titre */
.title {
    text-align:center;
    font-size: 42px;
    font-weight: bold;
    color: #e6e6e6;
    text-shadow: 3px 3px 0px #000;
    margin-bottom: 0px;
}

/* sous titre */
.subtitle {
    text-align:center;
    color: #b5c0b0;
    margin-bottom: 20px;
}

/* chat messages */
.stChatMessage {
    background-color: rgba(25, 35, 25, 0.85);
    border: 2px solid #4f7a3a;
    border-radius: 12px;
}

/* input */
[data-testid="stChatInput"] textarea {
    background-color: #101810 !important;
    color: white !important;
    border: 2px solid #4f7a3a !important;
    border-radius: 10px;
}

/* boutons */
.stButton > button {
    background-color: #4f7a3a;
    color: white;
    border-radius: 8px;
    border: 1px solid #2d4d22;
}

.stButton > button:hover {
    background-color: #5f8f45;
}

/* avatars */
[data-testid="chatAvatarIcon-user"] {
    background-color: #2b6cb0;
}

[data-testid="chatAvatarIcon-assistant"] {
    background-color: #2f855a;
}
/* remove spacing around image */
[data-testid="stImage"] {
    margin-top: 0px !important;
    margin-bottom: 0px !important;
}

/* remove markdown spacing */
.title {
    margin-top: 0px !important;
    margin-bottom: 5px !important;
}

.subtitle {
    margin-top: 0px !important;
    margin-bottom: 10px !important;
}

/* reduce column padding */
[data-testid="column"] {
    padding-top: 0rem !important;
}

</style>
""",
    unsafe_allow_html=True,
)

# =========================================================
# HEADER
# =========================================================

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.image(LOGO, width=500)

st.markdown(
    """
<div class="title">Minecraft Chatbot</div>
<div class="subtitle">
Pose tes questions : survie, crafting, Nether, End, mobs, redstone...
</div>
""",
    unsafe_allow_html=True,
)

# =========================================================
# SESSION STATE
# =========================================================

if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "assistant",
            "content": "Salut ! Je suis ton assistant Minecraft. Que veux-tu savoir ?",
        }
    ]

# =========================================================
# DISPLAY CHAT
# =========================================================

for msg in st.session_state.messages:

    avatar = USER_AVATAR if msg["role"] == "user" else BOT_AVATAR

    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])

# =========================================================
# INPUT
# =========================================================

question = st.chat_input("Ex : Comment survivre dans le Nether ?")

if question:

    # user message
    st.session_state.messages.append({"role": "user", "content": question})

    with st.chat_message("user", avatar=USER_AVATAR):
        st.markdown(question)

    # bot response
    with st.chat_message("assistant", avatar=BOT_AVATAR):

        with st.spinner("Chargement des connaissances Minecraft..."):

            try:
                answer = ask_minecraft_bot(question)
            except Exception as e:
                answer = f"Erreur : {e}"

        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})

# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.image(LOGO, width=180)

    st.markdown("## 🧭 Guide Minecraft")

    st.markdown("""
### Exemples :

- Comment battre l’Ender Dragon ?
- Comment obtenir de la Netherite ?
- Comment faire une potion ?
- Comment survivre dans le Nether ?
- Comment utiliser la redstone ?
- Quels sont les mobs dangereux ?
""")

    if st.button("Nouvelle conversation"):
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Nouvelle partie lancée ! Que veux-tu savoir ?",
            }
        ]
        st.rerun()
