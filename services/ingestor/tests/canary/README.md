# Dataset Canario - CorpChat Ingestor

Este directorio contiene documentos de prueba para validar el pipeline de ingesta completo.

## Documentos de Prueba

### 1. PDF Simple (test_doc_1.pdf)
- **Propósito**: Validar extracción básica de texto
- **Contenido**: 2 páginas de texto simple
- **Validaciones**:
  - Extracción de texto por página
  - Preservación de saltos de línea
  - Chunking correcto

### 2. PDF con Tabla (test_doc_2.pdf)
- **Propósito**: Validar detección y extracción de tablas
- **Contenido**: 1 página con tabla estructurada
- **Validaciones**:
  - Detección de tabla
  - Headers correctos
  - Rows completas
  - Formato de tabla preservado

### 3. Excel con Merged Cells (test_doc_3.xlsx)
- **Propósito**: Validar manejo de celdas combinadas
- **Contenido**: 2 hojas con merged cells
- **Validaciones**:
  - Detección de merged cells
  - Múltiples hojas
  - Headers normalizados

### 4. Word con Encabezados (test_doc_4.docx)
- **Propósito**: Validar jerarquía de encabezados
- **Contenido**: Documento con H1, H2, H3
- **Validaciones**:
  - Detección de encabezados
  - Niveles correctos
  - Tablas en DOCX

### 5. Imagen con Texto (test_doc_5.png)
- **Propósito**: Validar OCR
- **Contenido**: Screenshot con texto legible
- **Validaciones**:
  - OCR funcional
  - Confidence > 50%
  - Texto reconocible

## Uso

### Tests Unitarios
```bash
cd services/ingestor
pytest tests/test_extractors.py -v
```

### Test Pipeline Completo
```bash
pytest tests/test_pipeline_e2e.py -v
```

## Criterios de Éxito

- ✅ Extraction success rate >= 90%
- ✅ Table detection accuracy >= 80%
- ✅ Embedding generation < 2s per chunk
- ✅ Pipeline E2E completa sin errores

