"""
Search engine with configurable backends.
Advanced search features are conditionally available.
"""

import logging
from typing import List, Dict, Any
from feature_flags import has_advanced_search

logger = logging.getLogger(__name__)


class SearchResult:
    """Represents a search result."""

    def __init__(self, doc_id: int, title: str, score: float, snippet: str = ""):
        self.doc_id = doc_id
        self.title = title
        self.score = score
        self.snippet = snippet

    def __repr__(self):
        return f"SearchResult(id={self.doc_id}, title='{self.title}', score={self.score})"


class BasicSearchEngine:
    """Basic search engine (always available)."""

    def __init__(self):
        self.documents = {}
        logger.info("Basic search engine initialized")

    def index_document(self, doc_id: int, title: str, content: str):
        """Index a document for searching."""
        self.documents[doc_id] = {'title': title, 'content': content}
        logger.debug(f"Document indexed: {doc_id}")

    def search(self, query: str) -> List[SearchResult]:
        """Perform basic search."""
        results = []

        for doc_id, doc in self.documents.items():
            if query.lower() in doc['title'].lower() or query.lower() in doc['content'].lower():
                # Simple scoring based on title match
                score = 1.0 if query.lower() in doc['title'].lower() else 0.5
                results.append(SearchResult(doc_id, doc['title'], score))

        results.sort(key=lambda r: r.score, reverse=True)
        return results


# Conditionally define advanced search only if feature is enabled
if has_advanced_search():
    logger.info("Advanced search is enabled, defining advanced search functions")

    def fuzzy_search(engine: BasicSearchEngine, query: str, threshold: float = 0.7) -> List[SearchResult]:
        """
        Perform fuzzy search with similarity matching.
        Only available when advanced search is enabled.
        """
        logger.info(f"Performing fuzzy search: {query}")

        results = []

        for doc_id, doc in engine.documents.items():
            # Simulate fuzzy matching
            title_similarity = _calculate_similarity(query, doc['title'])
            content_similarity = _calculate_similarity(query, doc['content'])

            max_similarity = max(title_similarity, content_similarity)

            if max_similarity >= threshold:
                snippet = _extract_snippet(doc['content'], query)
                results.append(SearchResult(doc_id, doc['title'], max_similarity, snippet))

        results.sort(key=lambda r: r.score, reverse=True)
        return results

    def _calculate_similarity(text1: str, text2: str) -> float:
        """Calculate similarity between two strings."""
        # Simplified similarity calculation
        text1_lower = text1.lower()
        text2_lower = text2.lower()

        if text1_lower == text2_lower:
            return 1.0

        # Count matching words
        words1 = set(text1_lower.split())
        words2 = set(text2_lower.split())

        if not words1 or not words2:
            return 0.0

        intersection = words1.intersection(words2)
        union = words1.union(words2)

        return len(intersection) / len(union)

    def _extract_snippet(content: str, query: str, context: int = 50) -> str:
        """Extract a relevant snippet from content."""
        query_lower = query.lower()
        content_lower = content.lower()

        pos = content_lower.find(query_lower)

        if pos == -1:
            return content[:100] + "..." if len(content) > 100 else content

        start = max(0, pos - context)
        end = min(len(content), pos + len(query) + context)

        snippet = content[start:end]

        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."

        return snippet

else:
    logger.info("Advanced search is disabled, fuzzy_search will not be available")


class SearchService:
    """High-level search service."""

    def __init__(self):
        self.engine = BasicSearchEngine()
        logger.info("Search service initialized")

    def index(self, doc_id: int, title: str, content: str):
        """Index a document."""
        self.engine.index_document(doc_id, title, content)

    def basic_search(self, query: str) -> List[SearchResult]:
        """Perform basic search."""
        return self.engine.search(query)

    def advanced_search(self, query: str, fuzzy: bool = True, threshold: float = 0.7) -> List[SearchResult]:
        """Perform advanced search with fuzzy matching."""
        if fuzzy:
            # This will fail if advanced search is not enabled
            return fuzzy_search(self.engine, query, threshold)
        else:
            return self.basic_search(query)
