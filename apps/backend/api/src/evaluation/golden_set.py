"""
Evaluation Module for RAG Quality Testing

Provides golden set testing and retrieval quality metrics.
"""
import json
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import asyncio

from shared.clients.vespa_client import VespaClient


@dataclass
class GoldenQuery:
    query_id: str
    query: str
    expected_doc_ids: List[str]
    expected_answer_contains: List[str]
    tags: List[str] = None


@dataclass
class EvalResult:
    query_id: str
    recall_at_5: float
    recall_at_10: float
    mrr: float
    answer_coverage: float
    latency_ms: float


class GoldenSetEvaluator:
    """Evaluates retrieval quality against golden set."""
    
    def __init__(self, vespa_client: VespaClient):
        self.vespa = vespa_client
    
    async def evaluate(
        self,
        golden_set: List[GoldenQuery],
        tenant_id: str,
        user_id: str = None
    ) -> Dict:
        """
        Run evaluation against golden set.
        
        Returns aggregate metrics and per-query results.
        """
        results = []
        
        for gq in golden_set:
            start = datetime.now()
            
            # Run retrieval
            hits = await self.vespa.hybrid_search(
                query=gq.query,
                tenant_id=tenant_id,
                user_id=user_id,
                limit=10
            )
            
            latency = (datetime.now() - start).total_seconds() * 1000
            retrieved_ids = [h["doc_id"] for h in hits]
            
            # Calculate metrics
            recall_5 = self._recall_at_k(gq.expected_doc_ids, retrieved_ids[:5])
            recall_10 = self._recall_at_k(gq.expected_doc_ids, retrieved_ids)
            mrr = self._mrr(gq.expected_doc_ids, retrieved_ids)
            
            results.append(EvalResult(
                query_id=gq.query_id,
                recall_at_5=recall_5,
                recall_at_10=recall_10,
                mrr=mrr,
                answer_coverage=0.0,  # Requires LLM call
                latency_ms=latency
            ))
        
        return {
            "timestamp": datetime.now().isoformat(),
            "num_queries": len(golden_set),
            "avg_recall_at_5": sum(r.recall_at_5 for r in results) / len(results),
            "avg_recall_at_10": sum(r.recall_at_10 for r in results) / len(results),
            "avg_mrr": sum(r.mrr for r in results) / len(results),
            "avg_latency_ms": sum(r.latency_ms for r in results) / len(results),
            "per_query": [asdict(r) for r in results]
        }
    
    def _recall_at_k(self, expected: List[str], retrieved: List[str]) -> float:
        if not expected:
            return 1.0
        hits = len(set(expected) & set(retrieved))
        return hits / len(expected)
    
    def _mrr(self, expected: List[str], retrieved: List[str]) -> float:
        for i, doc_id in enumerate(retrieved):
            if doc_id in expected:
                return 1.0 / (i + 1)
        return 0.0
    
    def load_golden_set(self, path: str) -> List[GoldenQuery]:
        """Load golden set from JSON file."""
        with open(path) as f:
            data = json.load(f)
        return [GoldenQuery(**q) for q in data["queries"]]
    
    def save_results(self, results: Dict, path: str):
        """Save evaluation results to JSON."""
        with open(path, "w") as f:
            json.dump(results, f, indent=2)
