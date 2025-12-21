"""LLM inference endpoints with Kolibri AI integration."""
from __future__ import annotations

import hashlib
import json
import logging
import time
from typing import Any, AsyncGenerator, Dict, Iterable, List

import httpx
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, status
from fastapi.responses import StreamingResponse
from pydantic import ValidationError

from ..ai_core import KolibriAICore
from ..generative_ai import GenerativeDecimalAI
from ..audit import log_audit_event, log_genome_event
from ..config import Settings, get_settings
from ..instrumentation import INFER_LATENCY, INFER_REQUESTS
from ..scheduler import EnergyAwareScheduler
from ..schemas import InferenceRequest, InferenceResponse, ModerationDiagnostics
from .._compat import safe_model_dump
from ..moderation import (
    enforce_prompt_policy,
    moderate_response,
    ModerationError,
)
from ..security import AuthContext, get_rbac_policy, require_permission, verify_session_token, get_current_identity

__all__ = ["router"]

router = APIRouter()
LOGGER = logging.getLogger(__name__)

# Global instances
_scheduler = EnergyAwareScheduler(
    device_power_budget_j=10.0,
    default_latency_slo_ms=1000.0,
    local_runner_available=False,
    upstream_available=False,
)

_ai_core = KolibriAICore(
    secret_key="kolibri-prod-secret",
    enable_llm=False,  # Will be enabled if LLM endpoint configured
    llm_endpoint=None,
)

# NEW: Generative Decimal AI (самообучающаяся система)
_generative_ai = GenerativeDecimalAI(
    secret_key="kolibri-generative-prod",
    pool_size=24  # 24 эволюционирующие формулы
)


def _extract_text(payload: Any) -> str:
    if isinstance(payload, dict):
        if isinstance(payload.get("response"), str):
            return payload["response"].strip()

        choices = payload.get("choices")
        if isinstance(choices, list) and choices:
            first_choice = choices[0]
            if isinstance(first_choice, dict):
                message = first_choice.get("message")
                if isinstance(message, dict) and isinstance(message.get("content"), str):
                    return message["content"].strip()
                if isinstance(first_choice.get("text"), str):
                    return first_choice["text"].strip()

        if isinstance(payload.get("content"), str):
            return payload["content"].strip()

    raise ValueError("Upstream response did not contain text output")


async def _perform_upstream_call(
    request: InferenceRequest,
    settings: Settings,
) -> tuple[str, float, str]:
    if not settings.llm_endpoint:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM endpoint is not configured",
        )

    headers: Dict[str, str] = {"Content-Type": "application/json"}
    if settings.llm_api_key:
        headers["Authorization"] = f"Bearer {settings.llm_api_key}"

    temperature = request.temperature
    if temperature is None:
        temperature = settings.llm_temperature_default

    max_tokens = request.max_tokens
    if max_tokens is None:
        max_tokens = settings.llm_max_tokens_default

    payload: Dict[str, Any] = {
        "prompt": request.prompt,
        "mode": request.mode,
        "model": settings.llm_model,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    sanitized_payload = {key: value for key, value in payload.items() if value is not None}

    start = time.perf_counter()
    async with httpx.AsyncClient(timeout=settings.llm_timeout) as client:
        upstream_response = await client.post(
            settings.llm_endpoint,
            json=sanitized_payload,
            headers=headers,
        )
    elapsed = (time.perf_counter() - start) * 1000.0

    try:
        upstream_response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Upstream LLM returned {exc.response.status_code}: {detail}",
        ) from exc

    try:
        payload_json = upstream_response.json()
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Upstream LLM responded with invalid JSON",
        ) from exc

    try:
        text = _extract_text(payload_json)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    provider = "llm"
    if isinstance(payload_json, dict) and isinstance(payload_json.get("provider"), str):
        provider = payload_json["provider"].strip() or provider

    return text, elapsed, provider


def _token_chunks(text: str, *, chunk_size: int = 32) -> Iterable[str]:
    buffer: list[str] = []
    for char in text:
        buffer.append(char)
        if len(buffer) >= chunk_size and char.isspace():
            yield "".join(buffer)
            buffer.clear()
    if buffer:
        yield "".join(buffer)


