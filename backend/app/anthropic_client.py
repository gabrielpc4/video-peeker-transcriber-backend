import json
from dataclasses import dataclass

import requests


@dataclass(frozen=True)
class BreakdownOutput:
    detectedLanguage: str | None
    vibe: str
    whatHappened: str
    keyPoints: list[str]
    howItWasSaid: str
    skippedAsFluff: list[str]


@dataclass(frozen=True)
class AudioRecapOutput:
    detectedLanguage: str | None
    recapBullets: list[str]


class AnthropicClient:
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def generate_audio_recap(self, *, transcript_text: str, detected_language: str | None) -> AudioRecapOutput:
        url = "https://api.anthropic.com/v1/messages"

        system_prompt = """
Você escreve textos curtos e naturais em Português do Brasil.

Tarefa:
- Gerar um resumo direto ao ponto do áudio em bullet points.

Restrições:
- recapBullets é uma lista de itens, sem colocar '•' ou '-' no começo.
- Responda APENAS com JSON válido seguindo o schema (sem texto fora do JSON).
""".strip()

        user_prompt = f"""
Quero um resumo direto ao ponto do áudio.

Transcrição:
{transcript_text}
""".strip()

        schema = {
            "type": "object",
            "properties": {
                "detectedLanguage": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                "recapBullets": {"type": "array", "items": {"type": "string"}},
            },
            "required": [
                "detectedLanguage",
                "recapBullets",
            ],
            "additionalProperties": False,
        }

        combined_text = _call_anthropic_structured_json(
            api_key=self._api_key,
            url=url,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema=schema,
            max_tokens=900,
            temperature=0.3,
        )

        output_payload = json.loads(combined_text)

        recap_items = [str(item).strip() for item in (output_payload.get("recapBullets") or []) if str(item).strip() != ""]

        detected_value = output_payload.get("detectedLanguage")
        detected_language_value = None
        if isinstance(detected_value, str) and detected_value.strip() != "":
            detected_language_value = detected_value.strip()

        return AudioRecapOutput(
            detectedLanguage=detected_language_value,
            recapBullets=recap_items,
        )

    def generate_breakdown(self, *, transcript_text: str, detected_language: str | None) -> BreakdownOutput:
        url = "https://api.anthropic.com/v1/messages"

        system_prompt = """
Você vai ler a transcrição completa de um vídeo e gerar um breakdown que pareça que eu assisti ao vídeo.

Objetivo:
- Eu quero conseguir falar sobre o conteúdo como se eu tivesse visto.
- Capture a vibe: se é humor, sarcasmo, crítica, curiosidade, indignação, etc.
- Pule enrolação: pedido de like/subscribe, patrocinador, anúncios, introduções vazias.

Saída:
- Responda APENAS com JSON válido seguindo o schema (sem texto fora do JSON).
""".strip()

        detected_language_hint = detected_language or "unknown"

        user_prompt = f"""
Transcrição:
{transcript_text}

Dica de idioma detectado (pode estar errado): {detected_language_hint}
""".strip()

        schema = {
            "type": "object",
            "properties": {
                "detectedLanguage": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                "vibe": {"type": "string"},
                "whatHappened": {"type": "string"},
                "keyPoints": {"type": "array", "items": {"type": "string"}},
                "howItWasSaid": {"type": "string"},
                "skippedAsFluff": {"type": "array", "items": {"type": "string"}},
            },
            "required": [
                "detectedLanguage",
                "vibe",
                "whatHappened",
                "keyPoints",
                "howItWasSaid",
                "skippedAsFluff",
            ],
            "additionalProperties": False,
        }

        combined_text = _call_anthropic_structured_json(
            api_key=self._api_key,
            url=url,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema=schema,
            max_tokens=1200,
            temperature=0.4,
        )

        output_payload = json.loads(combined_text)

        return BreakdownOutput(
            detectedLanguage=output_payload.get("detectedLanguage"),
            vibe=str(output_payload.get("vibe") or "").strip(),
            whatHappened=str(output_payload.get("whatHappened") or "").strip(),
            keyPoints=[str(item).strip() for item in (output_payload.get("keyPoints") or []) if str(item).strip() != ""],
            howItWasSaid=str(output_payload.get("howItWasSaid") or "").strip(),
            skippedAsFluff=[str(item).strip() for item in (output_payload.get("skippedAsFluff") or []) if str(item).strip() != ""],
        )


def _call_anthropic_structured_json(
    *,
    api_key: str,
    url: str,
    system_prompt: str,
    user_prompt: str,
    schema: dict,
    max_tokens: int,
    temperature: float,
) -> str:
    request_body = {
        "model": "claude-sonnet-4-5",
        "max_tokens": max_tokens,
        "temperature": temperature,
        "system": system_prompt,
        "messages": [{"role": "user", "content": [{"type": "text", "text": user_prompt}]}],
        "output_config": {
            "format": {
                "type": "json_schema",
                "schema": schema,
            }
        },
    }

    response = requests.post(
        url,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        data=json.dumps(request_body).encode("utf-8"),
    )

    if response.ok is False:
        raise RuntimeError(f"Anthropic error: HTTP {response.status_code}\n\n{response.text}")

    payload = response.json()
    content_blocks = payload.get("content") or []
    text_blocks = [block.get("text") for block in content_blocks if block.get("type") == "text"]
    combined_text = "\n".join([t for t in text_blocks if isinstance(t, str)])
    combined_text = combined_text.strip()

    if combined_text == "":
        raise RuntimeError("Anthropic returned empty content.")

    try:
        json.loads(combined_text)
    except Exception as error:
        raise RuntimeError(f"Anthropic did not return valid JSON.\n\n{combined_text}") from error

    return combined_text

