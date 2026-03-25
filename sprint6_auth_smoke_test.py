import time
import uuid

import httpx

BASE_URL = "http://127.0.0.1:8000/api/v1"


def assert_status(response: httpx.Response, expected: int, label: str) -> None:
    if response.status_code != expected:
        raise RuntimeError(f"{label} failed: expected {expected}, got {response.status_code}, body={response.text}")


def register_user(email: str, full_name: str, password: str) -> str:
    response = httpx.post(
        f"{BASE_URL}/auth/register",
        json={"email": email, "full_name": full_name, "password": password},
        timeout=30.0,
    )
    assert_status(response, 201, "register")
    return response.json()["data"]["token"]["access_token"]


print("=" * 60)
print("SPRINT 6 AUTH SMOKE TEST")
print("=" * 60)

time.sleep(1)

print("1) Unauthenticated documents list should be rejected")
unauth_list = httpx.get(f"{BASE_URL}/documents", timeout=30.0)
assert_status(unauth_list, 401, "unauthenticated documents list")
print("   OK")

print("2) Register user #1 and fetch profile")
email_1 = f"user1-{uuid.uuid4().hex[:8]}@example.com"
password = "StrongPass123"
token_1 = register_user(email_1, "User One", password)

me_1 = httpx.get(
    f"{BASE_URL}/auth/me",
    headers={"Authorization": f"Bearer {token_1}"},
    timeout=30.0,
)
assert_status(me_1, 200, "auth me")
print("   OK")

print("3) User #1 creates one document")
create_doc = httpx.post(
    f"{BASE_URL}/documents",
    headers={"Authorization": f"Bearer {token_1}"},
    json={
        "filename": "auth-test-doc.txt",
        "content_type": "text/plain",
        "storage_path": "/uploads/auth-test-doc.txt",
        "extracted_text": "Invoice amount due is 250 dollars.",
    },
    timeout=30.0,
)
assert_status(create_doc, 201, "create document")
print("   OK")

print("4) User #1 lists documents and sees at least one own record")
list_1 = httpx.get(
    f"{BASE_URL}/documents",
    headers={"Authorization": f"Bearer {token_1}"},
    timeout=30.0,
)
assert_status(list_1, 200, "list documents user #1")
user1_docs = list_1.json()["data"]
if len(user1_docs) < 1:
    raise RuntimeError("user #1 should see at least one document")
print(f"   OK (count={len(user1_docs)})")

print("5) Register user #2 and verify isolation")
email_2 = f"user2-{uuid.uuid4().hex[:8]}@example.com"
token_2 = register_user(email_2, "User Two", password)
list_2 = httpx.get(
    f"{BASE_URL}/documents",
    headers={"Authorization": f"Bearer {token_2}"},
    timeout=30.0,
)
assert_status(list_2, 200, "list documents user #2")
user2_docs = list_2.json()["data"]
if len(user2_docs) != 0:
    raise RuntimeError(f"user #2 should see 0 documents, saw {len(user2_docs)}")
print("   OK")

print("=" * 60)
print("ALL SPRINT 6 AUTH TESTS PASSED")
print("=" * 60)