def _encode_sse(event: str, payload: Dict[str, Any]) -> str:
    data = json.dumps(payload, ensure_ascii=False)
    return f"event: {event}\ndata: {data}\n\n"


async def _execute_inference(
    request: InferenceRequest,
    settings: Settings,
    context: AuthContext,
) -> tuple[str, float, str, Dict[str, Any]]:
    try:
        enforce_prompt_policy(request.prompt, settings)
    except ModerationError as exc:
        INFER_REQUESTS.labels(outcome="error").inc()
        log_audit_event(
            event_type="llm.infer.rejected",
            actor=context.subject,
            payload={"phase": "prompt", "code": exc.code, "topics": exc.topics},
            settings=settings,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": exc.code, "message": exc.message, "topics": exc.topics},
        ) from exc

    # Use scheduler to decide on runner
    _scheduler.upstream_available = bool(settings.llm_endpoint)
    runner_choice = _scheduler.schedule(request.prompt, prefer_local=False)
    
    scheduler_metadata = {
        "runner_choice": runner_choice.runner_type,
        "runner_reason": runner_choice.reason,
        "estimated_cost_j": runner_choice.estimated_cost_j,
        "estimated_latency_ms": runner_choice.estimated_latency_ms,
    }

    try:
        text, latency_ms, provider = await _perform_upstream_call(request, settings)
    except HTTPException:
        INFER_REQUESTS.labels(outcome="error").inc()
        log_audit_event(
            event_type="llm.infer.error",
            actor=context.subject,
            payload={"mode": request.mode, "scheduler": scheduler_metadata},
            settings=settings,
        )
        raise

    try:
        moderated_text, tone, paraphrased = await moderate_response(text, settings)
    except ModerationError as exc:
        INFER_REQUESTS.labels(outcome="error").inc()
        log_audit_event(
            event_type="llm.infer.rejected",
            actor=context.subject,
            payload={"phase": "response", "code": exc.code, "topics": exc.topics},
            settings=settings,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": exc.code, "message": exc.message, "topics": exc.topics},
        ) from exc

    diagnostics = ModerationDiagnostics(
        tone=tone.label,
        tone_score=tone.score,
        paraphrased=paraphrased,
        negative_terms=tone.negative_terms,
        positive_terms=tone.positive_terms,
    )

    INFER_REQUESTS.labels(outcome="success").inc()
    INFER_LATENCY.labels(provider=provider or "unknown").observe((latency_ms or 0.0) / 1000.0)

    moderation_payload = safe_model_dump(diagnostics)

    log_audit_event(
        event_type="llm.infer",
        actor=context.subject,
        payload={
            "mode": request.mode,
            "provider": provider,
            "latency_ms": latency_ms,
            "moderation": moderation_payload,
        },
        settings=settings,
    )
    log_genome_event(
        stage="response",
        actor=context.subject,
        payload={
            "provider": provider,
            "latency_ms": latency_ms,
            "moderation": moderation_payload,
            "scheduler": scheduler_metadata,
        },
        settings=settings,
    )
    return text, latency_ms, provider, scheduler_metadata


async def _sse_event_stream(
    request: InferenceRequest,
    settings: Settings,
    context: AuthContext,
) -> AsyncGenerator[str, None]:
    try:
        text, latency_ms, provider, scheduler_meta = await _execute_inference(request, settings, context)
    except HTTPException as exc:
        yield _encode_sse("error", {"detail": exc.detail})
        return

    for chunk in _token_chunks(text):
        if chunk:
            yield _encode_sse("token", {"token": chunk})

    yield _encode_sse(
        "done",
        {
            "provider": provider,
            "latency_ms": latency_ms,
            "scheduler": scheduler_meta,
        },
    )


async def _websocket_event_stream(
    request: InferenceRequest,
    settings: Settings,
    context: AuthContext,
) -> AsyncGenerator[Dict[str, Any], None]:
    try:
        text, latency_ms, provider, scheduler_meta = await _execute_inference(request, settings, context)
    except HTTPException as exc:
        yield {"type": "error", "detail": exc.detail}
        return

    for chunk in _token_chunks(text):
        if chunk:
            yield {"type": "token", "token": chunk}

    yield {"type": "done", "provider": provider, "latency_ms": latency_ms, "scheduler": scheduler_meta}


