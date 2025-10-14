"""
Sheets Tool - Herramienta para leer Google Sheets.

Proporciona endpoints OpenAPI para que los agentes ADK lean catálogos y datos tabulares.
"""

import logging
import os
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from fastapi import FastAPI, HTTPException, Header
from pydantic import BaseModel
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google.cloud import logging as cloud_logging
from cachetools import TTLCache

# Configurar logging
cloud_logging.Client().setup_logging()
_logger = logging.getLogger(__name__)

# Variables de entorno
PROJECT_ID = os.getenv("PROJECT_ID", "genai-385616")

# FastAPI app
app = FastAPI(
    title="CorpChat Sheets Tool",
    description="Herramienta para leer Google Sheets",
    version="1.0.0"
)

# Cache en memoria (TTL 5 minutos)
cache = TTLCache(maxsize=100, ttl=300)

# Cliente Google Sheets (lazy initialization)
sheets_service = None


def get_sheets_service():
    """Obtiene el servicio de Google Sheets."""
    global sheets_service
    
    if sheets_service is None:
        # Usar Application Default Credentials (Workload Identity en Cloud Run)
        try:
            sheets_service = build('sheets', 'v4')
            _logger.info("Google Sheets service inicializado")
        except Exception as e:
            _logger.error(f"Error inicializando Sheets service: {e}")
            raise
    
    return sheets_service


# Modelos Pydantic
class ReadRangeRequest(BaseModel):
    """Request para leer un rango de una sheet."""
    spreadsheet_id: str
    range_name: str  # Ej: "Sheet1!A1:C10"
    user_id: Optional[str] = None


class ReadRangeResponse(BaseModel):
    """Response con los datos del rango."""
    values: List[List[Any]]
    spreadsheet_id: str
    range_name: str
    row_count: int
    column_count: int


class SearchRequest(BaseModel):
    """Request para buscar en una sheet."""
    spreadsheet_id: str
    sheet_name: str
    search_term: str
    column: Optional[str] = None  # Ej: "A" para buscar solo en columna A
    user_id: Optional[str] = None


class SearchResponse(BaseModel):
    """Response con resultados de búsqueda."""
    results: List[Dict[str, Any]]
    spreadsheet_id: str
    search_term: str
    match_count: int


def extract_user_from_header(header_value: Optional[str]) -> str:
    """Extrae user ID desde header IAP."""
    if not header_value:
        return "anonymous"
    if ":" in header_value:
        return header_value.split(":")[-1]
    return header_value


def get_cached_range(spreadsheet_id: str, range_name: str) -> Optional[List[List[Any]]]:
    """Obtiene un rango desde el cache."""
    cache_key = f"{spreadsheet_id}:{range_name}"
    return cache.get(cache_key)


def set_cached_range(spreadsheet_id: str, range_name: str, values: List[List[Any]]) -> None:
    """Guarda un rango en el cache."""
    cache_key = f"{spreadsheet_id}:{range_name}"
    cache[cache_key] = values


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "service": "corpchat-sheets-tool",
        "version": "1.0.0",
        "status": "healthy"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/read-range", response_model=ReadRangeResponse)
async def read_range(
    request: ReadRangeRequest,
    x_goog_authenticated_user_email: Optional[str] = Header(None)
):
    """
    Lee un rango de una Google Sheet.
    
    Args:
        request: Request con spreadsheet_id y range_name
        x_goog_authenticated_user_email: Header de IAP
    
    Returns:
        Datos del rango
    """
    try:
        user_id = extract_user_from_header(x_goog_authenticated_user_email)
        if request.user_id:
            user_id = request.user_id
        
        # Intentar obtener del cache
        cached_values = get_cached_range(request.spreadsheet_id, request.range_name)
        if cached_values is not None:
            _logger.info(f"Cache hit: {request.spreadsheet_id}:{request.range_name}")
            return ReadRangeResponse(
                values=cached_values,
                spreadsheet_id=request.spreadsheet_id,
                range_name=request.range_name,
                row_count=len(cached_values),
                column_count=len(cached_values[0]) if cached_values else 0
            )
        
        # Leer desde Google Sheets
        service = get_sheets_service()
        result = service.spreadsheets().values().get(
            spreadsheetId=request.spreadsheet_id,
            range=request.range_name
        ).execute()
        
        values = result.get('values', [])
        
        # Guardar en cache
        set_cached_range(request.spreadsheet_id, request.range_name, values)
        
        _logger.info(
            f"Rango leído: {request.spreadsheet_id}:{request.range_name} por {user_id}",
            extra={
                "user_id": user_id,
                "spreadsheet_id": request.spreadsheet_id,
                "range": request.range_name
            }
        )
        
        return ReadRangeResponse(
            values=values,
            spreadsheet_id=request.spreadsheet_id,
            range_name=request.range_name,
            row_count=len(values),
            column_count=len(values[0]) if values else 0
        )
    
    except HttpError as e:
        _logger.error(f"Error de Google Sheets API: {e}")
        if e.resp.status == 404:
            raise HTTPException(status_code=404, detail="Spreadsheet o rango no encontrado")
        elif e.resp.status == 403:
            raise HTTPException(status_code=403, detail="Acceso denegado al spreadsheet")
        else:
            raise HTTPException(status_code=500, detail=str(e))
    
    except Exception as e:
        _logger.error(f"Error leyendo rango: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/search", response_model=SearchResponse)
