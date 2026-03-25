import httpx
import json
import time

BASE_URL = 'http://127.0.0.1:8000/api/v1'

# Test 1: Create a document
print('=' * 60)
print('TEST 1: Creating test document')
print('=' * 60)
create_response = httpx.post(
    f'{BASE_URL}/documents',
    json={
        'filename': 'test_invoice.txt',
        'content_type': 'text/plain',
        'storage_path': '/uploads/test_invoice.txt',
        'extracted_text': 'Invoice #INV-2024-001. We hereby invoice you for services rendered. Total due: $500.00. Please pay within 30 days.'
    }
)
print(f'Status: {create_response.status_code}')
if create_response.status_code in [200, 201]:
    doc_data = create_response.json()
    doc_id = doc_data.get('data', {}).get('id')
    print(f'SUCCESS: Created document ID: {doc_id}')
else:
    print(f'FAILED: {create_response.text}')
    exit(1)

print()

# Test 2: Classify document
print('=' * 60)
print('TEST 2: Classifying document')
print('=' * 60)
classify_response = httpx.post(
    f'{BASE_URL}/ai/documents/{doc_id}/classify',
    json={}
)
print(f'Status: {classify_response.status_code}')
if classify_response.status_code == 200:
    classify_data = classify_response.json()
    result = classify_data.get('data', {})
    print(f'SUCCESS:')
    print(f'  Document Type: {result.get("document_type")}')
    print(f'  Confidence: {result.get("confidence")}')
    print(f'  Reasoning: {result.get("reasoning")}')
else:
    print(f'FAILED: {classify_response.text}')
    exit(1)

print()

# Test 3: Ask document
print('=' * 60)
print('TEST 3: Asking document a question')
print('=' * 60)
ask_response = httpx.post(
    f'{BASE_URL}/ai/documents/{doc_id}/ask',
    json={'question': 'What is the total amount due?'}
)
print(f'Status: {ask_response.status_code}')
if ask_response.status_code == 200:
    ask_data = ask_response.json()
    result = ask_data.get('data', {})
    print(f'SUCCESS:')
    print(f'  Answer: {result.get("answer")}')
    print(f'  Confidence: {result.get("confidence")}')
    print(f'  Sources Used: {result.get("context_chunks_used", 0)}')
else:
    print(f'FAILED: {ask_response.text}')
    exit(1)

print()

# Test 4: Verify document was updated
print('=' * 60)
print('TEST 4: Verifying document updates in database')
print('=' * 60)
get_response = httpx.get(f'{BASE_URL}/documents/{doc_id}')
if get_response.status_code == 200:
    doc = get_response.json().get('data', {})
    print(f'SUCCESS:')
    print(f'  Document Type: {doc.get("document_type")}')
    print(f'  Processing Status: {doc.get("processing_status")}')
    print(f'  Title: {doc.get("filename")}')
else:
    print(f'FAILED: {get_response.text}')
    exit(1)

print()
print('=' * 60)
print('ALL SMOKE TESTS PASSED')
print('=' * 60)
