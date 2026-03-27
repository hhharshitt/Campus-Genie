"""
CampusGenie — Health Check Route
Returns liveness and dependency status for all services.
Used by docker-compose healthcheck and the frontend status page.
"""

import logging
import httpx
from fastapi import APIRouter
from app.models.schemas import HealthResponse
from app.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

SERVICES = {
    "ollama":   f"{settings.ollama_base_url}/api/tags",
    "chromadb": f"http://{settings.chroma_host}:{settings.chroma_port}/api/v1/heartbeat",
}


async def _ping(name: str, url: str) -> tuple[str, str]:
    """Ping a service and return (name, status)."""
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(url)
            status = "up" if r.status_code == 200 else "degraded"
    except httpx.ConnectError:
        status = "down"
    except Exception as exc:
        logger.warning(f"Health check failed for {name}: {exc}")
        status = "down"
    return name, status


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Check health of all CampusGenie services.
    Returns overall status: healthy | degraded | unhealthy
    """
    import asyncio
    results = await asyncio.gather(*[_ping(n, u) for n, u in SERVICES.items()])
    services = {name: status for name, status in results}
    services["backend"] = "up"

    if all(v == "up" for v in services.values()):
        overall = "healthy"
    elif any(v == "down" for v in services.values()):
        overall = "unhealthy"
    else:
        overall = "degraded"

    return HealthResponse(status=overall, services=services)
