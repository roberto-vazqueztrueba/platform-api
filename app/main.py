import os
import time
import redis

from typing import Any
from fastapi import FastAPI, Response, HTTPException
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

APP_NAME = os.getenv("APP_NAME", "platform-api")
APP_VERSION = os.getenv("APP_VERSION", "dev")

REQUEST_COUNT = Counter(
  "http_requests_total",
  "Total de peticiones HTTP",
  ["method", "path", "status"],
)

REQUEST_LATENCY = Histogram(
  "http_request_duration_seconds",
  "Duración de las peticiones HTTP",
  ["method", "path"],
)

app = FastAPI(title=APP_NAME, version=APP_VERSION)

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

redis_client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        decode_responses=True,
)


@app.middleware("http")
async def metrics_middleware(request: Any, call_next: Any) -> Response:
  start = time.perf_counter()
  response = await call_next(request)
  elapsed = time.perf_counter() - start
  path = request.url.path
  REQUEST_COUNT.labels(request.method, path, str(response.status_code)).inc()
  REQUEST_LATENCY.labels(request.method, path).observe(elapsed)
  return response

@app.get("/")
def root() -> dict[str, str]:
  return {"app": APP_NAME, "version": APP_VERSION, "message": "hello platform"}

@app.get("/health/live")
def live() -> dict[str, str]:
  return {"status": "alive"}

@app.get("/health/ready")
def ready() -> dict[str, str]:
  # En una aplicación real aquí se comprobarían dependencias necesarias.
  return {"status": "ready"}

@app.get("/items")
def items() -> dict[str, list[dict[str, Any]]]:
  return {"items": [{"id": 1, "name": "docker"}, {"id": 2, "name": "kubernetes"}]}

@app.get("/metrics")
def metrics() -> Response:
  return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/cache/{key}")
def set_cache_value(key: str) -> dict[str, str | None]:
    value = redis_client.get(key)
    return  {"key": key, "value": value}

@app.put("/cache/{key}")
def set_cache_variable(key: str, value: str) -> dict[str, str]:
    redis_client.set(key, value)
    return {"key": key, "value": value}