@router.post("/api/v1/infer", response_model=InferenceResponse)
async def infer(
    request: InferenceRequest,
    settings: Settings = Depends(get_settings),
    context: AuthContext = Depends(require_permission("kolibri.infer")),
) -> InferenceResponse:
    if settings.response_mode != "llm":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM mode is disabled",
        )

    text, latency_ms, provider, _scheduler_meta = await _execute_inference(request, settings, context)
    return InferenceResponse(response=text, provider=provider, latency_ms=latency_ms)


@router.post("/api/v1/infer/stream")
async def infer_stream(
    request: InferenceRequest,
    settings: Settings = Depends(get_settings),
    context: AuthContext = Depends(require_permission("kolibri.infer")),
) -> StreamingResponse:
    if settings.response_mode != "llm":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM mode is disabled",
        )

    stream = _sse_event_stream(request, settings, context)
    headers = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    return StreamingResponse(stream, media_type="text/event-stream", headers=headers)


async def _authenticate_websocket(websocket: WebSocket, settings: Settings) -> AuthContext:
    policy_violation_code = 1008
    if not settings.sso_enabled:
        roles = set(settings.offline_mode_roles or ["system:admin"])
        return AuthContext(
            subject="offline-mode",
            roles=roles,
            attributes={"mode": "offline"},
            session_expires_at=None,
            session_id=None,
        )

    authorization = websocket.headers.get("Authorization")
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        if not token:
            await websocket.close(code=policy_violation_code, reason="Empty bearer token")
            raise WebSocketDisconnect(code=policy_violation_code)
        try:
            return verify_session_token(token, settings)
        except HTTPException as exc:  # pragma: no cover - defensive close
            await websocket.close(code=policy_violation_code, reason=exc.detail)
            raise WebSocketDisconnect(code=policy_violation_code) from exc

    await websocket.close(code=policy_violation_code, reason="Missing bearer token")
    raise WebSocketDisconnect(code=policy_violation_code)


@router.websocket("/ws/v1/infer")
async def infer_websocket(websocket: WebSocket) -> None:
    settings = get_settings()
    if settings.response_mode != "llm":
        await websocket.close(code=1013, reason="LLM mode is disabled")
        return

    try:
        context = await _authenticate_websocket(websocket, settings)
    except WebSocketDisconnect:
        return

    policy = get_rbac_policy(settings=settings)
    if not policy.is_allowed(context.roles, "kolibri.infer"):
        await websocket.close(code=1008, reason="Insufficient permissions")
        return

    await websocket.accept()

    while True:
        try:
            payload = await websocket.receive_json()
        except WebSocketDisconnect:
            break
        except json.JSONDecodeError:
            await websocket.send_json({"type": "error", "detail": "Invalid JSON payload"})
            continue

        try:
            request = InferenceRequest(**payload)
        except ValidationError as exc:
            await websocket.send_json(
                {
                    "type": "error",
                    "detail": "Invalid request payload",
                    "errors": exc.errors(),
                }
            )
            continue

        async for message in _websocket_event_stream(request, settings, context):
            try:
                await websocket.send_json(message)
            except WebSocketDisconnect:
                return


# ============================================================================
# KOLIBRI AI — UNIFIED REASONING ENDPOINT
# ============================================================================

