"""FastAPI backend for the Knowledge Expansion System."""

import asyncio
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Union
from urllib.parse import urlparse
import uuid
import csv
import io
import json
import time
from datetime import datetime
from enum import Enum

from fastapi import FastAPI, File, Form, HTTPException, UploadFile, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, HttpUrl, Field

from ..database.service import ZettelkastenService
from ..ingestion import ContentIngestionManager
from ..llm.knowledge_retriever import KnowledgeEnhancedLLM

app = FastAPI(title="Knowledge Expansion System API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React development server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Models
class UploadResponse(BaseModel):
    """Response model for file uploads."""
    id: str
    title: str
    source_type: str
    summary: str
    tags: List[str]
    is_new_information: bool
    confidence_score: float

class QueryRequest(BaseModel):
    """Request model for database queries."""
    query: str
    include_sources: bool = True

class QueryResponse(BaseModel):
    """Response model for database queries."""
    response: str
    confidence: float
    sources: Optional[List[str]] = None

class NodeDetails(BaseModel):
    """Details of a Zettelkasten node."""
    id: str
    title: str
    summary: str
    tags: List[str]
    source_type: str
    source_path: Union[str, HttpUrl]
    is_new_information: bool
    confidence_score: float
    related_nodes: List[str]

class GraphData(BaseModel):
    """Graph visualization data."""
    nodes: List[Dict]
    edges: List[Dict]

# New API Models
class BulkUploadResponse(BaseModel):
    """Response model for bulk file uploads."""
    total_files: int
    processed_files: int
    failed_files: List[str]
    nodes: List[UploadResponse]

class WebScrapingRequest(BaseModel):
    """Request model for web scraping."""
    urls: List[HttpUrl]
    max_depth: Optional[int] = 1
    follow_links: Optional[bool] = False
    same_domain_only: Optional[bool] = True

class ScrapingStatus(BaseModel):
    """Status model for web scraping jobs."""
    job_id: str
    total_urls: int
    processed_urls: int
    failed_urls: List[str]
    nodes: List[UploadResponse]
    is_complete: bool

class BatchJobControl(BaseModel):
    """Control model for batch processing jobs."""
    job_id: str
    action: str  # pause, resume, cancel

class RetryRequest(BaseModel):
    """Request model for retrying failed items."""
    job_id: str
    items: List[str]  # IDs of items to retry

# Enhanced API Models
class BatchProcessingConfig(BaseModel):
    """Configuration for batch processing."""
    batch_size: int = 10
    error_threshold: float = 0.2  # 20% error rate threshold
    auto_pause: bool = True

class BatchMetrics(BaseModel):
    """Detailed metrics for batch processing."""
    processing_speed: float  # items per second
    estimated_time_remaining: float  # seconds
    error_rate: float
    success_rate: float
    average_processing_time: float
    start_time: str
    elapsed_time: float

class BatchJobHistory(BaseModel):
    """History record for a batch job."""
    job_id: str
    job_type: str  # upload or scraping
    total_items: int
    successful_items: int
    failed_items: int
    start_time: str
    end_time: Optional[str]
    duration: float
    final_status: str
    error_rate: float
    config: BatchProcessingConfig

class BatchAnalytics(BaseModel):
    """Analytics for batch operations."""
    total_processed: int
    success_rate: float
    average_processing_time: float
    error_distribution: Dict[str, int]
    processing_speed_over_time: List[Dict[str, float]]
    common_error_types: List[Dict[str, any]]

# Update BatchJobStatus with new fields
class BatchJobStatus(BaseModel):
    """Enhanced status model for batch jobs."""
    job_id: str
    total_items: int
    processed_items: int
    failed_items: List[Dict[str, str]]
    successful_items: List[Dict[str, any]]
    status: str  # running, paused, completed, cancelled
    progress_details: Dict[str, any]
    started_at: str
    updated_at: str
    config: BatchProcessingConfig
    metrics: BatchMetrics
    current_batch: Optional[List[str]]

# Store for batch job history
batch_history: Dict[str, BatchJobHistory] = {}

# Store for batch analytics
batch_analytics: Dict[str, BatchAnalytics] = {}

# Service instances
service: Optional[ZettelkastenService] = None
ingestion: Optional[ContentIngestionManager] = None
llm: Optional[KnowledgeEnhancedLLM] = None

# Store for scraping jobs
scraping_jobs: Dict[str, ScrapingStatus] = {}

# Store for batch jobs
batch_jobs: Dict[str, Dict] = {}

# LLM Configuration Models
class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    DEEPSEEK = "deepseek"
    OLLAMA = "ollama"

class LLMConfig(BaseModel):
    """Configuration for LLM providers."""
    provider: LLMProvider
    model_name: str
    api_key: Optional[str] = None
    api_base: Optional[str] = None  # For Ollama or custom endpoints
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    context_window: Optional[int] = None
    streaming: bool = False

class LLMModelInfo(BaseModel):
    """Information about available LLM models."""
    provider: str
    name: str
    context_window: int
    capabilities: List[str]
    pricing: Optional[str] = None

# Store for LLM configurations
llm_configs: Dict[str, LLMConfig] = {}

# Default models by provider
DEFAULT_MODELS = {
    LLMProvider.OPENAI: [
        LLMModelInfo(
            provider="openai",
            name="gpt-4-turbo-preview",
            context_window=128000,
            capabilities=["text", "analysis", "code"],
            pricing="$0.01/1K tokens"
        ),
        LLMModelInfo(
            provider="openai",
            name="gpt-3.5-turbo",
            context_window=16385,
            capabilities=["text", "analysis"],
            pricing="$0.001/1K tokens"
        )
    ],
    LLMProvider.ANTHROPIC: [
        LLMModelInfo(
            provider="anthropic",
            name="claude-3-opus",
            context_window=200000,
            capabilities=["text", "analysis", "code"],
            pricing="$0.015/1K tokens"
        ),
        LLMModelInfo(
            provider="anthropic",
            name="claude-3-sonnet",
            context_window=200000,
            capabilities=["text", "analysis"],
            pricing="$0.003/1K tokens"
        )
    ],
    LLMProvider.DEEPSEEK: [
        LLMModelInfo(
            provider="deepseek",
            name="deepseek-coder",
            context_window=32768,
            capabilities=["text", "code"],
            pricing="$0.002/1K tokens"
        )
    ],
    LLMProvider.OLLAMA: [
        LLMModelInfo(
            provider="ollama",
            name="llama2",
            context_window=4096,
            capabilities=["text", "analysis"],
            pricing="Free (Local)"
        ),
        LLMModelInfo(
            provider="ollama",
            name="codellama",
            context_window=16384,
            capabilities=["text", "code"],
            pricing="Free (Local)"
        ),
        LLMModelInfo(
            provider="ollama",
            name="mistral",
            context_window=8192,
            capabilities=["text", "analysis"],
            pricing="Free (Local)"
        )
    ]
}

# LLM Performance and Configuration Models
class TokenUsage(BaseModel):
    """Token usage statistics."""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    total_cost: float

class ModelPerformanceMetrics(BaseModel):
    """Performance metrics for an LLM model."""
    model_name: str
    average_latency: float  # seconds
    token_throughput: float  # tokens per second
    error_rate: float
    total_requests: int
    total_tokens: TokenUsage
    last_updated: datetime

class ModelComparison(BaseModel):
    """Comparison data between different models."""
    models: List[str]
    metrics: Dict[str, ModelPerformanceMetrics]
    benchmark_results: Dict[str, Dict[str, float]]  # model -> metric -> score
    cost_analysis: Dict[str, Dict[str, float]]  # model -> metric -> value

class PromptTemplate(BaseModel):
    """Custom prompt template."""
    id: str
    name: str
    description: str
    template: str
    variables: List[str]
    model_name: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_used: Optional[datetime] = None
    usage_count: int = 0

class FallbackConfig(BaseModel):
    """Configuration for model fallback behavior."""
    primary_model: str
    fallback_models: List[str]
    fallback_triggers: Dict[str, float]  # error_type -> threshold
    max_retries: int = 3
    timeout_seconds: float = 30.0

# Store for metrics and templates
model_metrics: Dict[str, ModelPerformanceMetrics] = {}
prompt_templates: Dict[str, PromptTemplate] = {}
fallback_configs: Dict[str, FallbackConfig] = {}

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    global service, ingestion, llm
    
    service = ZettelkastenService()
    await service.setup()
    
    ingestion = ContentIngestionManager()
    llm = KnowledgeEnhancedLLM(service)

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up services on shutdown."""
    if service:
        await service.close()

@app.post("/upload/file", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None)
):
    """Handle file uploads."""
    try:
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_path = Path(temp_file.name)
        
        try:
            # Process the file
            content = await ingestion.ingest_content(temp_path)
            node, _ = await service.process_ingested_content(content)
            
            return UploadResponse(
                id=node.id,
                title=node.title or title or file.filename,
                source_type=node.source_type,
                summary=node.summary,
                tags=list(node.tags),
                is_new_information=node.is_new_information,
                confidence_score=node.confidence_score
            )
        finally:
            # Clean up temporary file
            temp_path.unlink()
            
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/upload/url", response_model=UploadResponse)
async def upload_url(url: HttpUrl):
    """Handle URL uploads."""
    try:
        # Process the URL
        content = await ingestion.ingest_content(url)
        node, _ = await service.process_ingested_content(content)
        
        return UploadResponse(
            id=node.id,
            title=node.title or str(url),
            source_type=node.source_type,
            summary=node.summary,
            tags=list(node.tags),
            is_new_information=node.is_new_information,
            confidence_score=node.confidence_score
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/query", response_model=QueryResponse)
async def query_database(request: QueryRequest):
    """Query the knowledge base."""
    try:
        response = await llm.generate_response(
            request.query,
            include_sources=request.include_sources
        )
        return QueryResponse(**response)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/nodes/{node_id}", response_model=NodeDetails)
async def get_node(node_id: str):
    """Get details of a specific node."""
    try:
        node = await service.get_note(node_id)
        if not node:
            raise HTTPException(status_code=404, detail="Node not found")
        
        return NodeDetails(
            id=node.id,
            title=node.title,
            summary=node.summary,
            tags=list(node.tags),
            source_type=node.source_type,
            source_path=node.source_path,
            is_new_information=node.is_new_information,
            confidence_score=node.confidence_score,
            related_nodes=list(node.related_nodes)
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/graph", response_model=GraphData)
async def get_graph_data(
    max_nodes: Optional[int] = 100,
    min_confidence: Optional[float] = 0.5
):
    """Get graph visualization data."""
    try:
        # Get all notes
        notes = await service.search_notes(min_confidence=min_confidence)
        notes = notes[:max_nodes]  # Limit number of nodes
        
        # Create nodes
        nodes = [
            {
                "id": note.id,
                "label": note.title,
                "type": note.source_type,
                "tags": list(note.tags),
                "isNew": note.is_new_information,
                "confidence": note.confidence_score
            }
            for note in notes
        ]
        
        # Create edges
        edges = []
        for note in notes:
            related = await service.get_related(note.id)
            for rel in related:
                edges.append({
                    "source": note.id,
                    "target": rel.id,
                    "weight": rel.confidence_score
                })
        
        return GraphData(nodes=nodes, edges=edges)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/search")
async def search_nodes(
    keywords: Optional[str] = None,
    tags: Optional[str] = None,
    source_type: Optional[str] = None,
    only_new: Optional[bool] = None,
    min_confidence: Optional[float] = None
):
    """Search for nodes with filters."""
    try:
        notes = await service.search_notes(
            keywords=keywords.split() if keywords else None,
            tags=tags.split(",") if tags else None,
            source_types=[source_type] if source_type else None,
            only_new=only_new,
            min_confidence=min_confidence
        )
        
        return [
            {
                "id": note.id,
                "title": note.title,
                "summary": note.summary,
                "tags": list(note.tags),
                "source_type": note.source_type,
                "is_new_information": note.is_new_information,
                "confidence_score": note.confidence_score
            }
            for note in notes
        ]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/upload/bulk", response_model=BulkUploadResponse)
async def upload_bulk_files(
    files: List[UploadFile] = File(...),
    background_tasks: BackgroundTasks = None
):
    """Handle bulk file uploads."""
    response = BulkUploadResponse(
        total_files=len(files),
        processed_files=0,
        failed_files=[],
        nodes=[]
    )

    async def process_file(file: UploadFile):
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(delete=False) as temp_file:
                content = await file.read()
                temp_file.write(content)
                temp_path = Path(temp_file.name)
            
            try:
                # Process the file
                content = await ingestion.ingest_content(temp_path)
                node, _ = await service.process_ingested_content(content)
                
                response.nodes.append(UploadResponse(
                    id=node.id,
                    title=node.title or file.filename,
                    source_type=node.source_type,
                    summary=node.summary,
                    tags=list(node.tags),
                    is_new_information=node.is_new_information,
                    confidence_score=node.confidence_score
                ))
                response.processed_files += 1
            finally:
                # Clean up temporary file
                temp_path.unlink()
                
        except Exception as e:
            response.failed_files.append(f"{file.filename}: {str(e)}")

    # Process files concurrently
    await asyncio.gather(*[process_file(file) for file in files])
    return response

@app.post("/scrape/start", response_model=ScrapingStatus)
async def start_web_scraping(
    request: WebScrapingRequest,
    background_tasks: BackgroundTasks
):
    """Start a web scraping job."""
    job_id = str(uuid.uuid4())
    status = ScrapingStatus(
        job_id=job_id,
        total_urls=len(request.urls),
        processed_urls=0,
        failed_urls=[],
        nodes=[],
        is_complete=False
    )
    scraping_jobs[job_id] = status

    async def process_url(url: HttpUrl, depth: int = 0):
        try:
            # Process the URL
            content = await ingestion.ingest_content(url)
            node, _ = await service.process_ingested_content(content)
            
            status.nodes.append(UploadResponse(
                id=node.id,
                title=node.title or str(url),
                source_type=node.source_type,
                summary=node.summary,
                tags=list(node.tags),
                is_new_information=node.is_new_information,
                confidence_score=node.confidence_score
            ))
            status.processed_urls += 1

            # Follow links if requested
            if request.follow_links and depth < request.max_depth:
                links = await ingestion.extract_links(url)
                if request.same_domain_only:
                    base_domain = urlparse(str(url)).netloc
                    links = [
                        link for link in links
                        if urlparse(str(link)).netloc == base_domain
                    ]
                
                # Process new links concurrently
                status.total_urls += len(links)
                await asyncio.gather(*[
                    process_url(link, depth + 1)
                    for link in links
                ])
                
        except Exception as e:
            status.failed_urls.append(f"{url}: {str(e)}")

    async def run_scraping():
        try:
            # Process initial URLs concurrently
            await asyncio.gather(*[
                process_url(url)
                for url in request.urls
            ])
        finally:
            status.is_complete = True

    # Start scraping in background
    background_tasks.add_task(run_scraping)
    return status

@app.get("/scrape/{job_id}", response_model=ScrapingStatus)
async def get_scraping_status(job_id: str):
    """Get the status of a web scraping job."""
    if job_id not in scraping_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    return scraping_jobs[job_id]

@app.post("/batch/control", response_model=BatchJobStatus)
async def control_batch_job(control: BatchJobControl):
    """Control a batch processing job."""
    if control.job_id not in batch_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = batch_jobs[control.job_id]
    
    if control.action == "pause":
        job["status"] = "paused"
    elif control.action == "resume":
        job["status"] = "running"
    elif control.action == "cancel":
        job["status"] = "cancelled"
    else:
        raise HTTPException(status_code=400, detail="Invalid action")
    
    return job

@app.post("/batch/retry", response_model=BatchJobStatus)
async def retry_failed_items(retry: RetryRequest):
    """Retry failed items in a batch job."""
    if retry.job_id not in batch_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = batch_jobs[retry.job_id]
    
    # Move items back to queue
    failed_items = {item["id"]: item for item in job["failed_items"]}
    retry_items = [failed_items[item_id] for item_id in retry.items if item_id in failed_items]
    
    # Update job status
    job["failed_items"] = [item for item in job["failed_items"] if item["id"] not in retry.items]
    job["total_items"] += len(retry_items)
    
    # Process retry items
    if job["type"] == "upload":
        background_tasks.add_task(process_files, retry_items, job)
    else:
        background_tasks.add_task(process_urls, retry_items, job)
    
    return job

@app.get("/batch/export/{job_id}")
async def export_batch_results(job_id: str, format: str = "json"):
    """Export batch processing results."""
    if job_id not in batch_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = batch_jobs[job_id]
    
    if format == "json":
        return StreamingResponse(
            io.StringIO(json.dumps(job, indent=2)),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=batch_job_{job_id}.json"}
        )
    elif format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["id", "title", "source_type", "status", "error"])
        
        # Write successful items
        for item in job["successful_items"]:
            writer.writerow([item["id"], item["title"], item["source_type"], "success", ""])
        
        # Write failed items
        for item in job["failed_items"]:
            writer.writerow([item["id"], item.get("title", ""), item.get("source_type", ""), "failed", item["error"]])
        
        output.seek(0)
        return StreamingResponse(
            output,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=batch_job_{job_id}.csv"}
        )
    else:
        raise HTTPException(status_code=400, detail="Unsupported format")

@app.post("/batch/configure/{job_id}")
async def configure_batch_job(job_id: str, config: BatchProcessingConfig):
    """Configure batch processing parameters."""
    if job_id not in batch_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = batch_jobs[job_id]
    job["config"] = config.dict()
    
    return job

@app.get("/batch/metrics/{job_id}")
async def get_batch_metrics(job_id: str):
    """Get detailed metrics for a batch job."""
    if job_id not in batch_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = batch_jobs[job_id]
    return job["metrics"]

@app.get("/batch/history")
async def get_batch_history(
    limit: int = 10,
    offset: int = 0,
    job_type: Optional[str] = None,
    min_success_rate: Optional[float] = None
):
    """Get batch job history with filtering."""
    history = list(batch_history.values())
    
    if job_type:
        history = [h for h in history if h.job_type == job_type]
    if min_success_rate is not None:
        history = [h for h in history if (h.successful_items / h.total_items) >= min_success_rate]
    
    # Sort by start time descending
    history.sort(key=lambda x: x.start_time, reverse=True)
    
    return {
        "total": len(history),
        "items": history[offset:offset + limit]
    }

@app.get("/batch/analytics")
async def get_batch_analytics(
    time_range: Optional[str] = "24h",
    job_type: Optional[str] = None
):
    """Get analytics for batch operations."""
    analytics = batch_analytics.copy()
    
    if job_type:
        analytics = {k: v for k, v in analytics.items() if k.startswith(job_type)}
    
    # Aggregate analytics based on time range
    result = BatchAnalytics(
        total_processed=sum(a.total_processed for a in analytics.values()),
        success_rate=sum(a.success_rate for a in analytics.values()) / len(analytics) if analytics else 0,
        average_processing_time=sum(a.average_processing_time for a in analytics.values()) / len(analytics) if analytics else 0,
        error_distribution={},
        processing_speed_over_time=[],
        common_error_types=[]
    )
    
    # Combine error distributions
    for a in analytics.values():
        for error_type, count in a.error_distribution.items():
            if error_type in result.error_distribution:
                result.error_distribution[error_type] += count
            else:
                result.error_distribution[error_type] = count
    
    # Sort and limit common error types
    result.common_error_types = sorted(
        [{"type": k, "count": v} for k, v in result.error_distribution.items()],
        key=lambda x: x["count"],
        reverse=True
    )[:10]
    
    return result

# Update existing batch processing logic
async def process_batch(items: List[any], job: Dict):
    """Process a batch of items with enhanced monitoring."""
    config = job.get("config", BatchProcessingConfig().dict())
    batch_size = config["batch_size"]
    error_threshold = config["error_threshold"]
    
    start_time = time.time()
    processed = 0
    errors = 0
    
    for i in range(0, len(items), batch_size):
        if job["status"] == "cancelled":
            break
        if job["status"] == "paused":
            await asyncio.sleep(1)
            continue
            
        batch = items[i:i + batch_size]
        job["current_batch"] = [str(item) for item in batch]
        
        try:
            # Process batch items concurrently
            results = await asyncio.gather(
                *[process_item(item) for item in batch],
                return_exceptions=True
            )
            
            # Update counts and check error rate
            batch_errors = sum(1 for r in results if isinstance(r, Exception))
            errors += batch_errors
            processed += len(batch)
            
            error_rate = errors / processed if processed > 0 else 0
            if config["auto_pause"] and error_rate > error_threshold:
                job["status"] = "paused"
                job["metrics"]["error_rate"] = error_rate
                continue
            
            # Update metrics
            elapsed = time.time() - start_time
            job["metrics"].update({
                "processing_speed": processed / elapsed,
                "estimated_time_remaining": (len(items) - processed) / (processed / elapsed) if processed > 0 else 0,
                "error_rate": error_rate,
                "success_rate": 1 - error_rate,
                "average_processing_time": elapsed / processed if processed > 0 else 0,
                "elapsed_time": elapsed
            })
            
        except Exception as e:
            job["failed_items"].append({
                "id": str(uuid.uuid4()),
                "error": str(e),
                "batch": job["current_batch"]
            })
    
    # Update job history and analytics
    job_history = BatchJobHistory(
        job_id=job["job_id"],
        job_type=job["type"],
        total_items=len(items),
        successful_items=len(job["successful_items"]),
        failed_items=len(job["failed_items"]),
        start_time=job["started_at"],
        end_time=datetime.now().isoformat(),
        duration=time.time() - start_time,
        final_status=job["status"],
        error_rate=job["metrics"]["error_rate"],
        config=config
    )
    batch_history[job["job_id"]] = job_history

# Update existing batch processing logic
async def process_files(items: List[any], job: Dict):
    """Process a batch of file items with enhanced monitoring."""
    config = job.get("config", BatchProcessingConfig().dict())
    batch_size = config["batch_size"]
    error_threshold = config["error_threshold"]
    
    start_time = time.time()
    processed = 0
    errors = 0
    
    for i in range(0, len(items), batch_size):
        if job["status"] == "cancelled":
            break
        if job["status"] == "paused":
            await asyncio.sleep(1)
            continue
            
        batch = items[i:i + batch_size]
        job["current_batch"] = [str(item) for item in batch]
        
        try:
            # Process batch items concurrently
            results = await asyncio.gather(
                *[process_file(item) for item in batch],
                return_exceptions=True
            )
            
            # Update counts and check error rate
            batch_errors = sum(1 for r in results if isinstance(r, Exception))
            errors += batch_errors
            processed += len(batch)
            
            error_rate = errors / processed if processed > 0 else 0
            if config["auto_pause"] and error_rate > error_threshold:
                job["status"] = "paused"
                job["metrics"]["error_rate"] = error_rate
                continue
            
            # Update metrics
            elapsed = time.time() - start_time
            job["metrics"].update({
                "processing_speed": processed / elapsed,
                "estimated_time_remaining": (len(items) - processed) / (processed / elapsed) if processed > 0 else 0,
                "error_rate": error_rate,
                "success_rate": 1 - error_rate,
                "average_processing_time": elapsed / processed if processed > 0 else 0,
                "elapsed_time": elapsed
            })
            
        except Exception as e:
            job["failed_items"].append({
                "id": str(uuid.uuid4()),
                "error": str(e),
                "batch": job["current_batch"]
            })
    
    # Update job history and analytics
    job_history = BatchJobHistory(
        job_id=job["job_id"],
        job_type="upload",
        total_items=len(items),
        successful_items=len(job["successful_items"]),
        failed_items=len(job["failed_items"]),
        start_time=job["started_at"],
        end_time=datetime.now().isoformat(),
        duration=time.time() - start_time,
        final_status=job["status"],
        error_rate=job["metrics"]["error_rate"],
        config=config
    )
    batch_history[job["job_id"]] = job_history

# Update existing batch processing logic
async def process_urls(items: List[any], job: Dict):
    """Process a batch of URL items with enhanced monitoring."""
    config = job.get("config", BatchProcessingConfig().dict())
    batch_size = config["batch_size"]
    error_threshold = config["error_threshold"]
    
    start_time = time.time()
    processed = 0
    errors = 0
    
    for i in range(0, len(items), batch_size):
        if job["status"] == "cancelled":
            break
        if job["status"] == "paused":
            await asyncio.sleep(1)
            continue
            
        batch = items[i:i + batch_size]
        job["current_batch"] = [str(item) for item in batch]
        
        try:
            # Process batch items concurrently
            results = await asyncio.gather(
                *[process_url(item) for item in batch],
                return_exceptions=True
            )
            
            # Update counts and check error rate
            batch_errors = sum(1 for r in results if isinstance(r, Exception))
            errors += batch_errors
            processed += len(batch)
            
            error_rate = errors / processed if processed > 0 else 0
            if config["auto_pause"] and error_rate > error_threshold:
                job["status"] = "paused"
                job["metrics"]["error_rate"] = error_rate
                continue
            
            # Update metrics
            elapsed = time.time() - start_time
            job["metrics"].update({
                "processing_speed": processed / elapsed,
                "estimated_time_remaining": (len(items) - processed) / (processed / elapsed) if processed > 0 else 0,
                "error_rate": error_rate,
                "success_rate": 1 - error_rate,
                "average_processing_time": elapsed / processed if processed > 0 else 0,
                "elapsed_time": elapsed
            })
            
        except Exception as e:
            job["failed_items"].append({
                "id": str(uuid.uuid4()),
                "error": str(e),
                "batch": job["current_batch"]
            })
    
    # Update job history and analytics
    job_history = BatchJobHistory(
        job_id=job["job_id"],
        job_type="scraping",
        total_items=len(items),
        successful_items=len(job["successful_items"]),
        failed_items=len(job["failed_items"]),
        start_time=job["started_at"],
        end_time=datetime.now().isoformat(),
        duration=time.time() - start_time,
        final_status=job["status"],
        error_rate=job["metrics"]["error_rate"],
        config=config
    )
    batch_history[job["job_id"]] = job_history 

@app.get("/llm/providers")
async def get_llm_providers():
    """Get list of supported LLM providers."""
    return [{"id": p.value, "name": p.name} for p in LLMProvider]

@app.get("/llm/models/{provider}")
async def get_llm_models(provider: LLMProvider):
    """Get available models for a provider."""
    return DEFAULT_MODELS.get(provider, [])

@app.post("/llm/configure")
async def configure_llm(config: LLMConfig):
    """Configure LLM settings with performance tracking."""
    try:
        # Initialize metrics if not exists
        if config.model_name not in model_metrics:
            model_metrics[config.model_name] = ModelPerformanceMetrics(
                model_name=config.model_name,
                average_latency=0.0,
                token_throughput=0.0,
                error_rate=0.0,
                total_requests=0,
                total_tokens=TokenUsage(
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_tokens=0,
                    total_cost=0.0
                ),
                last_updated=datetime.utcnow()
            )
        
        # Existing configuration logic...
        if config.provider == LLMProvider.OLLAMA:
            # Test Ollama connection
            import requests
            base_url = config.api_base or "http://localhost:11434"
            response = requests.get(f"{base_url}/api/tags")
            if not response.ok:
                raise HTTPException(status_code=400, detail="Failed to connect to Ollama")
            
            # Check if model is available
            models = response.json()
            if config.model_name not in [m["name"] for m in models["models"]]:
                raise HTTPException(status_code=400, detail=f"Model {config.model_name} not available in Ollama")

        # Initialize the appropriate LLM client with performance tracking
        if config.provider == LLMProvider.OPENAI:
            from openai import OpenAI
            client = OpenAI(api_key=config.api_key)
            llm = KnowledgeEnhancedLLM(service, client=client, model=config.model_name)
        elif config.provider == LLMProvider.ANTHROPIC:
            from anthropic import Anthropic
            client = Anthropic(api_key=config.api_key)
            llm = KnowledgeEnhancedLLM(service, client=client, model=config.model_name)
        elif config.provider == LLMProvider.DEEPSEEK:
            from deepseek import Deepseek
            client = Deepseek(api_key=config.api_key)
            llm = KnowledgeEnhancedLLM(service, client=client, model=config.model_name)
        elif config.provider == LLMProvider.OLLAMA:
            from langchain.llms import Ollama
            client = Ollama(base_url=config.api_base, model=config.model_name)
            llm = KnowledgeEnhancedLLM(service, client=client)

        # Store configuration
        llm_configs[config.provider] = config
        
        return {"status": "success", "message": "LLM configured successfully"}
    except Exception as e:
        # Update error rate in metrics
        if config.model_name in model_metrics:
            metrics = model_metrics[config.model_name]
            metrics.error_rate = (metrics.error_rate * metrics.total_requests + 1) / (metrics.total_requests + 1)
            metrics.total_requests += 1
            metrics.last_updated = datetime.utcnow()
        
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/llm/config")
async def get_llm_config():
    """Get current LLM configuration."""
    return llm_configs 

@app.get("/llm/metrics/{model_name}")
async def get_model_metrics(model_name: str):
    """Get performance metrics for a specific model."""
    if model_name not in model_metrics:
        raise HTTPException(status_code=404, detail="Model metrics not found")
    return model_metrics[model_name]

@app.get("/llm/metrics/compare")
async def compare_models(model_names: List[str]):
    """Compare performance metrics between models."""
    metrics = {name: model_metrics[name] for name in model_names if name in model_metrics}
    if not metrics:
        raise HTTPException(status_code=404, detail="No metrics found for specified models")
    
    # Calculate benchmark scores
    benchmark_results = {}
    for name, metric in metrics.items():
        benchmark_results[name] = {
            "latency_score": 1.0 / metric.average_latency,
            "throughput_score": metric.token_throughput,
            "reliability_score": 1.0 - metric.error_rate,
            "cost_efficiency": metric.total_tokens.total_tokens / metric.total_tokens.total_cost
            if metric.total_tokens.total_cost > 0 else float('inf')
        }
    
    # Calculate cost analysis
    cost_analysis = {}
    for name, metric in metrics.items():
        cost_analysis[name] = {
            "cost_per_1k_tokens": metric.total_tokens.total_cost * 1000 / metric.total_tokens.total_tokens
            if metric.total_tokens.total_tokens > 0 else 0,
            "cost_per_request": metric.total_tokens.total_cost / metric.total_requests
            if metric.total_requests > 0 else 0
        }
    
    return ModelComparison(
        models=list(metrics.keys()),
        metrics=metrics,
        benchmark_results=benchmark_results,
        cost_analysis=cost_analysis
    )

@app.post("/llm/templates")
async def create_prompt_template(template: PromptTemplate):
    """Create a new prompt template."""
    template.id = str(uuid.uuid4())
    prompt_templates[template.id] = template
    return template

@app.get("/llm/templates")
async def list_prompt_templates():
    """List all prompt templates."""
    return list(prompt_templates.values())

@app.get("/llm/templates/{template_id}")
async def get_prompt_template(template_id: str):
    """Get a specific prompt template."""
    if template_id not in prompt_templates:
        raise HTTPException(status_code=404, detail="Template not found")
    return prompt_templates[template_id]

@app.put("/llm/templates/{template_id}")
async def update_prompt_template(template_id: str, template: PromptTemplate):
    """Update a prompt template."""
    if template_id not in prompt_templates:
        raise HTTPException(status_code=404, detail="Template not found")
    template.id = template_id
    prompt_templates[template_id] = template
    return template

@app.delete("/llm/templates/{template_id}")
async def delete_prompt_template(template_id: str):
    """Delete a prompt template."""
    if template_id not in prompt_templates:
        raise HTTPException(status_code=404, detail="Template not found")
    del prompt_templates[template_id]
    return {"status": "success"}

@app.post("/llm/fallback/configure")
async def configure_fallback(config: FallbackConfig):
    """Configure fallback behavior for a model."""
    fallback_configs[config.primary_model] = config
    return config

@app.get("/llm/fallback/{model_name}")
async def get_fallback_config(model_name: str):
    """Get fallback configuration for a model."""
    if model_name not in fallback_configs:
        raise HTTPException(status_code=404, detail="Fallback configuration not found")
    return fallback_configs[model_name] 