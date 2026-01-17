"""
Vespa Query Builder

Builds YQL queries with QUERY-TIME access control filtering.
All access control is enforced in Vespa, NOT post-filtering in FastAPI.
"""
from typing import Optional, Tuple, List
from shared.config.settings import get_config

config = get_config()

class VespaQueryBuilder:
    """
    Builds Vespa YQL queries with query-time access control.
    
    Access control is enforced via Vespa filter constraints on:
    - tenant_id: Multi-tenant isolation (future-proof)
    - workspace_id: Workspace isolation within tenant
    - access_scope: 'global' or 'private'
    - owner_user_id: Owner for private docs
    
    These are ALL filterable attributes in Vespa schema (fast-search, exact match).
    """
    
    def build_rag_query(
        self,
        query_text: str,
        user_id: Optional[str] = None,
        tenant_id: str = None,
        workspace_id: str = None,
        include_global: bool = True,
        limit: int = None
    ) -> Tuple[str, dict]:
        """
        Build YQL query with Vespa-native access control filtering.
        
        Access control (ALL enforced in Vespa, not post-filter):
        - tenant_id filter (exact match)
        - workspace_id filter (exact match)  
        - Global docs (access_scope='global') visible to all in workspace
        - Private docs (access_scope='private') only visible to owner_user_id
        """
        tenant_id = tenant_id or config.default_tenant_id
        workspace_id = workspace_id or config.default_workspace_id
        limit = limit or config.vespa.default_hits
        
        # Build access control filter - ALL done in Vespa
        access_parts = []
        if include_global:
            access_parts.append("access_scope = 'global'")
        if user_id:
            access_parts.append(f"(access_scope = 'private' AND owner_user_id = '{user_id}')")
        
        access_filter = " OR ".join(access_parts) if access_parts else "access_scope = 'global'"
        
        # Full YQL with tenant isolation + access control
        yql = f"""
            select * from sop_elements where 
            tenant_id = '{tenant_id}' AND
            workspace_id = '{workspace_id}' AND
            ({access_filter}) AND 
            (userQuery() OR {{targetHits:{config.vespa.target_hits_dense}}}nearestNeighbor(embedding, query_embedding))
            limit {limit}
        """
        
        ranking_features = {
            "query": query_text,
            "ranking.profile": config.vespa.default_profile,
            "timeout": f"{config.vespa.query_timeout_ms}ms"
        }
        
        return yql.strip(), ranking_features
    
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
        """Build hybrid BM25 + dense query with Vespa-native filters."""
        tenant_id = tenant_id or config.default_tenant_id
        workspace_id = workspace_id or config.default_workspace_id
        limit = limit or config.vespa.default_hits
        
        conditions = [
            f"tenant_id = '{tenant_id}'",
            f"workspace_id = '{workspace_id}'"
        ]
        
        # Access control - enforced in Vespa
        if user_id:
            conditions.append(
                f"(access_scope = 'global' OR "
                f"(access_scope = 'private' AND owner_user_id = '{user_id}'))"
            )
        else:
            conditions.append("access_scope = 'global'")
        
        # Optional filters
        if doc_ids:
            doc_filter = " OR ".join([f"doc_id = '{d}'" for d in doc_ids])
            conditions.append(f"({doc_filter})")
        
        if element_types:
            type_filter = " OR ".join([f"element_type = '{t}'" for t in element_types])
            conditions.append(f"({type_filter})")
        
        where_clause = " AND ".join(conditions)
        
        yql = f"""
            select * from sop_elements where 
            {where_clause} AND
            (userQuery() OR {{targetHits:{config.vespa.target_hits_colbert}}}nearestNeighbor(embedding, query_embedding))
            limit {limit}
        """
        
        return yql.strip(), {
            "query": query_text, 
            "ranking.profile": config.vespa.hybrid_profile,
            "ranking.rerankCount": config.vespa.rerank_count
        }
    
    def build_citation_lookup(
        self, 
        doc_id: str, 
        element_id: str,
        tenant_id: str = None,
        workspace_id: str = None
    ) -> str:
        """Build query to fetch specific element for citation."""
        tenant_id = tenant_id or config.default_tenant_id
        workspace_id = workspace_id or config.default_workspace_id
        
        return f"""
            select * from sop_elements where 
            tenant_id = '{tenant_id}' AND
            workspace_id = '{workspace_id}' AND
            doc_id = '{doc_id}' AND 
            element_id = '{element_id}'
            limit 1
        """
    
    def build_user_docs_query(
        self,
        user_id: str,
        tenant_id: str = None,
        workspace_id: str = None
    ) -> str:
        """Query all private docs for a user (for listing/deletion)."""
        tenant_id = tenant_id or config.default_tenant_id
        workspace_id = workspace_id or config.default_workspace_id
        
        return f"""
            select doc_id, element_id from sop_elements where
            tenant_id = '{tenant_id}' AND
            workspace_id = '{workspace_id}' AND
            access_scope = 'private' AND
            owner_user_id = '{user_id}'
        """