@router.post("/api/v1/ai/reason")
async def ai_reason(
    request: InferenceRequest,
    settings: Settings = Depends(get_settings),
    context: AuthContext = Depends(get_current_identity),
) -> Dict[str, Any]:
    """
    Execute Generative Decimal AI reasoning — самообучающаяся система.
    
    Использует:
    - Decimal cognition: текст → цифры 0-9
    - Эволюционные формулы с фитнесом
    - Фрактальную вложенность
    - Децентрализованное хранение
    """
    start = time.perf_counter()
    
    try:
        # Step 1: Validate prompt
        enforce_prompt_policy(request.prompt, settings)
    except ModerationError as exc:
        INFER_REQUESTS.labels(outcome="error").inc()
        log_audit_event(
            event_type="kolibri_ai.reason.rejected",
            actor=context.subject,
            payload={"phase": "prompt", "code": exc.code, "topics": exc.topics},
            settings=settings,
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": exc.code, "message": exc.message, "topics": exc.topics},
        ) from exc
    
    # Step 2: Execute generative reasoning
    try:
        result = await _generative_ai.reason(request.prompt)
    except Exception as exc:
        INFER_REQUESTS.labels(outcome="error").inc()
        log_audit_event(
            event_type="kolibri_ai.reason.error",
            actor=context.subject,
            payload={"error": str(exc)},
            settings=settings,
        )
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Generative AI failed: {exc}",
        ) from exc
    
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    
    # Step 3: Log success
    INFER_REQUESTS.labels(outcome="success").inc()
    INFER_LATENCY.labels(provider="generative_decimal_ai").observe(elapsed_ms / 1000.0)
    
    log_audit_event(
        event_type="kolibri_ai.generative_reason",
        actor=context.subject,
        payload={
            "query_length": len(request.prompt),
            "response_length": len(result["response"]),
            "confidence": result["confidence"],
            "mode": result["mode"],
            "formula_fitness": result["formula_fitness"],
            "generation": result["generation"],
            "latency_ms": elapsed_ms,
        },
        settings=settings,
    )
    
    # Step 4: Log genome evolution (optional)
    if result["formula_fitness"] > 0.5:
        try:
            log_genome_event(
                stage="formula_application",
                actor=context.subject,
                payload={
                    "formula_gene": result["formula_gene"],
                    "fitness": result["formula_fitness"],
                    "generation": result["generation"],
                    "query_digest": hashlib.sha256(request.prompt.encode()).hexdigest()[:16],
                },
                settings=settings,
            )
        except Exception as log_err:
            LOGGER.warning(f"Failed to log genome event: {log_err}")
    
    # Step 5: Return generative decision
    return result


@router.post("/api/v1/ai/chat")
async def ai_chat(
    request: InferenceRequest,
    settings: Settings = Depends(get_settings),
) -> Dict[str, Any]:
    """
    Chat endpoint для генеративной ИИ системы.
    
    Публичный endpoint без авторизации для использования в UI.
    Возвращает поле 'message' для совместимости с frontend.
    """
    start = time.perf_counter()
    
    try:
        enforce_prompt_policy(request.prompt, settings)
    except ModerationError as exc:
        INFER_REQUESTS.labels(outcome="error").inc()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": exc.code, "message": exc.message, "topics": exc.topics},
        ) from exc
    
    try:
        result = await _generative_ai.reason(request.prompt)
    except Exception as exc:
        INFER_REQUESTS.labels(outcome="error").inc()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Generative AI failed: {exc}",
        ) from exc
    
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    
    INFER_REQUESTS.labels(outcome="success").inc()
    INFER_LATENCY.labels(provider="generative_decimal_ai").observe(elapsed_ms / 1000.0)
    
    # Возвращаем с полем 'message' для совместимости с frontend
    return {
        "message": result["response"],
        "response": result["response"],
        "confidence": result["confidence"],
        "mode": result["mode"],
        "latency_ms": elapsed_ms,
        "generation": result["generation"],
        "formula_fitness": result["formula_fitness"],
    }


@router.post("/api/v1/ai/teach")
async def ai_teach(
    input_text: str,
    expected_output: str,
    evolve_generations: int = 5,
    settings: Settings = Depends(get_settings),
) -> Dict[str, Any]:
    """
    Обучить генеративную ИИ на примере.
    
    Добавляет пример (вход → выход) и запускает эволюцию формул.
    Система самообучается, улучшая фитнес через генетический алгоритм.
    
    Публичный endpoint для использования в UI обучения.
    """
    if not input_text or not expected_output:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both input_text and expected_output are required"
        )
    
    if evolve_generations < 1 or evolve_generations > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="evolve_generations must be between 1 and 100"
        )
    
    try:
        result = await _generative_ai.teach(input_text, expected_output, evolve_generations)
    except Exception as exc:
        log_audit_event(
            event_type="kolibri_ai.teach.error",
            actor="public-ui",
            payload={"error": str(exc)},
            settings=settings,
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Teaching failed: {exc}",
        ) from exc
    
    # Log successful learning
    log_audit_event(
        event_type="kolibri_ai.teach",
        actor="public-ui",
        payload={
            "input_length": len(input_text),
            "output_length": len(expected_output),
            "generations": evolve_generations,
            "best_fitness": result["evolution"]["best_fitness"],
        },
        settings=settings,
    )
    
    return result


