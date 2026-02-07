"""
Vespa Query Builder

Builds YQL queries with QUERY-TIME access control filtering.
All access control is enforced in Vespa, NOT post-filtering in FastAPI.
"""
from typing import Optional, Tuple, List
from shared.config.settings import get_config

config = get_config()

def _eq(field: str, value: str) -> str:
    """String equality filter for Vespa YQL."""
    return f"{field} contains '{value}'"

class VespaQueryBuilder:
    
    def build_rag_query(
        self,
        query_text: str,
        user_id: Optional[str] = None,
        tenant_id: str = None,
        workspace_id: str = None,
        include_global: bool = True,
        limit: int = None
    ) -> Tuple[str, dict]:
        tenant_id = tenant_id or config.default_tenant_id
        workspace_id = workspace_id or config.default_workspace_id
        limit = limit or config.vespa.default_hits
        
        access_parts = []
        if include_global:
            access_parts.append(_eq("access_scope", "global"))
        if user_id:
            access_parts.append(f"({_eq('access_scope', 'private')} AND {_eq('owner_user_id', user_id)})")
        
        access_filter = " OR ".join(access_parts) if access_parts else _eq("access_scope", "global")
        
        yql = (
            f"select * from sop_elements where "
            f"{_eq('tenant_id', tenant_id)} AND "
            f"{_eq('workspace_id', workspace_id)} AND "
            f"({access_filter}) AND "
            f"(userQuery() OR ({{targetHits:{config.vespa.target_hits_dense}}}nearestNeighbor(embedding, query_embedding))) "
            f"limit {limit}"
        )
        
        return yql, {
            "query": query_text,
            "ranking.profile": config.vespa.default_profile,
            "timeout": f"{config.vespa.query_timeout_ms}ms"
        }
    
    def build_hybrid_query(
        self,
        query_text: str,
        user_id: Optional[str] = None,
        tenant_id: str = None,
        workspace_id: str = None,
        doc_ids: Optional[List[str]] = None,
        element_types: Optional[List[str]] = None,
        limit: int = None
    ) -> Tuple[str, dict]:
        tenant_id = tenant_id or config.default_tenant_id
        workspace_id = workspace_id or config.default_workspace_id
        limit = limit or config.vespa.default_hits
        
        conditions = [_eq("tenant_id", tenant_id), _eq("workspace_id", workspace_id)]
        
        if user_id:
            conditions.append(
                f"({_eq('access_scope', 'global')} OR "
                f"({_eq('access_scope', 'private')} AND {_eq('owner_user_id', user_id)}))"
            )
        else:
            conditions.append(_eq("access_scope", "global"))
        
        if doc_ids:
            conditions.append("(" + " OR ".join([_eq("doc_id", d) for d in doc_ids]) + ")")
        if element_types:
            conditions.append("(" + " OR ".join([_eq("element_type", t) for t in element_types]) + ")")
        
        where_clause = " AND ".join(conditions)
        
        yql = (
            f"select * from sop_elements where "
            f"{where_clause} AND "
            f"(userQuery() OR ({{targetHits:{config.vespa.target_hits_colbert}}}nearestNeighbor(embedding, query_embedding))) "
            f"limit {limit}"
        )
        
        return yql, {
            "query": query_text,
            "ranking.profile": config.vespa.hybrid_profile,
            "ranking.rerankCount": config.vespa.rerank_count
        }
    
    def build_citation_lookup(self, doc_id: str, element_id: str, tenant_id: str = None, workspace_id: str = None) -> str:
        tenant_id = tenant_id or config.default_tenant_id
        workspace_id = workspace_id or config.default_workspace_id
        return (
            f"select * from sop_elements where "
            f"{_eq('tenant_id', tenant_id)} AND {_eq('workspace_id', workspace_id)} AND "
            f"{_eq('doc_id', doc_id)} AND {_eq('element_id', element_id)} limit 1"
        )
    
    def build_user_docs_query(self, user_id: str, tenant_id: str = None, workspace_id: str = None) -> str:
        tenant_id = tenant_id or config.default_tenant_id
        workspace_id = workspace_id or config.default_workspace_id
        return (
            f"select doc_id, element_id from sop_elements where "
            f"{_eq('tenant_id', tenant_id)} AND {_eq('workspace_id', workspace_id)} AND "
            f"{_eq('access_scope', 'private')} AND {_eq('owner_user_id', user_id)}"
        )
