def run_langgraph(prompt: str, user_id: str) -> str:
    # Aquí se define el grafo de LangGraph con nodos simples:
    # - Intent validator
    # - Retriever local
    # - LLM answer
    # También se puede usar Redis para memoria corta
    return "Respuesta generada por LLM"
