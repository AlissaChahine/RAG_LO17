from self_rag import ask_with_self_rag


def ask_minecraft_bot(question: str) -> str:
    return ask_with_self_rag(question, show_steps=True)