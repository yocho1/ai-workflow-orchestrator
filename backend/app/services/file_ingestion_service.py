import io
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
            return content.decode("utf-8", errors="ignore").strip()

        reader = PdfReader(io.BytesIO(content))
        pages: list[str] = []
        for page in reader.pages:
            pages.append(page.extract_text() or "")
        return "\n\n".join(pages).strip()
