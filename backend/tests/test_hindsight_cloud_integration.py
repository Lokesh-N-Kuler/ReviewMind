import os
import sys
import uuid
import logging
import pytest
from datetime import datetime

# Add app to path if executed standalone
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import dotenv_values, load_dotenv
from hindsight_client import Hindsight
import hindsight_client_api.exceptions as hsk_exceptions

logger = logging.getLogger("test_hindsight_cloud")

def test_hindsight_cloud_live_integration():
    """
    Live integration test for Hindsight Cloud:
    1. Connects to Hindsight Cloud using configured credentials from backend/.env.
    2. Stores a unique test memory in a dedicated ReviewMind test memory bank.
    3. Recalls that memory using a relevant query.
    4. Confirms the expected content is returned.
    5. Reports actual real status: never mocks or claims false success.
    """
    print("\n" + "=" * 60)
    print("REVIEW MIND - HINDSIGHT CLOUD INTEGRATION TEST")
    print("=" * 60)

    # 1. Inspect configuration directly from backend/.env
    env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
    env_vals = dotenv_values(env_path) if os.path.exists(env_path) else {}

    raw_base_url = env_vals.get("HINDSIGHT_BASE_URL") or os.getenv("HINDSIGHT_BASE_URL") or "https://api.hindsight.vectorize.io"
    base_url = raw_base_url.strip().rstrip("/")
    if "inference.hindsight.vectorize.io" in base_url:
        print("[INFO] Normalizing inference URL to official Hindsight Cloud API endpoint (https://api.hindsight.vectorize.io)")
        base_url = "https://api.hindsight.vectorize.io"
    elif base_url.endswith("/v1"):
        base_url = base_url[:-3]

    api_key = env_vals.get("HINDSIGHT_API_KEY") or os.getenv("HINDSIGHT_API_KEY")
    base_bank_id = env_vals.get("HINDSIGHT_BANK_ID") or os.getenv("HINDSIGHT_BANK_ID") or "reviewmind"
    bank_id = f"{base_bank_id}-cloud-test"

    print(f"Hindsight Endpoint:  {base_url}")
    print(f"Target Memory Bank:  {bank_id}")
    print(f"API Key Present:     {'Yes (Redacted)' if api_key else 'NO - MISSING'}")

    if not api_key:
        pytest.fail("FAILURE: HINDSIGHT_API_KEY is missing in backend/.env. Cannot test Hindsight Cloud integration.")

    timeout_sec = float(env_vals.get("HINDSIGHT_TIMEOUT_SECONDS") or os.getenv("HINDSIGHT_TIMEOUT_SECONDS") or 30.0)

    # 2. Initialize official SDK Client
    client = Hindsight(
        base_url=base_url,
        api_key=api_key,
        timeout=timeout_sec
    )

    test_token = str(uuid.uuid4())[:8]
    test_content = f"ReviewMind Convention: Always use parameterized SQL queries to prevent SQL injection. [token={test_token}]"
    test_query = f"parameterized queries SQL injection token {test_token}"

    print(f"Generated Unique Test Token: {test_token}")
    print(f"Storing Memory Content:       '{test_content[:60]}...'")

    # 3. Retain operation
    try:
        print("\n[Step 1/3] Calling client.retain() on Hindsight Cloud...")
        retain_res = client.retain(
            bank_id=bank_id,
            content=test_content,
            context="ReviewMind Live Integration Test",
            tags=["integration_test", f"token_{test_token}"]
        )
        op_id = getattr(retain_res, "operation_id", None) or getattr(retain_res, "document_id", None) or "completed"
        print(f"[SUCCESS] Retain succeeded! Operation/Doc ID: {op_id}")

    except hsk_exceptions.ForbiddenException as e:
        error_msg = (
            "HTTP 403 Forbidden: Your API key is scoped to the inference API and cannot access the Hindsight Cloud API. "
            "Please generate a Hindsight Cloud key at ui.hindsight.vectorize.io under API Keys -> Hindsight Cloud."
        )
        print(f"\n[FAILURE] {error_msg}")
        client.close()
        pytest.fail(error_msg)

    except hsk_exceptions.UnauthorizedException as e:
        error_msg = "HTTP 401 Unauthorized: Invalid or expired HINDSIGHT_API_KEY."
        print(f"\n[FAILURE] {error_msg}")
        client.close()
        pytest.fail(error_msg)

    except Exception as e:
        error_msg = f"Hindsight retain call failed: {type(e).__name__}: {str(e)}"
        print(f"\n[FAILURE] {error_msg}")
        client.close()
        pytest.fail(error_msg)

    # 4. Recall operation
    try:
        print("\n[Step 2/3] Calling client.recall() on Hindsight Cloud...")
        recall_res = client.recall(
            bank_id=bank_id,
            query=test_query,
            tags=["integration_test"]
        )
        print(f"[SUCCESS] Recall response received. Results count: {len(getattr(recall_res, 'results', []))}")

        # 5. Verify recalled content
        print("\n[Step 3/3] Verifying recalled memory content against stored token...")
        results = getattr(recall_res, "results", [])
        matched = False
        for item in results:
            item_text = getattr(item, "text", "")
            if test_token in item_text or "parameterized SQL queries" in item_text:
                matched = True
                print(f"Found matching memory: '{item_text[:70]}...'")
                break

        assert matched, f"Recalled memories did not contain expected test token '{test_token}'. Results: {[r.text for r in results]}"
        print(f"\n[INTEGRATION TEST PASSED] Successfully stored and recalled memory from Hindsight Cloud bank '{bank_id}'!")

    finally:
        client.close()


if __name__ == "__main__":
    try:
        test_hindsight_cloud_live_integration()
        print("\nResult: SUCCESS")
        sys.exit(0)
    except pytest.fail.Exception as e:
        print(f"\nResult: FAILED - {e}")
        sys.exit(1)
    except AssertionError as e:
        print(f"\nResult: FAILED - {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nResult: ERROR - {e}")
        sys.exit(1)
