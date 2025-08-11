def validate_intent(message: str) -> str:
    # Aquí va la lógica para detectar el tema:
    # "procesos_electorales", "sistemas_integrados", "conoce_al_jne", "out_of_scope"
    # También debe filtrar prompt injection
    return "procesos_electorales"
