import csv
import io
import uuid

import httpx

BASE_URL = "http://127.0.0.1:8000/api/v1"
PASSWORD = "StrongPass123"


def assert_status(response: httpx.Response, expected: int, label: str) -> None:
    if response.status_code != expected:
        raise RuntimeError(
            f"{label} failed: expected {expected}, got {response.status_code}, body={response.text}"
        )


def register_user(email: str, full_name: str) -> str:
    response = httpx.post(
        f"{BASE_URL}/auth/register",
        json={"email": email, "full_name": full_name, "password": PASSWORD},
        timeout=30.0,
    )
    assert_status(response, 201, "register")
    return response.json()["data"]["token"]["access_token"]


def main() -> None:
    print("=" * 60)
    print("SPRINT 7 QA SMOKE TEST")
    print("=" * 60)

    print("1) Unauthenticated documents list should be rejected")
    unauth_list = httpx.get(f"{BASE_URL}/documents", timeout=30.0)
    assert_status(unauth_list, 401, "unauthenticated documents list")
    print("   OK")

    print("2) Register user and check profile")
    email = f"qa-{uuid.uuid4().hex[:8]}@example.com"
    token = register_user(email, "QA User")

    me = httpx.get(
        f"{BASE_URL}/auth/me",
        headers={"Authorization": f"Bearer {token}"},
        timeout=30.0,
    )
    assert_status(me, 200, "auth me")
    print("   OK")

    print("3) Create two documents")
    headers = {"Authorization": f"Bearer {token}"}
    created_ids: list[int] = []
    for idx in range(1, 3):
        create_doc = httpx.post(
            f"{BASE_URL}/documents",
            headers=headers,
            json={
                "filename": f"qa-doc-{idx}.txt",
                "content_type": "text/plain",
                "storage_path": f"/uploads/qa-doc-{idx}.txt",
                "extracted_text": f"QA test document #{idx}.",
            },
            timeout=30.0,
        )
        assert_status(create_doc, 201, f"create document #{idx}")
        created_ids.append(create_doc.json()["data"]["id"])
    print(f"   OK (ids={created_ids})")

    print("4) List documents for current user")
    list_docs = httpx.get(
        f"{BASE_URL}/documents",
        headers=headers,
        timeout=30.0,
    )
    assert_status(list_docs, 200, "list documents")
    docs = list_docs.json()["data"]
    doc_ids = {doc["id"] for doc in docs}
    if not set(created_ids).issubset(doc_ids):
        raise RuntimeError("list documents failed: created docs are missing")
    print(f"   OK (count={len(docs)})")

    print("5) Review queue endpoint responds")
    queue = httpx.get(
        f"{BASE_URL}/documents/metadata/review-queue",
        headers=headers,
        timeout=30.0,
    )
    assert_status(queue, 200, "review queue")
    if not isinstance(queue.json().get("data"), list):
        raise RuntimeError("review queue failed: data is not a list")
    print("   OK")

    print("6) CSV export responds and includes created docs")
    csv_resp = httpx.get(
        f"{BASE_URL}/documents/metadata/export/csv",
        headers=headers,
        timeout=30.0,
    )
    assert_status(csv_resp, 200, "csv export")
    if "text/csv" not in csv_resp.headers.get("content-type", ""):
        raise RuntimeError("csv export failed: invalid content-type")
    csv_text = csv_resp.content.decode("utf-8-sig")
    rows = list(csv.DictReader(io.StringIO(csv_text)))
    rows_by_id = {int(row["document_id"]): row for row in rows if row.get("document_id")}
    for doc_id in created_ids:
        if doc_id not in rows_by_id:
            raise RuntimeError(f"csv export failed: document {doc_id} missing")
    print("   OK")

    print("7) PDF export responds with PDF signature")
    pdf_resp = httpx.get(
        f"{BASE_URL}/documents/metadata/export/pdf",
        headers=headers,
        timeout=30.0,
    )
    assert_status(pdf_resp, 200, "pdf export")
    if "application/pdf" not in pdf_resp.headers.get("content-type", ""):
        raise RuntimeError("pdf export failed: invalid content-type")
    if not pdf_resp.content.startswith(b"%PDF"):
        raise RuntimeError("pdf export failed: response is not a PDF")
    print("   OK")

    print("8) CSV export filter by document_type=invoice returns only header (no extracted metadata yet)")
    csv_filtered = httpx.get(
        f"{BASE_URL}/documents/metadata/export/csv",
        headers=headers,
        params={"document_type": "invoice"},
        timeout=30.0,
    )
    assert_status(csv_filtered, 200, "csv export filtered")
    filtered_text = csv_filtered.content.decode("utf-8-sig")
    filtered_rows = list(csv.DictReader(io.StringIO(filtered_text)))
    if len(filtered_rows) != 0:
        raise RuntimeError(
            f"csv filtered export failed: expected 0 rows for invoice filter, got {len(filtered_rows)}"
        )
    print("   OK")

    print("=" * 60)
    print("ALL SPRINT 7 QA SMOKE TESTS PASSED")
    print("=" * 60)


if __name__ == "__main__":
    main()
