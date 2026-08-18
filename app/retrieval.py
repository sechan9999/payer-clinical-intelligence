import math
import re
from typing import Dict, List, Optional, Tuple
from app.domain import DocumentRecord, DomainDomain, UserIdentity, UserRole
from app.store import DataStore, get_store


def _build_term_vector(text: str) -> Dict[str, float]:
    """
    Computes term-frequency (TF) vector for text, normalized for length.
    """
    words = re.findall(r"\w+", text.lower())
    if not words:
        return {}
    
    freqs = {}
    for w in words:
        freqs[w] = freqs.get(w, 0.0) + 1.0
        
    norm = math.sqrt(sum(v * v for v in freqs.values()))
    if norm == 0:
        return {}
    
    return {w: v / norm for w, v in freqs.items()}


def compute_cosine_similarity(query_vec: Dict[str, float], doc_vec: Dict[str, float]) -> float:
    """
    Computes cosine similarity dot product between normalized term vectors.
    """
    if not query_vec or not doc_vec:
        return 0.0
    
    dot_product = 0.0
    for term, val in query_vec.items():
        if term in doc_vec:
            dot_product += val * doc_vec[term]
            
    return dot_product


def semantic_rank_documents(query: str, documents: List[DocumentRecord]) -> List[Tuple[DocumentRecord, float]]:
    """
    Ranks permitted documents using vector cosine similarity.
    Filtering MUST run before ranking (SQL Security Predicate -> Semantic Cosine Similarity).
    """
    if not documents:
        return []
    
    query_vec = _build_term_vector(query)
    ranked = []
    
    for doc in documents:
        # Combined document text representation (Title + Summary + Content + Codes)
        doc_text = f"{doc.title} {doc.summary} {doc.content} {' '.join(doc.cpt_codes)} {' '.join(doc.icd10_codes)}"
        doc_vec = _build_term_vector(doc_text)
        sim_score = compute_cosine_similarity(query_vec, doc_vec)
        
        # Boost for CPT/ICD10 code exact matches in query
        for cpt in doc.cpt_codes:
            if cpt.lower() in query.lower():
                sim_score += 0.5
        for icd in doc.icd10_codes:
            if icd.lower() in query.lower():
                sim_score += 0.5
                
        ranked.append((doc, sim_score))

    # Sort descending by semantic similarity score
    ranked.sort(key=lambda x: x[1], reverse=True)
    return ranked


def permitted_documents(
    user_identity: UserIdentity,
    query_text: str,
    domain_filter: Optional[DomainDomain] = None,
    store: Optional[DataStore] = None,
) -> Tuple[List[DocumentRecord], Optional[str]]:
    """
    Two-Stage Retrieval Pipeline:
    Stage 1: SECURITY PRE-FILTERING IN SQL (WHERE allowed_roles LIKE %role%)
    Stage 2: SEMANTIC COSINE SIMILARITY RANKING (vector cosine similarity over permitted candidates only)
    """
    db = store or get_store()
    
    # STAGE 1: SQL Pre-filtering (Security Boundary)
    role = user_identity.role
    all_permitted = db.get_documents_by_roles([role])

    # Optional domain filter
    if domain_filter:
        all_permitted = [d for d in all_permitted if d.domain == domain_filter]

    if not all_permitted:
        # Check if documents exist in target domain that were blocked by RBAC
        all_domain_docs = [d for d in db.get_documents_by_roles([UserRole.PAYER_ADMIN, UserRole.CLINICIAN, UserRole.MEDICAL_DIRECTOR]) if not domain_filter or d.domain == domain_filter]
        if all_domain_docs:
            return [], f"Access Denied: User role '{role.value}' is restricted from accessing documents in '{domain_filter or 'all'}' domain."
        return [], "No documents found."

    # STAGE 2: Semantic Cosine Similarity Ranking (Quality Layer)
    ranked_docs = semantic_rank_documents(query_text, all_permitted)
    
    # Extract top permitted documents
    top_docs = [doc for doc, score in ranked_docs]
    return top_docs, None
