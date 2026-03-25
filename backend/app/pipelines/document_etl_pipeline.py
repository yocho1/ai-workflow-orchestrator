from pathlib import Path

from app.models.document import Document


class DocumentEtlPipeline:
    def extract(self, document: Document) -> str:
        path = Path(document.storage_path)
        if path.exists() and path.is_file():
            content = path.read_text(encoding="utf-8", errors="ignore")
            return content

        return document.extracted_text or ""

    def transform(self, text: str) -> tuple[str, str | None]:
        normalized = " ".join(text.split())
        lowered = normalized.lower()

        inferred_type = None
        if "invoice" in lowered:
            inferred_type = "invoice"
        elif "contract" in lowered:
            inferred_type = "contract"
        elif "receipt" in lowered:
            inferred_type = "receipt"

        return normalized, inferred_type

    def load(self, document: Document, *, normalized_text: str, inferred_type: str | None) -> None:
        document.extracted_text = normalized_text if normalized_text else document.extracted_text
        if inferred_type and not document.document_type:
            document.document_type = inferred_type
        document.processing_status = "processed"
