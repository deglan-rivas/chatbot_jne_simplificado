import math
import os
import unicodedata
import logging
from dataclasses import dataclass
from functools import lru_cache
from typing import Dict, Iterable, List, Optional, Tuple

from dotenv import load_dotenv
from google import genai

load_dotenv()

logger = logging.getLogger(__name__)


def _strip_accents(text: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", text or "")
        if unicodedata.category(c) != "Mn"
    )


def _normalize(text: str) -> str:
    text = _strip_accents(text.lower())
    cleaned = []
    for ch in text:
        if ch.isalnum() or ch.isspace():
            cleaned.append(ch)
        else:
            cleaned.append(" ")
    text = "".join(cleaned)
    return " ".join(text.split())


def _cosine_similarity(a: Iterable[float], b: Iterable[float]) -> float:
    dot = 0.0
    norm_a = 0.0
    norm_b = 0.0
    for va, vb in zip(a, b):
        dot += va * vb
        norm_a += va * va
        norm_b += vb * vb
    if norm_a <= 0.0 or norm_b <= 0.0:
        return 0.0
    return dot / (math.sqrt(norm_a) * math.sqrt(norm_b))


@lru_cache(maxsize=None)
def _default_synonyms() -> Dict[str, List[str]]:
    return {
        "procesos_electorales": [
            "procesos electorales",
            "informacion de elecciones",
            "cronograma electoral",
            "calendario electoral",
            "candidatos",
            "consulta de politico",
            "politicos",
        ],
        "organizaciones_politicas": [
            "organizaciones politicas",
            "partidos",
            "movimientos",
            "afiliacion",
            "afiliarme",
            "registro de partidos",
        ],
        "informacion_institucional": [
            "informacion institucional",
            "pleno",
            "funcionarios",
            "sedes",
            "jurados electorales",
        ],
        "servicios_digitales": [
            "servicios digitales",
            "tramites",
            "multas",
            "consultas virtuales",
            "servicios al ciudadano",
        ],
        "cronograma_electoral": [
            "cronograma electoral",
            "fechas de elecciones",
            "plazos",
            "calendario",
        ],
        "consulta_politico": [
            "consulta de politico",
            "buscar politico",
            "buscar candidato",
            "informacion de candidatos",
        ],
        "organizacion_politica": [
            "tipos de organizaciones politicas",
            "tipos de partidos",
            "tipos de movimientos",
        ],
        "consulta_afiliacion": [
            "consulta de afiliacion",
            "ver mi afiliacion",
            "buscar afiliacion",
            "afiliarme",
        ],
        "pleno": [
            "pleno del jne",
            "miembros del pleno",
            "presidencia",
        ],
        "funcionarios": [
            "funcionarios",
            "directivos",
            "autoridades",
            "directores",
        ],
        "jee": [
            "jurados electorales especiales",
            "jurado electoral especial",
            "jee",
        ],
        "sedes": [
            "sedes",
            "oficinas",
            "direcciones",
            "ubicaciones",
        ],
        "servicios_ciudadano": [
            "servicios para el ciudadano",
            "servicios mas usados",
            "tramites frecuentes",
        ],
        "tramite": [
            "tramite especifico",
            "consultar un tramite",
            "informacion de multas",
            "presentar solicitud",
        ],
    }


@dataclass
class RouteResult:
    option_key: Optional[str]
    score: float = 0.0


