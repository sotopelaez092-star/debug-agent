"""
Data loading utilities.
"""

from typing import List, Dict, Any


def load_sample_documents() -> List[Dict[str, Any]]:
    """Load sample documents for testing."""
    return [
        {
            'id': 1,
            'title': 'Introduction to Python',
            'content': 'Python is a high-level programming language known for its simplicity and readability. It supports multiple programming paradigms.'
        },
        {
            'id': 2,
            'title': 'Advanced Python Techniques',
            'content': 'Learn about decorators, generators, context managers, and metaclasses in Python. These advanced features make Python powerful.'
        },
        {
            'id': 3,
            'title': 'Machine Learning with Python',
            'content': 'Python is the most popular language for machine learning. Libraries like scikit-learn, TensorFlow, and PyTorch make it easy.'
        },
        {
            'id': 4,
            'title': 'Web Development with Django',
            'content': 'Django is a high-level Python web framework that encourages rapid development and clean, pragmatic design.'
        },
        {
            'id': 5,
            'title': 'Data Science Tools',
            'content': 'Pandas, NumPy, and Matplotlib are essential tools for data science in Python. They provide powerful data manipulation capabilities.'
        },
    ]


def format_search_results(results: List) -> str:
    """Format search results for display."""
    if not results:
        return "No results found."

    output = []
    output.append(f"\nFound {len(results)} results:")
    output.append("-" * 60)

    for i, result in enumerate(results, 1):
        output.append(f"\n{i}. {result.title} (score: {result.score:.2f})")
        if hasattr(result, 'snippet') and result.snippet:
            output.append(f"   {result.snippet}")

    return "\n".join(output)
