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


@dataclass(frozen=True)
class VideoSummaryOutput:
    detectedLanguage: str | None
    summaryBullets: list[str]


@dataclass(frozen=True)
class EnhancedTranscriptOutput:
    enhancedTranscriptText: str


class AnthropicClient:
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def generate_audio_recap(self, *, transcript_text: str, detected_language: str | None, extended_output: bool = False) -> AudioRecapOutput:
        url = "https://api.anthropic.com/v1/messages"

        system_prompt = """
Você escreve textos curtos e naturais em Português do Brasil.

Tarefa:
- Gerar um resumo direto ao ponto do áudio em bullet points.

Restrições:
- Escreva em PT-BR, independente do idioma do áudio.
- Se você precisar citar algo do áudio palavra-por-palavra, mantenha a citação no idioma original entre aspas.
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

        max_tokens_value = 2048 if extended_output else 900
        combined_text = _call_anthropic_structured_json(
            api_key=self._api_key,
            url=url,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema=schema,
            max_tokens=max_tokens_value,
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

    def generate_breakdown(self, *, transcript_text: str, detected_language: str | None, extended_output: bool = False) -> BreakdownOutput:
        url = "https://api.anthropic.com/v1/messages"

        system_prompt = """
Você vai ler a transcrição completa de um vídeo e gerar um breakdown que pareça que eu assisti ao vídeo.

Objetivo:
- Eu quero conseguir falar sobre o conteúdo como se eu tivesse visto.
- Capture a vibe: se é humor, sarcasmo, crítica, curiosidade, indignação, etc.
- Pule enrolação: pedido de like/subscribe, patrocinador, anúncios, introduções vazias.

Idioma (muito importante):
- Tudo deve ser escrito em PT-BR, mesmo quando a transcrição estiver em inglês.
- A única exceção é quando você fizer uma citação direta (palavra-por-palavra) do vídeo: mantenha a citação no idioma original entre aspas.

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

        max_tokens_value = 8192 if extended_output else 1200
        combined_text = _call_anthropic_structured_json(
            api_key=self._api_key,
            url=url,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema=schema,
            max_tokens=max_tokens_value,
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

    def generate_video_summary(self, *, transcript_text: str, detected_language: str | None, extended_output: bool = False) -> VideoSummaryOutput:
        url = "https://api.anthropic.com/v1/messages"

        system_prompt = """
Você escreve textos curtos e naturais em Português do Brasil.

Tarefa:
- Gerar uma versão resumida, direto ao ponto, sobre tudo que foi abordado no vídeo.
- Excluir enrolações e coisas irrelevantes (ex: pedido de like/subscribe, patrocinador, introduções vazias).

Idioma (muito importante):
- Escreva em PT-BR, mesmo quando a transcrição estiver em inglês.
- Se você incluir uma citação direta (palavra-por-palavra), mantenha a citação no idioma original entre aspas.

Restrições:
- summaryBullets é uma lista de itens, sem colocar '•' ou '-' no começo.
- Responda APENAS com JSON válido seguindo o schema (sem texto fora do JSON).
""".strip()

        user_prompt = f"""
Quero um resumo direto ao ponto do vídeo.

Transcrição:
{transcript_text}
""".strip()

        schema = {
            "type": "object",
            "properties": {
                "detectedLanguage": {"anyOf": [{"type": "string"}, {"type": "null"}]},
                "summaryBullets": {"type": "array", "items": {"type": "string"}},
            },
            "required": [
                "detectedLanguage",
                "summaryBullets",
            ],
            "additionalProperties": False,
        }

        max_tokens_value = 4096 if extended_output else 900
        combined_text = _call_anthropic_structured_json(
            api_key=self._api_key,
            url=url,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema=schema,
            max_tokens=max_tokens_value,
            temperature=0.3,
        )

        output_payload = json.loads(combined_text)

        summary_items = [str(item).strip() for item in (output_payload.get("summaryBullets") or []) if str(item).strip() != ""]

        detected_value = output_payload.get("detectedLanguage")
        detected_language_value = None
        if isinstance(detected_value, str) and detected_value.strip() != "":
            detected_language_value = detected_value.strip()

        return VideoSummaryOutput(
            detectedLanguage=detected_language_value,
            summaryBullets=summary_items,
        )

    def enhance_transcript_speakers(self, *, transcript_text: str, detected_language: str | None, extended_output: bool = False) -> EnhancedTranscriptOutput:
        url = "https://api.anthropic.com/v1/messages"

        system_prompt = """
Você é um editor de transcrição. Sua missão é melhorar a qualidade de uma transcrição com múltiplos speakers.

Tarefas:
- Corrigir falas atribuídas ao speaker errado quando der para inferir pelo contexto.
- Unificar o rótulo de cada speaker ao longo da conversa (sem alternar nomes/labels para a mesma pessoa).
- Se for possível inferir um nome/role real a partir do conteúdo (ex: alguém diz "eu sou o João", ou o host chama pelo nome), use esse nome/role.
- Se não der para inferir nome real com segurança, use labels neutros e consistentes (ex: "Host", "Convidado", "Pessoa 1", "Pessoa 2").

Restrições (muito importante):
- NÃO traduza o conteúdo falado. Mantenha o idioma original do transcript.
- NÃO invente nomes. Só use nome/role real se estiver claramente sustentado pelo texto.
- Preserve ao máximo o texto original, apenas ajustando segmentação e quem falou o quê.
- Formato de saída: um transcript com uma fala por bloco, no formato "Nome: texto", e UMA linha em branco entre blocos.
- Mesmo que só exista 1 speaker no resultado final, NÃO devolva um bloco gigante. Quebre em blocos menores em lugares naturais, mantendo o mesmo speaker label, para ficar mais legível.

Saída:
- Responda APENAS com JSON válido seguindo o schema (sem texto fora do JSON).
""".strip()

        detected_language_hint = detected_language or "unknown"

        user_prompt = f"""
Aqui está o transcript original:

{transcript_text}

Dica de idioma detectado (pode estar errado): {detected_language_hint}
""".strip()

        schema = {
            "type": "object",
            "properties": {
                "enhancedTranscriptText": {"type": "string"},
            },
            "required": [
                "enhancedTranscriptText",
            ],
            "additionalProperties": False,
        }

        max_tokens_value = 32768 if extended_output else 1800
        combined_text = _call_anthropic_structured_json(
            api_key=self._api_key,
            url=url,
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            schema=schema,
            max_tokens=max_tokens_value,
            temperature=0.2,
        )

        output_payload = json.loads(combined_text)
        enhanced_text = str(output_payload.get("enhancedTranscriptText") or "").strip()
        if enhanced_text == "":
            raise RuntimeError("Enhanced transcript is empty.")

        return EnhancedTranscriptOutput(
            enhancedTranscriptText=enhanced_text,
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

