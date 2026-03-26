from enum import Enum


class DocumentStatus(str, Enum):
    """Document lifecycle status enumeration.
    
    States:
    - uploaded: Document has been uploaded but not yet processed
    - processing: Document is being processed (extracting text, classification, etc.)
    - classified: Document has been classified (AI has determined its type)
    - completed: Document processing is complete and ready for use
    - failed: Document processing failed and cannot be recovered
    """

    UPLOADED = "uploaded"
    PROCESSING = "processing"
    CLASSIFIED = "classified"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentType(str, Enum):
    """Document type classification.
    
    Types:
    - invoice: Sales invoice or purchase invoice
    - contract: Legal or business contract
    - receipt: Purchase receipt or transaction record
    - report: Business report or financial document
    - other: Unclassified or miscellaneous document
    """

    INVOICE = "invoice"
    CONTRACT = "contract"
    RECEIPT = "receipt"
    REPORT = "report"
    OTHER = "other"


# Valid status transitions (state machine)
# Format: current_status -> list of allowed next statuses
VALID_STATUS_TRANSITIONS = {
    DocumentStatus.UPLOADED: [DocumentStatus.PROCESSING, DocumentStatus.FAILED],
    DocumentStatus.PROCESSING: [DocumentStatus.CLASSIFIED, DocumentStatus.FAILED],
    DocumentStatus.CLASSIFIED: [DocumentStatus.COMPLETED, DocumentStatus.FAILED],
    DocumentStatus.COMPLETED: [DocumentStatus.PROCESSING],  # Allow reprocessing
    DocumentStatus.FAILED: [DocumentStatus.PROCESSING],  # Allow retry
}
