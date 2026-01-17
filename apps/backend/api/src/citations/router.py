import os
from typing import List
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from shared.clients.vespa_client import VespaClient
from src.retrieval.vespa_query_builder import VespaQueryBuilder

router = APIRouter()

class CitationRequest(BaseModel):
    doc_id: str
    element_id: str

class CitationDetail(BaseModel):
    doc_id: str
    element_id: str
    element_type: str
    page_number: int
    bbox: List[float]
    content_text: str
    parent_context: str
    table_html: str | None = None
    figure_caption: str | None = None
    crop_uri: str | None = None

vespa_client = VespaClient(os.getenv("VESPA_ENDPOINT"))
query_builder = VespaQueryBuilder()

@router.get("/{doc_id}/{element_id}", response_model=CitationDetail)
async def get_citation(doc_id: str, element_id: str):
    """Get full citation details for highlighting in UI."""
    yql = query_builder.build_citation_lookup(doc_id, element_id)
    results = await vespa_client.query(yql, {})
    
    if not results:
        raise HTTPException(status_code=404, detail="Citation not found")
    
    r = results[0]
    return CitationDetail(
        doc_id=r["doc_id"],
        element_id=r["element_id"],
        element_type=r["element_type"],
        page_number=r["page_number"],
        bbox=r["bbox"],
        content_text=r["content_text"],
        parent_context=r.get("parent_context", ""),
        table_html=r.get("table_html"),
        figure_caption=r.get("figure_caption"),
        crop_uri=r.get("crop_uri")
    )

@router.get("/page/{doc_id}/{page_number}")
async def get_page_elements(doc_id: str, page_number: int):
    """Get all elements on a specific page for rendering."""
    yql = f"""
        select * from sop_elements where 
        doc_id contains '{doc_id}' AND page_number = {page_number}
        order by bbox[0] asc
    """
    results = await vespa_client.query(yql, {})
    return {"elements": results}
