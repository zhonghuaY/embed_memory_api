#!/usr/bin/env python3
"""
Embedding API 测试用例
启动服务后运行: python3 test_api.py
或直接运行（自动启动服务）: python3 test_api.py --auto
"""

import sys
import time
import subprocess
import signal
import httpx
import numpy as np

BASE_URL = "http://127.0.0.1:8786"
PASS = 0
FAIL = 0


def report(name: str, ok: bool, detail: str = ""):
    global PASS, FAIL
    tag = "PASS" if ok else "FAIL"
    if ok:
        PASS += 1
    else:
        FAIL += 1
    suffix = f" — {detail}" if detail else ""
    print(f"  [{tag}] {name}{suffix}")


def test_health(client: httpx.Client):
    print("\n== Test: Health Check ==")
    r = client.get(f"{BASE_URL}/health")
    report("status 200", r.status_code == 200)
    data = r.json()
    report("status=ok", data.get("status") == "ok")
    report("has version", "version" in data)
    report("has model", "model" in data)


def test_models(client: httpx.Client):
    print("\n== Test: List Models ==")
    r = client.get(f"{BASE_URL}/v1/models")
    report("status 200", r.status_code == 200)
    data = r.json()
    report("object=list", data.get("object") == "list")
    report("has data", len(data.get("data", [])) > 0)
    report("model has id", "id" in data["data"][0])


def test_single_embedding(client: httpx.Client):
    print("\n== Test: Single Text Embedding ==")
    r = client.post(f"{BASE_URL}/v1/embeddings", json={
        "input": "Hello, world!",
        "model": "all-MiniLM-L6-v2",
    })
    report("status 200", r.status_code == 200)
    data = r.json()
    report("object=list", data.get("object") == "list")
    report("1 embedding returned", len(data.get("data", [])) == 1)

    emb = data["data"][0]
    report("object=embedding", emb.get("object") == "embedding")
    report("index=0", emb.get("index") == 0)
    report("embedding is list", isinstance(emb.get("embedding"), list))
    report("embedding dim=384", len(emb.get("embedding", [])) == 384,
           f"got {len(emb.get('embedding', []))}")

    vec = np.array(emb["embedding"])
    norm = float(np.linalg.norm(vec))
    report("normalized (norm≈1.0)", abs(norm - 1.0) < 0.01, f"norm={norm:.6f}")

    usage = data.get("usage", {})
    report("has prompt_tokens", usage.get("prompt_tokens", 0) > 0)
    report("has model field", "model" in data)


def test_batch_embedding(client: httpx.Client):
    print("\n== Test: Batch Embedding ==")
    texts = ["apple", "banana", "cherry"]
    r = client.post(f"{BASE_URL}/v1/embeddings", json={
        "input": texts,
        "model": "all-MiniLM-L6-v2",
    })
    report("status 200", r.status_code == 200)
    data = r.json()
    report("3 embeddings returned", len(data.get("data", [])) == 3)

    for i, item in enumerate(data.get("data", [])):
        report(f"item[{i}].index={i}", item.get("index") == i)

    vecs = [np.array(d["embedding"]) for d in data["data"]]
    for i, v in enumerate(vecs):
        norm = float(np.linalg.norm(v))
        report(f"item[{i}] normalized", abs(norm - 1.0) < 0.01)


def test_semantic_similarity(client: httpx.Client):
    print("\n== Test: Semantic Similarity ==")
    texts = ["I love dogs", "I adore puppies", "The weather is sunny"]
    r = client.post(f"{BASE_URL}/v1/embeddings", json={"input": texts})
    data = r.json()
    vecs = [np.array(d["embedding"]) for d in data["data"]]

    sim_close = float(np.dot(vecs[0], vecs[1]))
    sim_far = float(np.dot(vecs[0], vecs[2]))
    report("similar texts have higher cosine",
           sim_close > sim_far,
           f"sim('dogs','puppies')={sim_close:.4f} > sim('dogs','weather')={sim_far:.4f}")


def test_empty_input(client: httpx.Client):
    print("\n== Test: Empty String Input ==")
    r = client.post(f"{BASE_URL}/v1/embeddings", json={"input": ""})
    report("status 200", r.status_code == 200)
    data = r.json()
    report("1 embedding returned", len(data.get("data", [])) == 1)


def test_long_text(client: httpx.Client):
    print("\n== Test: Long Text Input ==")
    long_text = "embedding test " * 200
    r = client.post(f"{BASE_URL}/v1/embeddings", json={"input": long_text})
    report("status 200", r.status_code == 200)
    data = r.json()
    report("1 embedding returned", len(data.get("data", [])) == 1)
    report("embedding dim=384", len(data["data"][0].get("embedding", [])) == 384)


def test_invalid_request(client: httpx.Client):
    print("\n== Test: Invalid Request (missing input) ==")
    r = client.post(f"{BASE_URL}/v1/embeddings", json={})
    report("status 422 (validation error)", r.status_code == 422)


def wait_for_server(client: httpx.Client, timeout: int = 30):
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = client.get(f"{BASE_URL}/health", timeout=2)
            if r.status_code == 200:
                return True
        except Exception:
            pass
        time.sleep(0.5)
    return False


def main():
    auto = "--auto" in sys.argv
    proc = None

    if auto:
        print("Starting server automatically...")
        proc = subprocess.Popen(
            [sys.executable, "main.py"],
            cwd="/home/albert/Downloads/embed_memory_api",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

    client = httpx.Client(timeout=60)

    try:
        if auto:
            print("Waiting for server to be ready...")
            if not wait_for_server(client):
                print("ERROR: Server failed to start within 30s")
                sys.exit(1)
        else:
            try:
                client.get(f"{BASE_URL}/health", timeout=3)
            except Exception:
                print(f"ERROR: Server not running at {BASE_URL}")
                print("Start it with: python3 main.py")
                print("Or run: python3 test_api.py --auto")
                sys.exit(1)

        print(f"\n{'='*50}")
        print(f"  Embedding API Test Suite")
        print(f"{'='*50}")

        test_health(client)
        test_models(client)
        test_single_embedding(client)
        test_batch_embedding(client)
        test_semantic_similarity(client)
        test_empty_input(client)
        test_long_text(client)
        test_invalid_request(client)

        print(f"\n{'='*50}")
        print(f"  Results: {PASS} passed, {FAIL} failed")
        print(f"{'='*50}\n")

        sys.exit(0 if FAIL == 0 else 1)

    finally:
        client.close()
        if proc:
            proc.send_signal(signal.SIGTERM)
            proc.wait(timeout=5)


if __name__ == "__main__":
    main()
