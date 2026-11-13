"""Vendored stdlib-only core of context-palace (models, lake, retrieval).

Upstream: https://github.com/NoJuanNobody/context-palace (commit in VENDORED.json).
Refresh with ``python scripts/vendor_context_palace.py <repo> <commit>``.
"""
from .models import ConceptNode, RelationEdge, compute_text_embedding, cosine_similarity, estimate_tokens
from .lake import ContextLake
from .retrieval import DualDirectionRetriever

__all__ = [
    "ConceptNode",
    "RelationEdge",
    "compute_text_embedding",
    "cosine_similarity",
    "estimate_tokens",
    "ContextLake",
    "DualDirectionRetriever",
]
