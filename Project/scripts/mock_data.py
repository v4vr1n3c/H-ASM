# Simple script to POST mock assets to the API for demo purposes.
import requests, os
API = os.getenv("API_URL", "http://localhost:8000")
data = {"hostname":"demo.hospital.local","ip":"10.0.0.10","asn":"AS0000","country":"BR","url":"http://demo.hospital.local"}
print(requests.post(f"{API}/api/v1/assets/mock", json=data).json())
