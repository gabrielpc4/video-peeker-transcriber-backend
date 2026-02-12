import time
from dataclasses import dataclass

import requests


@dataclass(frozen=True)
class AssemblyAiTranscriptResult:
    transcript_text: str
    detected_language_code: str | None


class AssemblyAiClient:
    def __init__(self, api_key: str) -> None:
        self._api_key = api_key

    def _headers(self) -> dict[str, str]:
        return {"authorization": self._api_key}

    def upload_file(self, file_path: str) -> str:
        url = "https://api.assemblyai.com/v2/upload"

        with open(file_path, "rb") as file_handle:
            response = requests.post(url, headers=self._headers(), data=file_handle)

        if response.ok is False:
            raise RuntimeError(f"AssemblyAI upload failed: HTTP {response.status_code}\n\n{response.text}")

        upload_url = response.json().get("upload_url")
        if isinstance(upload_url, str) is False or upload_url.strip() == "":
            raise RuntimeError("AssemblyAI upload did not return upload_url.")

        return upload_url

    def create_transcript(self, upload_url: str) -> str:
        url = "https://api.assemblyai.com/v2/transcript"

        trimmed_upload_url = upload_url.strip()
        if trimmed_upload_url.startswith("http://") is False and trimmed_upload_url.startswith("https://") is False:
            raise RuntimeError(f"AssemblyAI audio_url is not a valid URL: {trimmed_upload_url}")

        payload: dict = {
            # Why: keep request minimal and compatible; language detection is default when
            # language_code is not provided.
            "audio_url": trimmed_upload_url,
        }

        response = requests.post(url, headers={**self._headers(), "content-type": "application/json"}, json=payload)
        if response.ok is False:
            raise RuntimeError(
                "AssemblyAI create transcript failed.\n\n"
                f"HTTP {response.status_code}\n\n"
                f"audio_url: {trimmed_upload_url}\n\n"
                f"{response.text}"
            )

        transcript_id = response.json().get("id")
        if isinstance(transcript_id, str) is False or transcript_id.strip() == "":
            raise RuntimeError("AssemblyAI create transcript did not return id.")

        return transcript_id

    def poll_transcript(self, transcript_id: str, timeout_seconds: int = 1200) -> AssemblyAiTranscriptResult:
        url = f"https://api.assemblyai.com/v2/transcript/{transcript_id}"

        started_at = time.time()

        while True:
            if time.time() - started_at > timeout_seconds:
                raise RuntimeError("AssemblyAI transcription timed out.")

            response = requests.get(url, headers=self._headers())
            if response.ok is False:
                raise RuntimeError(f"AssemblyAI get transcript failed: HTTP {response.status_code}\n\n{response.text}")

            payload = response.json()
            status = payload.get("status")

            if status == "completed":
                transcript_text = payload.get("text") or ""
                detected_language_code = payload.get("language_code")

                transcript_text = str(transcript_text).strip()
                if transcript_text == "":
                    raise RuntimeError("AssemblyAI completed but text is empty.")

                language_value = None
                if isinstance(detected_language_code, str) and detected_language_code.strip() != "":
                    language_value = detected_language_code.strip()

                return AssemblyAiTranscriptResult(
                    transcript_text=transcript_text,
                    detected_language_code=language_value,
                )

            if status == "error":
                error_message = payload.get("error") or "Unknown error"
                raise RuntimeError(f"AssemblyAI transcription failed: {error_message}")

            time.sleep(1.0)

