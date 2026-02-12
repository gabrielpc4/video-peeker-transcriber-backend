import json
import re
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

        enhanced_text = _make_single_speaker_transcript_more_breathable(enhanced_text)

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


_SPEAKER_LINE_RE = re.compile(r"^(?P<speaker>[^:\n]{1,60}):\s+(?P<text>\S.+)$")


def _count_distinct_speakers(transcript_text: str) -> set[str]:
    speakers: set[str] = set()
    for raw_line in transcript_text.splitlines():
        line = raw_line.strip()
        if line == "":
            continue
        match = _SPEAKER_LINE_RE.match(line)
        if match is None:
            continue
        speaker = (match.group("speaker") or "").strip()
        if speaker != "":
            speakers.add(speaker)
    return speakers


def _paragraphize_text(text: str, *, target_chars: int = 200, min_sentences: int = 2) -> str:
    """
    Insert blank lines to make long single-speaker transcript blocks easier to read.
    We keep the original wording; only add paragraph breaks.
    """
    cleaned = " ".join(text.strip().split())
    if cleaned == "":
        return ""

    # Rough sentence splitter. Good enough for readability without LLM cost.
    sentences = re.split(r"(?<=[\.\!\?\…])\s+", cleaned)
    sentences = [s.strip() for s in sentences if s.strip() != ""]
    if len(sentences) <= 3:
        return cleaned

    paragraphs: list[str] = []
    current: list[str] = []
    current_len = 0

    for sentence in sentences:
        current.append(sentence)
        current_len += len(sentence) + 1

        if len(current) >= min_sentences and current_len >= target_chars:
            paragraphs.append(" ".join(current).strip())
            current = []
            current_len = 0

    if len(current) > 0:
        paragraphs.append(" ".join(current).strip())

    # If we failed to create multiple paragraphs, keep as-is.
    if len(paragraphs) <= 1:
        return cleaned

    return "\n\n".join(paragraphs)


def _make_single_speaker_transcript_more_breathable(enhanced_transcript_text: str) -> str:
    """
    If an enhanced transcript ends up with only one (or zero) distinct speaker labels,
    make it more readable by adding paragraph breaks inside each block.
    """
    text = enhanced_transcript_text.strip()
    if text == "":
        return text

    speakers = _count_distinct_speakers(text)
    if len(speakers) > 1:
        return enhanced_transcript_text

    # Split into blocks separated by blank lines (Claude already uses this for multi-speaker).
    blocks = [b.strip() for b in re.split(r"\n\s*\n", text) if b.strip() != ""]
    if len(blocks) == 0:
        return enhanced_transcript_text

    processed_blocks: list[str] = []
    for block in blocks:
        # If this is a speaker-labeled line, keep the prefix and paragraphize the content.
        match = _SPEAKER_LINE_RE.match(block)
        if match is not None:
            speaker = (match.group("speaker") or "").strip()
            content = (match.group("text") or "").strip()
            content = _paragraphize_text(content)
            processed_blocks.append(f"{speaker}: {content}".strip())
            continue

        # Otherwise, paragraphize the whole block.
        processed_blocks.append(_paragraphize_text(block))

    return "\n\n".join([b for b in processed_blocks if b.strip() != ""]).strip()

