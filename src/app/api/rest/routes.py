from __future__ import annotations

import hashlib

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.api.dependencies import AppContainer, get_container
from app.api.rest.models import (
    IngestionJobResponse,
    InvokeRequest,
    InvokeResponse,
)
from app.contracts.ingestion import DocumentBlob
from app.core.exceptions import FeatureDisabledError
from app.utils.id_normalizers import stable_uuid

router = APIRouter(prefix="/v1", tags=["v1"])


@router.post("/invoke", response_model=InvokeResponse)
async def invoke(
    request: InvokeRequest,
    container: AppContainer = Depends(get_container),
) -> InvokeResponse:
    result = await container.graph_runtime.invoke(request.model_dump())
    return InvokeResponse(**result)


@router.post("/ingest/upload", response_model=IngestionJobResponse)
async def ingest_upload(
    file: UploadFile = File(...),
    collection: str | None = Form(default=None),
    embedding_provider: str | None = Form(default=None),
    graph_enabled: bool = Form(default=True),
    document_id: str | None = Form(default=None),
    container: AppContainer = Depends(get_container),
) -> IngestionJobResponse:
    if not container.settings.enable_ingestion:
        raise FeatureDisabledError("ingestion")

    content = await file.read()
    max_size = container.settings.max_upload_size_mb * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(status_code=413, detail="File is too large")

    computed_id = str(stable_uuid(f"{file.filename}:{hashlib.sha256(content).hexdigest()}"))
    blob = DocumentBlob(
        document_id=document_id or computed_id,
        filename=file.filename,
        content_type=file.content_type or "application/octet-stream",
        content_bytes=content,
    )

    job = await container.ingestion_pipeline.ingest_blob(
        blob=blob,
        collection=collection,
        embedding_provider=embedding_provider,
        graph_enabled=graph_enabled,
    )
    return IngestionJobResponse(
        job_id=job.job_id,
        document_id=job.document_id,
        status=job.status,
        message=job.message,
        stats=job.stats,
    )


@router.get("/ingest/jobs/{job_id}", response_model=IngestionJobResponse)
async def get_ingest_job(
    job_id: str,
    container: AppContainer = Depends(get_container),
) -> IngestionJobResponse:
    job = container.ingestion_pipeline.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return IngestionJobResponse(
        job_id=job.job_id,
        document_id=job.document_id,
        status=job.status,
        message=job.message,
        stats=job.stats,
    )
