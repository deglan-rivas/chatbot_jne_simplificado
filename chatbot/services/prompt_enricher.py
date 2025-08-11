def enrich_prompt(message: str, intent: str) -> str:
    # Aquí agregar terminología oficial del JNE según el intent detectado
    return f"{message} (con terminología enriquecida para {intent})"
