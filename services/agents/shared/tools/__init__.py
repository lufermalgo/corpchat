"""
Tools compartidos para agentes ADK de CorpChat.

Este módulo contiene herramientas (Tools) que pueden ser utilizadas
por los agentes especialistas para realizar tareas específicas.
"""

from .knowledge_search_tool import search_knowledge_base
from .docs_tool_wrapper import read_corporate_document, list_corporate_documents
from .sheets_tool_wrapper import query_product_catalog, get_product_pricing, generate_quote

__all__ = [
    "search_knowledge_base",
    "read_corporate_document",
    "list_corporate_documents",
    "query_product_catalog",
    "get_product_pricing",
    "generate_quote"
]