class MenuIntentRouter:
    """Gestiona embeddings y mapeo semantico dentro del menu actual."""

    def __init__(
        self,
        *,
        threshold: Optional[float] = None,
        embedding_model: Optional[str] = None,
    ) -> None:
        self.threshold = float(os.getenv("MENU_ROUTER_THRESHOLD", threshold or 0.76))
        self.embedding_model = os.getenv(
            "MENU_ROUTER_EMBED_MODEL",
            embedding_model or "text-embedding-004",
        )

        self._client = genai.Client()
        self._synonyms = _default_synonyms()
        self._menu_embeddings: Dict[str, Dict[str, List[float]]] = {}
        self._menu_phrases: Dict[str, Dict[str, List[str]]] = {}
        self._menu_signatures: Dict[str, Tuple] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def route_within_menu(
        self,
        user_text: str,
        menu_name: str,
        menus: Dict,
    ) -> RouteResult:
        """Devuelve la opcion (option_key) que mejor coincide dentro del menu actual."""

        user_norm = _normalize(user_text)
        options = menus.get(menu_name, {}).get("options", {})
        if not options:
            return RouteResult(None, 0.0)

        # Actualizar embeddings si el menu cambió (dinamicos)
        self._ensure_menu_embeddings(menu_name, menus)

        # Coincidencia directa por frases
        phrase_key = self._match_by_phrase(user_norm, menu_name)
        if phrase_key:
            return RouteResult(phrase_key, 1.0)

        user_embedding = self._embed_text(user_text)
        if user_embedding:
            scores = []
            embeddings = self._menu_embeddings.get(menu_name, {})
            for option_key, option_embedding in embeddings.items():
                if not option_embedding:
                    continue
                score = _cosine_similarity(user_embedding, option_embedding)
                scores.append((option_key, score))

            if scores:
                scores.sort(key=lambda item: item[1], reverse=True)
                logger.debug(
                    "menu-router scores menu=%s top=%s threshold=%.2f",
                    menu_name,
                    scores[:3],
                    self.threshold,
                )
                best_key, best_score = scores[0]
                if best_score >= self.threshold:
                    return RouteResult(best_key, best_score)

        # Fallback simple (bag of words / tf-idf ligero)
        fallback_key, fallback_score = self._fallback_tfidf(user_norm, menu_name)
        if fallback_key is not None:
            logger.debug(
                "menu-router fallback menu=%s candidate=%s score=%.3f",
                menu_name,
                fallback_key,
                fallback_score,
            )
        if fallback_key is not None and fallback_score >= 0.35:
            return RouteResult(fallback_key, fallback_score)

        return RouteResult(None, 0.0)

    # ------------------------------------------------------------------
    # Construcción de embeddings
    # ------------------------------------------------------------------
    def _ensure_menu_embeddings(self, menu_name: str, menus: Dict) -> None:
        signature = self._menu_signature(menu_name, menus)
        if signature == self._menu_signatures.get(menu_name):
            return

        menu_info = menus.get(menu_name, {})
        options = menu_info.get("options", {})
        option_embeddings: Dict[str, List[float]] = {}
        option_phrases: Dict[str, List[str]] = {}

        for option_number, option_key in options.items():
            phrases = self._build_phrases(menu_name, option_number, option_key, menus)
            option_phrases[option_key] = phrases
            text_to_embed = " \n ".join(phrases)
            embedding = self._embed_text(text_to_embed)
            option_embeddings[option_key] = embedding or []

        self._menu_embeddings[menu_name] = option_embeddings
        self._menu_phrases[menu_name] = option_phrases
        self._menu_signatures[menu_name] = signature

    def _menu_signature(self, menu_name: str, menus: Dict) -> Tuple:
        menu_info = menus.get(menu_name, {})
        options = menu_info.get("options", {})
        text = menu_info.get("text", "")
        return (menu_name, text, tuple(sorted(options.items())))

    def _build_phrases(
        self,
        menu_name: str,
        option_number: str,
        option_key: str,
        menus: Dict,
    ) -> List[str]:
        phrases: List[str] = []

        label = self._extract_label(menu_name, option_number, menus)
        if label:
            phrases.append(label)

        phrases.append(option_key.replace("_", " "))
        phrases.extend(self._synonyms.get(option_key, []))

        return phrases

    def _extract_label(self, menu_name: str, option_number: str, menus: Dict) -> Optional[str]:
        text = menus.get(menu_name, {}).get("text", "")
        for line in text.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            if stripped.startswith(f"{option_number}."):
                return stripped.split(".", 1)[1].strip()
        return None

    # ------------------------------------------------------------------
    # Coincidencias auxiliares
    # ------------------------------------------------------------------
    def _match_by_phrase(self, user_norm: str, menu_name: str) -> Optional[str]:
        phrases_by_option = self._menu_phrases.get(menu_name, {})
        for option_key, phrases in phrases_by_option.items():
            for phrase in phrases:
                norm_phrase = _normalize(phrase)
                if not norm_phrase:
                    continue
                if norm_phrase in user_norm and len(norm_phrase) >= 4:
                    return option_key
        return None

    def _fallback_tfidf(self, user_norm: str, menu_name: str) -> Tuple[Optional[str], float]:
        phrases_by_option = self._menu_phrases.get(menu_name, {})
        if not phrases_by_option:
            return None, 0.0

        user_tokens = user_norm.split()
        if not user_tokens:
            return None, 0.0

        token_set = set(user_tokens)
        best_key = None
        best_score = 0.0

        for option_key, phrases in phrases_by_option.items():
            option_tokens = set()
            for phrase in phrases:
                option_tokens.update(_normalize(phrase).split())

            if not option_tokens:
                continue

            overlap = token_set.intersection(option_tokens)
            if not overlap:
                continue

            score = len(overlap) / len(option_tokens)
            if score > best_score:
                best_key = option_key
                best_score = score

        return best_key, best_score

    # ------------------------------------------------------------------
    # Embeddings utilities
    # ------------------------------------------------------------------
    def _embed_text(self, text: str) -> Optional[List[float]]:
        cleaned = text.strip()
        if not cleaned:
            return None

        extractors = [
            lambda resp: getattr(resp, "values", None),
            lambda resp: getattr(getattr(resp, "embedding", None), "values", None),
            lambda resp: [emb.values for emb in getattr(resp, "embeddings", [])],
        ]

        try:
            response = self._client.models.embed_content(
                model=self.embedding_model,
                contents=cleaned,
            )
            vector = self._extract_embedding(response, extractors)
            if vector is not None:
                return vector
        except Exception:
            pass

        # Intento alternativo con lista de contenidos
        try:
            response = self._client.models.embed_content(
                model=self.embedding_model,
                contents=[cleaned],
            )
            vector = self._extract_embedding(response, extractors)
            if isinstance(vector, list) and vector and isinstance(vector[0], list):
                return vector[0]
            if vector is not None:
                return vector
        except Exception:
            pass

        return None

    def _extract_embedding(self, response, extractors: List) -> Optional[List[float]]:
        for extractor in extractors:
            try:
                value = extractor(response)
            except Exception:
                continue
            if value is None:
                continue
            if isinstance(value, list):
                if value and isinstance(value[0], list):
                    return value[0]
                return value
        return None


GREETINGS = {
    "hola",
    "holi",
    "holis",
    "buenas",
    "buenos dias",
    "buenas tardes",
    "buenas noches",
    "buen dia",
    "hello",
    "hi",
}


def is_greeting(text: str) -> bool:
    norm = _normalize(text)
    if norm in GREETINGS:
        return True
    return any(norm.startswith(prefix) for prefix in ("hola", "buen", "hello", "hi")) and len(norm.split()) <= 5
