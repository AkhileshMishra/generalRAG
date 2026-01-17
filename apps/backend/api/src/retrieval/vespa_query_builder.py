from typing import Optional, Tuple, List
from shared.clients.vespa_client import VespaClient

class VespaQueryBuilder:
    """Builds Vespa YQL queries with access control filtering."""
    
    def build_rag_query(
        self,
        query_text: str,
        user_id: Optional[str] = None,
        include_global: bool = True,
        limit: int = 20
    ) -> Tuple[str, dict]:
        """
        Build YQL query with access scope filtering.
        
        Access control logic:
        - Global docs (access_scope='global') visible to all
        - Private docs (access_scope='private') only visible to owner
        """
        # Build access filter
        access_conditions = []
        if include_global:
            access_conditions.append("access_scope contains 'global'")
        if user_id:
            access_conditions.append(
                f"(access_scope contains 'private' AND owner_user_id contains '{user_id}')"
            )
        
        access_filter = " OR ".join(access_conditions)
        
        yql = f"""
            select * from sop_elements where 
            ({access_filter}) AND 
            (userQuery() OR {{targetHits:100}}nearestNeighbor(embedding, query_embedding))
            limit {limit}
        """
        
        ranking_features = {
            "query": query_text,
            "ranking.profile": "rag"
        }
        
        return yql.strip(), ranking_features
    
    def build_hybrid_query(
        self,
        query_text: str,
        user_id: Optional[str] = None,
        doc_ids: Optional[List[str]] = None,
        element_types: Optional[List[str]] = None,
        limit: int = 50
    ) -> Tuple[str, dict]:
        """Build hybrid BM25 + dense query with optional filters."""
        conditions = []
        
        # Access control
        if user_id:
            conditions.append(
                f"(access_scope contains 'global' OR "
                f"(access_scope contains 'private' AND owner_user_id contains '{user_id}'))"
            )
        else:
            conditions.append("access_scope contains 'global'")
        
        # Optional filters
        if doc_ids:
            doc_filter = " OR ".join([f"doc_id contains '{d}'" for d in doc_ids])
            conditions.append(f"({doc_filter})")
        
        if element_types:
            type_filter = " OR ".join([f"element_type contains '{t}'" for t in element_types])
            conditions.append(f"({type_filter})")
        
        where_clause = " AND ".join(conditions)
        
        yql = f"""
            select * from sop_elements where 
            {where_clause} AND
            (userQuery() OR {{targetHits:200}}nearestNeighbor(embedding, query_embedding))
            limit {limit}
        """
        
        return yql.strip(), {"query": query_text, "ranking.profile": "hybrid"}
    
    def build_citation_lookup(self, doc_id: str, element_id: str) -> str:
        """Build query to fetch specific element for citation."""
        return f"""
            select * from sop_elements where 
            doc_id contains '{doc_id}' AND element_id contains '{element_id}'
            limit 1
        """
