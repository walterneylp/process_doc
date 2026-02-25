
def build_classification_prompt(subject: str, sender: str, body: str) -> str:
    return (
        "Classifique o documento e retorne JSON estrito com campos: "
        "category, department, confidence, priority, reason. "
        f"Assunto: {subject}\nRemetente: {sender}\nConteudo: {body}"
    )
