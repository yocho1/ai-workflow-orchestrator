import io
import re
from pathlib import Path
from uuid import uuid4

from pypdf import PdfReader  # type: ignore[import-not-found]

from app.core.config import get_settings


class FileIngestionService:
    _text_extensions = {"txt", "md", "csv", "json"}
    _all_extensions = _text_extensions | {"pdf"}

    def __init__(self) -> None:
        self.settings = get_settings()

    def ingest(self, *, original_filename: str, content: bytes) -> tuple[str, str]:
        extension = self._extract_extension(original_filename)
        if extension not in self._all_extensions:
            raise ValueError("Unsupported file format. Allowed: .txt, .md, .csv, .json, .pdf")

        upload_path = self._persist_file(original_filename=original_filename, content=content)
        extracted_text = self._extract_text(extension=extension, content=content)
        return str(upload_path), extracted_text

    def extract_from_path(self, *, storage_path: str, original_filename: str) -> str:
        path = Path(storage_path)
        if not path.exists() or not path.is_file():
            raise ValueError("Stored file not found for text extraction")

        extension = self._extract_extension(original_filename)
        if extension not in self._all_extensions:
            raise ValueError("Unsupported file format. Allowed: .txt, .md, .csv, .json, .pdf")

        content = path.read_bytes()
        return self._extract_text(extension=extension, content=content)

    def normalize_text(self, text: str) -> str:
        return self._normalize_extracted_text(text)

    def _extract_extension(self, filename: str) -> str:
        parts = filename.rsplit(".", 1)
        if len(parts) != 2:
            return ""
        return parts[1].lower().strip()

    def _persist_file(self, *, original_filename: str, content: bytes) -> Path:
        upload_dir = Path(self.settings.upload_dir)
        upload_dir.mkdir(parents=True, exist_ok=True)

        safe_name = original_filename.replace(" ", "_")
        target = upload_dir / f"{uuid4().hex}_{safe_name}"
        target.write_bytes(content)
        return target

    def _extract_text(self, *, extension: str, content: bytes) -> str:
        if extension in self._text_extensions:
            text = content.decode("utf-8", errors="ignore")
            return self._normalize_extracted_text(text)

        reader = PdfReader(io.BytesIO(content))
        pages: list[str] = []
        for page in reader.pages:
            pages.append(page.extract_text() or "")
        text = "\n\n".join(pages)
        return self._normalize_extracted_text(text)

    def _normalize_extracted_text(self, text: str) -> str:
        if not text:
            return ""

        text = text.replace("\xa0", " ")
        normalized_lines: list[str] = []

        for raw_line in text.splitlines():
            line = raw_line.strip()
            if not line:
                continue

            # Keep coarse word boundaries (2+ spaces), while collapsing char-spaced segments.
            segments = re.split(r"\s{2,}", line)
            rebuilt_segments: list[str] = []
            for segment in segments:
                segment = segment.strip()
                if not segment:
                    continue

                tokens = segment.split()
                alnum_tokens = [tok for tok in tokens if any(ch.isalnum() for ch in tok)]
                single_char_tokens = [tok for tok in alnum_tokens if len(tok) == 1]

                if alnum_tokens and (len(single_char_tokens) / len(alnum_tokens)) >= 0.6:
                    compact = re.sub(r"(?<=\b\w)\s+(?=\w\b)", "", segment)
                    compact = re.sub(r"\s+([,.:;!?])", r"\1", compact)
                    compact = re.sub(r"([,.:;!?])(?=\w)", r"\1 ", compact)
                    rebuilt_segments.append(compact)
                else:
                    rebuilt_segments.append(" ".join(tokens))

            if rebuilt_segments:
                normalized_lines.append(" ".join(rebuilt_segments))

        normalized = "\n".join(normalized_lines)
        return normalized.strip()
