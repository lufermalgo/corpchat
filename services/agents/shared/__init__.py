"""
Shared utilities for ADK agents.

Incluye clientes, utilidades y tools para los agentes especialistas.
"""

__version__ = "1.0.0"

from .firestore_client import FirestoreClient
from .bigquery_vector_search import BigQueryVectorSearch
from .utils import get_env_var

# Importar tools
from .tools import (
    search_knowledge_base,
    read_corporate_document,
    list_corporate_documents,
    query_product_catalog,
    get_product_pricing,
    generate_quote
)

__all__ = [
    'FirestoreClient',
    'BigQueryVectorSearch',
    'get_env_var',
    'search_knowledge_base',
    'read_corporate_document',
    'list_corporate_documents',
    'query_product_catalog',
    'get_product_pricing',
    'generate_quote'
]

