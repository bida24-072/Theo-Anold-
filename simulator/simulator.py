"""
Simulated gate client. Drives the backend /access/check endpoint with
scripted scenarios so the whole flow is demonstrable without hardware.
Run with: docker compose --profile sim up
"""
import os, time, httpx

API = os.getenv("API_URL", "http://backend:8000")

SCENARIOS = [
    # (label, payload)
    ("Student entry — valid card + face", {
        "gate_id": 1, "credential_type": "card",
        "credential_token": "CARD-UID-001", "second_factor_token": "FACE-TEMPLATE-001",
    }),
    ("Student entry again (passback)", {
        "gate_id": 1, "credential_type": "card",
        "credential_token": "CARD-UID-001", "second_factor_token": "FACE-TEMPLATE-001",
    }),
    ("Student exit (single factor)", {
        "gate_id": 3, "credential_type": "card", "credential_token": "CARD-UID-001",
    }),
    ("Student entry — card only (missing 2nd factor)", {
        "gate_id": 1, "credential_type": "card", "credential_token": "CARD-UID-001",
    }),
    ("Student entry — unknown card", {
        "gate_id": 1, "credential_type": "card", "credential_token": "UNKNOWN-CARD",
    }),
    ("Vehicle entry — registered", {
        "gate_id": 4, "plate": "B123ABC",
    }),
    ("Vehicle entry — unregistered", {
        "gate_id": 4, "plate": "XYZ999",
    }),
]

def main():
    print("Waiting for backend...")
    for _ in range(30):
        try:
            httpx.get(f"{API}/health", timeout=1)
            break
        except Exception:
            time.sleep(1)

    print("Running scenarios...")
    for label, payload in SCENARIOS:
        try:
            r = httpx.post(f"{API}/access/check", json=payload, timeout=3)
            print(f"[{r.status_code}] {label} → {r.json().get('result')} ({r.json().get('reason')})")
        except Exception as e:
            print(f"[ERR] {label} → {e}")
        time.sleep(2)
    print("Simulator done.")

if __name__ == "__main__":
    main()
