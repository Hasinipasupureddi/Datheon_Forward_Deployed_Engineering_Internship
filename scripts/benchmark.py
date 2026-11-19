"""Measure local API health and grounded-query latency without exposing passwords."""

import getpass
import os
import time
import statistics
import requests

BASE_URL = "http://127.0.0.1:8000"
USERNAME = input("Enter your login username: ")
PASSWORD = getpass.getpass("Enter your login password: ")

session = requests.Session()

# Login
login_response = session.post(
    f"{BASE_URL}/login",
    json={"username": USERNAME, "password": PASSWORD},
    timeout=30,
)
login_response.raise_for_status()

token = login_response.json()["access_token"]
session.headers.update({"Authorization": f"Bearer {token}"})

# Health benchmark
health_times = []

for i in range(10):
    start = time.perf_counter()
    response = session.get(f"{BASE_URL}/health", timeout=30)
    elapsed = (time.perf_counter() - start) * 1000
    response.raise_for_status()
    health_times.append(elapsed)

# Query benchmark
query_times = []
success_count = 0

question = input("Enter a question from your ingested PDF: ")

for i in range(3):
    start = time.perf_counter()
    response = session.post(
        f"{BASE_URL}/query",
        json={"query": question},
        timeout=180,
    )
    elapsed = (time.perf_counter() - start) * 1000
    query_times.append(elapsed)

    if response.ok and response.json().get("abstained") is False:
        success_count += 1

def report(name, values):
    print(f"\n{name}")
    print(f"Requests: {len(values)}")
    print(f"Average: {statistics.mean(values):.2f} ms")
    print(f"Minimum: {min(values):.2f} ms")
    print(f"Maximum: {max(values):.2f} ms")

report("HEALTH ENDPOINT", health_times)
report("RAG QUERY ENDPOINT", query_times)

print(f"\nSuccessful grounded queries: {success_count}/{len(query_times)}")

