import os
from google.cloud import kms_v1

PROJECT_ID = os.environ.get("PROJECT_ID", "vitaproof-gateway")
LOCATION = "us-central1"
KEYRING = "vitaproof-keyring"
KEY_NAME = "solana-anchor-key"
KEY_VERSION = "1"

client = kms_v1.KeyManagementServiceClient()
key_version_path = client.crypto_key_version_path(
    PROJECT_ID, LOCATION, KEYRING, KEY_NAME, KEY_VERSION
)

def sign_state_hash(state_hash: str) -> bytes:
    data = state_hash.encode("utf-8")
    
    response = client.asymmetric_sign(
        request={
            "name": key_version_path,
            "data": data,
        }
    )
    return response.signature

if __name__ == "__main__":
    sample_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    sig = sign_state_hash(sample_hash)
    print("====================================================")
    print("         GCP KMS ED25519 HARDWARE SIGNATURE          ")
    print("====================================================")
    print(f"Payload Hash: {sample_hash}")
    print(f"Signature Len: {len(sig)} bytes")
    print(f"Hex Signature: {sig.hex()[:64]}...")
    print("====================================================")
