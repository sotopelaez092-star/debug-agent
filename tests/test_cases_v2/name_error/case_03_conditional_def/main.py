"""
Main application demonstrating search functionality.
"""

import sys
import logging
from feature_flags import feature_flags
from search_engine import SearchService
from data_loader import load_sample_documents, format_search_results


def setup_logging():
    """Setup logging configuration."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def main():
    """Run the search demo."""
    setup_logging()

    print("=" * 60)
    print("Search Engine Demo")
    print("=" * 60)
    print(f"\nFeature Flags: {feature_flags}")
    print()

    # Initialize search service
    service = SearchService()

    # Load sample data
    documents = load_sample_documents()

    print(f"Indexing {len(documents)} documents...")
    for doc in documents:
        service.index(doc['id'], doc['title'], doc['content'])

    print("✓ Documents indexed successfully\n")

    # Test 1: Basic search
    print("=" * 60)
    print("Test 1: Basic Search")
    print("=" * 60)

    query = "Python"
    print(f"Query: '{query}'")

    results = service.basic_search(query)
    print(format_search_results(results))

    # Test 2: Advanced fuzzy search
    print("\n" + "=" * 60)
    print("Test 2: Advanced Fuzzy Search")
    print("=" * 60)

    query = "machine learning"
    print(f"Query: '{query}'")

    try:
        results = service.advanced_search(query, fuzzy=True, threshold=0.3)
        print(format_search_results(results))
    except Exception as e:
        print(f"✗ Advanced search failed: {e}")
        import traceback
        traceback.print_exc()
        return 1

    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
