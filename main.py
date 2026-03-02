#!/usr/bin/env python3
"""
Embedding API Service — 独立的嵌入向量服务
兼容 OpenAI /v1/embeddings 接口，使用 sentence-transformers 本地模型
"""

__version__ = "1.0.0"

import os
import logging
from typing import Union

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ========== 配置 ==========
HOST = os.environ.get("EMBED_HOST", "0.0.0.0")
PORT = int(os.environ.get("EMBED_PORT", "8786"))
MODEL_NAME = os.environ.get("EMBED_MODEL", "all-MiniLM-L6-v2")
LOG_LEVEL = os.environ.get("EMBED_LOG_LEVEL", "INFO")

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger("embed-api")

app = FastAPI(
    title="Embedding API",
    version=__version__,
    description="OpenAI-compatible embedding endpoint powered by sentence-transformers",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== 模型懒加载 ==========
_embedding_model = None


def _get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        logger.info(f"Loading embedding model: {MODEL_NAME}")
        from sentence_transformers import SentenceTransformer
        _embedding_model = SentenceTransformer(MODEL_NAME)
        logger.info(f"Embedding model loaded: {MODEL_NAME}")
    return _embedding_model


# ========== 请求/响应模型 ==========
class EmbeddingRequest(BaseModel):
    input: Union[str, list[str]]
    model: str = "all-MiniLM-L6-v2"
    encoding_format: str = "float"


# ========== 路由 ==========
@app.get("/health")
async def health():
    return {"status": "ok", "version": __version__, "model": MODEL_NAME}


@app.get("/v1/models")
async def list_models():
    return {
        "object": "list",
        "data": [
            {
                "id": MODEL_NAME,
                "object": "model",
                "owned_by": "local",
                "permission": [],
            }
        ],
    }


@app.post("/v1/embeddings")
async def create_embeddings(request: EmbeddingRequest):
    model = _get_embedding_model()
    texts = request.input if isinstance(request.input, list) else [request.input]
    embeddings = model.encode(texts, normalize_embeddings=True)
    data = []
    total_tokens = 0
    for i, (text, emb) in enumerate(zip(texts, embeddings)):
        data.append({
            "object": "embedding",
            "index": i,
            "embedding": emb.tolist(),
        })
        total_tokens += len(text.split())
    return {
        "object": "list",
        "data": data,
        "model": MODEL_NAME,
        "usage": {"prompt_tokens": total_tokens, "total_tokens": total_tokens},
    }


# ========== 入口 ==========
if __name__ == "__main__":
    import uvicorn
    logger.info(f"Starting Embedding API on {HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT, log_level=LOG_LEVEL.lower())
