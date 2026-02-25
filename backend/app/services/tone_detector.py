"""
Detector de tom de comunicação do lead.
Analisa as últimas mensagens e retorna "formal" ou "informal".
Usado para espelhar o tom do lead nos templates de resposta.
"""

from typing import List

INFORMAL_MARKERS = {
    "oi", "blz", "vlw", "valeu", "cara", "mano", "tmj",
    "kk", "kkk", "haha", "rsrs", "top", "show", "massa",
    "parceiro", "brother", "bro", "pow", "po", "q", "vc",
    "td", "tdo", "tá", "ta", "né", "ne", "tb", "tbm"
}

FORMAL_MARKERS = {
    "senhor", "senhora", "prezado", "prezada", "gostaria",
    "por gentileza", "poderia", "solicito", "atenciosamente",
    "cordialmente", "informo", "comunico", "venho", "solicitar",
    "por favor", "agradeço", "obrigado", "obrigada"
}


def detect_tone(conversation_history) -> str:
    """
    Analisa últimas 3 mensagens do lead e retorna "formal" ou "informal".
    Default: "informal" (mais natural para WhatsApp).

    Args:
        conversation_history: lista de ConversationMessage ou BaseMessage do LangChain
    """
    if not conversation_history:
        return "informal"

    # Pegar últimas 3 mensagens do usuário
    user_messages = []
    for msg in reversed(conversation_history):
        # Suporta tanto ConversationMessage (role) quanto LangChain (type)
        is_user = False
        content = ""

        if hasattr(msg, "role"):
            is_user = msg.role == "user"
            content = msg.content or ""
        elif hasattr(msg, "type"):
            is_user = msg.type == "human"
            content = msg.content or ""

        if is_user:
            user_messages.append(content.lower())
            if len(user_messages) >= 3:
                break

    if not user_messages:
        return "informal"

    # Contar marcadores
    informal_count = 0
    formal_count = 0

    for msg in user_messages:
        words = msg.split()
        for word in words:
            # Limpar pontuação
            clean_word = word.strip(".,!?;:")
            if clean_word in INFORMAL_MARKERS:
                informal_count += 1
            if clean_word in FORMAL_MARKERS:
                formal_count += 1

        # Checar frases multi-palavra
        for marker in FORMAL_MARKERS:
            if " " in marker and marker in msg:
                formal_count += 1

    # Formal só prevalece se tiver marcadores formais sem informais
    if formal_count > 0 and informal_count == 0:
        return "formal"

    return "informal"
