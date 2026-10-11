
import logging
import time

from google import genai
from google.genai import errors, types

from app.core.config import settings

logger = logging.getLogger(__name__)


def generate_ai_response(message: str) -> str:
    if not settings.gemini_api_key:
        raise RuntimeError("GEMINI_API_KEY is not configured")

    client = genai.Client(
        api_key=settings.gemini_api_key,
        http_options=types.HttpOptions(
            timeout=20000,  # 20 seconds per request
        ),
    )

    prompt = (
        "You are a helpful customer support assistant. "
        "Answer clearly, politely, and concisely. "
        "If you do not know an order status or company-specific "
        "detail, do not invent it. Ask the customer for more "
        "information when needed.\n\n"
        f"Customer message: {message}"
    )

    # Retry temporary Gemini overloads up to 3 attempts.
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=settings.gemini_model,
                contents=prompt,
            )

            answer = response.text

            if not answer or not answer.strip():
                raise RuntimeError("Gemini returned an empty response")

            return answer.strip()

        except errors.ServerError as exc:
            if exc.code != 503 or attempt == 2:
                logger.exception("Gemini server error")
                raise

            logger.warning(
                "Gemini temporarily unavailable. Retry %s of 2.",
                attempt + 1,
            )
            time.sleep(1 + attempt)

    raise RuntimeError("Gemini could not generate a response")