"""Search service for unified dataset search."""

from mldata.models.dataset import SearchResult


class SearchService:
    """Service for searching datasets across sources."""

    def __init__(self):
        """Initialize search service."""
        pass

    async def search(
        self,
        query: str,
        sources: list[str] | None = None,
        limit: int = 20,
        modality: str | None = None,
        task: str | None = None,
    ) -> list[SearchResult]:
        """Search across multiple sources.

        Args:
            query: Search query
            sources: List of sources to search (None for all)
            limit: Maximum results per source
            modality: Filter by modality
            task: Filter by task

        Returns:
            Aggregated search results
        """
        from mldata.connectors import HuggingFaceConnector, KaggleConnector, OpenMLConnector

        results = []

        if sources is None:
            sources = ["huggingface", "kaggle", "openml"]

        # Search each source
        if "huggingface" in sources:
            try:
                connector = HuggingFaceConnector()
                hf_results = await connector.search(query, limit=limit, modality=modality, task=task)
                results.extend(hf_results)
            except Exception:
                pass

        if "kaggle" in sources:
            try:
                connector = KaggleConnector()
                kg_results = await connector.search(query, limit=limit, modality=modality, task=task)
                results.extend(kg_results)
            except Exception:
                pass

        if "openml" in sources:
            try:
                connector = OpenMLConnector()
                om_results = await connector.search(query, limit=limit, modality=modality, task=task)
                results.extend(om_results)
            except Exception:
                pass

        return results
