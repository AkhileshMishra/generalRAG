from typing import List, Tuple, Optional
import base64
import httpx

class ContextPacker:
    """Packs retrieved elements into LLM context with multimodal support."""
    
    MAX_CONTEXT_TOKENS = 100000  # Gemini 1.5 Pro context window
    MAX_IMAGES = 10
    
    def pack(
        self, 
        results: List[dict],
        max_elements: int = 15
    ) -> Tuple[str, List[dict]]:
        """
        Pack retrieval results into context string and image crops.
        
        Returns:
            - context: Formatted text context for LLM
            - image_crops: List of {uri, base64, element_id} for multimodal
        """
        context_parts = []
        image_crops = []
        
        for i, result in enumerate(results[:max_elements]):
            element_type = result.get("element_type", "text")
            
            # Build citation reference
            citation_ref = f"[{i+1}] (Doc: {result['doc_id']}, Page: {result['page_number']})"
            
            if element_type == "text":
                # Use parent_context for broader context
                text = result.get("parent_context") or result.get("content_text", "")
                context_parts.append(f"{citation_ref}\n{text}\n")
                
            elif element_type == "table":
                # Include table HTML for structured data
                table_html = result.get("table_html", "")
                caption = result.get("content_text", "")
                context_parts.append(
                    f"{citation_ref} [TABLE]\n"
                    f"Caption: {caption}\n"
                    f"Content:\n{table_html}\n"
                )
                # Also include image crop for visual verification
                if result.get("crop_uri") and len(image_crops) < self.MAX_IMAGES:
                    image_crops.append({
                        "uri": result["crop_uri"],
                        "element_id": result["element_id"],
                        "type": "table"
                    })
                    
            elif element_type == "figure":
                # Include dense caption
                caption = result.get("figure_caption") or result.get("content_text", "")
                context_parts.append(
                    f"{citation_ref} [FIGURE]\n"
                    f"Description: {caption}\n"
                )
                # Include image crop for visual verification
                if result.get("crop_uri") and len(image_crops) < self.MAX_IMAGES:
                    image_crops.append({
                        "uri": result["crop_uri"],
                        "element_id": result["element_id"],
                        "type": "figure"
                    })
        
        context = "\n---\n".join(context_parts)
        return context, image_crops
    
    async def load_image_bytes(self, crops: List[dict]) -> List[dict]:
        """Load image bytes from GCS URIs for multimodal LLM."""
        loaded = []
        async with httpx.AsyncClient() as client:
            for crop in crops:
                uri = crop["uri"]
                if uri.startswith("gs://"):
                    # Convert to signed URL or use GCS client
                    # For now, assume accessible via HTTP
                    pass
                elif uri.startswith("http"):
                    resp = await client.get(uri)
                    if resp.status_code == 200:
                        crop["base64"] = base64.b64encode(resp.content).decode()
                        loaded.append(crop)
        return loaded

    def format_system_prompt(self) -> str:
        """System prompt for RAG generation."""
        return """You are a helpful assistant answering questions about documents.
        
Use the provided context to answer questions accurately. When referencing information:
- Cite sources using [N] notation matching the context references
- For tables, verify data against both the HTML and image if provided
- For figures/diagrams, describe what you see and reference the caption
- If information is not in the context, say so clearly

Be precise and factual. Quote specific text when relevant."""