@router.get("/api/v1/ai/generative/stats")
async def ai_generative_stats() -> Dict[str, Any]:
    """Возвращает статистику генеративной ИИ системы.
    
    Этот endpoint доступен без авторизации для отображения
    публичной статистики в UI.
    """
    return _generative_ai.get_stats()


@router.post("/api/v1/ai/learn/data")
async def ai_learn_from_data(
    data_pairs: List[Dict[str, str]],
    evolve_generations: int = 10,
    settings: Settings = Depends(get_settings),
    context: AuthContext = Depends(get_current_identity),
) -> Dict[str, Any]:
    """Обучает AI на массиве пар входных и выходных данных.
    
    Args:
        data_pairs: Список словарей с ключами "input" и "output"
        evolve_generations: Количество поколений эволюции (1-100)
        
    Example:
        POST /api/v1/ai/learn/data
        [
            {"input": "hello", "output": "hi there"},
            {"input": "goodbye", "output": "see you later"},
            {"input": "thanks", "output": "you're welcome"}
        ]
    """
    if not data_pairs or len(data_pairs) > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide 1-1000 data pairs"
        )
    
    if not (1 <= evolve_generations <= 100):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="evolve_generations must be between 1 and 100"
        )
    
    # Преобразуем словари в кортежи
    pairs = []
    for i, item in enumerate(data_pairs):
        if "input" not in item or "output" not in item:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Item {i} missing 'input' or 'output' field"
            )
        pairs.append((item["input"], item["output"]))
    
    # Обучаем систему
    result = await _generative_ai.learn_from_data(pairs, evolve_generations)
    
    # Логируем событие
    log_audit_event(
        event_type="kolibri_ai.learn_from_data",
        actor=context.subject,
        payload={
            "examples_count": len(pairs),
            "generations": evolve_generations,
            "best_fitness": result["evolution"]["best_fitness"],
        },
        settings=settings,
    )
    
    return result


@router.post("/api/v1/ai/reason/batch")
async def ai_reason_batch(
    queries: List[str],
    settings: Settings = Depends(get_settings),
    context: AuthContext = Depends(require_permission("kolibri.infer")),
) -> Dict[str, Any]:
    """Process multiple queries concurrently via Kolibri AI."""
    if not queries or len(queries) > 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provide 1-100 queries",
        )
    
    # Configure AI
    _ai_core.enable_llm = settings.response_mode == "llm" and bool(settings.llm_endpoint)
    _ai_core.llm_endpoint = settings.llm_endpoint
    
    # Execute batch reasoning
    start = time.perf_counter()
    decisions = await _ai_core.batch_reason(queries)
    elapsed_ms = (time.perf_counter() - start) * 1000.0
    
    log_audit_event(
        event_type="kolibri_ai.batch_reason",
        actor=context.subject,
        payload={
            "batch_size": len(queries),
            "total_energy_j": _ai_core.total_energy_j,
            "total_latency_ms": elapsed_ms,
        },
        settings=settings,
    )
    
    return {
        "batch_size": len(decisions),
        "decisions": [
            {
                "query": d.query,
                "response": d.response,
                "confidence": d.confidence,
                "signature": d.signature,
            }
            for d in decisions
        ],
        "total_energy_j": _ai_core.total_energy_j,
        "total_latency_ms": elapsed_ms,
        "stats": _ai_core.get_stats(),
    }


@router.get("/api/v1/ai/stats")
async def ai_stats(
    settings: Settings = Depends(get_settings),
    context: AuthContext = Depends(require_permission("kolibri.infer")),
) -> Dict[str, Any]:
    """Get Kolibri AI statistics."""
    return _ai_core.get_stats()