async def search_sheet(
    request: SearchRequest,
    x_goog_authenticated_user_email: Optional[str] = Header(None)
):
    """
    Busca un término en una Google Sheet.
    
    Args:
        request: Request con búsqueda
        x_goog_authenticated_user_email: Header de IAP
    
    Returns:
        Resultados de búsqueda
    """
    try:
        user_id = extract_user_from_header(x_goog_authenticated_user_email)
        if request.user_id:
            user_id = request.user_id
        
        # Leer toda la sheet
        service = get_sheets_service()
        result = service.spreadsheets().values().get(
            spreadsheetId=request.spreadsheet_id,
            range=request.sheet_name
        ).execute()
        
        values = result.get('values', [])
        
        # Buscar en los datos
        results = []
        search_term_lower = request.search_term.lower()
        
        for row_idx, row in enumerate(values):
            for col_idx, cell in enumerate(row):
                cell_str = str(cell).lower()
                
                # Si se especificó una columna, filtrar
                if request.column:
                    col_letter = chr(65 + col_idx)  # A=65 en ASCII
                    if col_letter != request.column.upper():
                        continue
                
                if search_term_lower in cell_str:
                    results.append({
                        "row": row_idx + 1,  # 1-indexed
                        "column": chr(65 + col_idx),
                        "value": cell,
                        "row_data": row
                    })
        
        _logger.info(
            f"Búsqueda en sheet: {request.spreadsheet_id}, term={request.search_term}, matches={len(results)}",
            extra={"user_id": user_id, "spreadsheet_id": request.spreadsheet_id}
        )
        
        return SearchResponse(
            results=results,
            spreadsheet_id=request.spreadsheet_id,
            search_term=request.search_term,
            match_count=len(results)
        )
    
    except HttpError as e:
        _logger.error(f"Error de Google Sheets API: {e}")
        if e.resp.status == 404:
            raise HTTPException(status_code=404, detail="Spreadsheet no encontrado")
        elif e.resp.status == 403:
            raise HTTPException(status_code=403, detail="Acceso denegado")
        else:
            raise HTTPException(status_code=500, detail=str(e))
    
    except Exception as e:
        _logger.error(f"Error en búsqueda: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/info/{spreadsheet_id}")
async def get_spreadsheet_info(
    spreadsheet_id: str,
    x_goog_authenticated_user_email: Optional[str] = Header(None)
):
    """
    Obtiene información de un spreadsheet.
    
    Args:
        spreadsheet_id: ID del spreadsheet
        x_goog_authenticated_user_email: Header de IAP
    
    Returns:
        Información del spreadsheet
    """
    try:
        user_id = extract_user_from_header(x_goog_authenticated_user_email)
        
        service = get_sheets_service()
        spreadsheet = service.spreadsheets().get(
            spreadsheetId=spreadsheet_id
        ).execute()
        
        sheets = []
        for sheet in spreadsheet.get('sheets', []):
            props = sheet.get('properties', {})
            sheets.append({
                "title": props.get('title'),
                "sheet_id": props.get('sheetId'),
                "index": props.get('index'),
                "row_count": props.get('gridProperties', {}).get('rowCount'),
                "column_count": props.get('gridProperties', {}).get('columnCount')
            })
        
        info = {
            "spreadsheet_id": spreadsheet_id,
            "title": spreadsheet.get('properties', {}).get('title'),
            "locale": spreadsheet.get('properties', {}).get('locale'),
            "sheets": sheets,
            "sheet_count": len(sheets)
        }
        
        _logger.info(
            f"Info de spreadsheet: {spreadsheet_id} por {user_id}",
            extra={"user_id": user_id, "spreadsheet_id": spreadsheet_id}
        )
        
        return info
    
    except HttpError as e:
        _logger.error(f"Error de Google Sheets API: {e}")
        if e.resp.status == 404:
            raise HTTPException(status_code=404, detail="Spreadsheet no encontrado")
        elif e.resp.status == 403:
            raise HTTPException(status_code=403, detail="Acceso denegado")
        else:
            raise HTTPException(status_code=500, detail=str(e))
    
    except Exception as e:
        _logger.error(f"Error obteniendo info: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)

