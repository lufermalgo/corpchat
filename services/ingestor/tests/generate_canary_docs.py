"""
Script para generar documentos canario sintéticos para tests.

Crea documentos de ejemplo en formatos PDF, DOCX, XLSX que pueden
usarse para validar los extractores.
"""

from pathlib import Path


def create_text_files():
    """Crea archivos de texto plano como placeholder."""
    canary_dir = Path(__file__).parent / "canary"
    
    # Crear directorios
    (canary_dir / "pdfs").mkdir(parents=True, exist_ok=True)
    (canary_dir / "docx").mkdir(parents=True, exist_ok=True)
    (canary_dir / "xlsx").mkdir(parents=True, exist_ok=True)
    (canary_dir / "images").mkdir(parents=True, exist_ok=True)
    
    # Crear placeholders de texto
    placeholders = {
        "pdfs/test_simple.txt": """
Manual de Usuario - CorpChat
============================

Capítulo 1: Introducción
-------------------------

CorpChat es una plataforma conversacional corporativa que permite a los
empleados interactuar con información empresarial de forma natural.

Características principales:
- Chat conversacional con IA
- Procesamiento de documentos
- Búsqueda semántica
- Multi-agente especializado

Capítulo 2: Primeros Pasos
---------------------------

Para comenzar a usar CorpChat:

1. Inicia sesión con tu cuenta corporativa
2. Crea un nuevo chat
3. Haz una pregunta o sube un documento
4. Recibe respuestas inteligentes del sistema

El sistema procesará tus documentos automáticamente y los indexará
para búsquedas futuras.
""",
        "pdfs/test_table.txt": """
Reporte de Ventas Q1 2025
=========================

Resumen Ejecutivo
-----------------

Este documento presenta los resultados de ventas del primer trimestre.

Tabla de Ventas por Región:

| Región      | Ventas Q1  | Crecimiento | Target  |
|-------------|------------|-------------|---------|
| Norte       | $125,000   | +15%        | $120,000|
| Sur         | $98,500    | +8%         | $95,000 |
| Este        | $110,200   | +12%        | $105,000|
| Oeste       | $87,300    | +5%         | $85,000 |
| TOTAL       | $421,000   | +10%        | $405,000|

Conclusiones:
- Todas las regiones superaron sus targets
- Crecimiento sostenido en todas las áreas
- Proyección positiva para Q2
""",
        "docx/test_headings.txt": """
Política de Vacaciones 2025
===========================

# 1. Objetivo

Establecer las directrices para el otorgamiento y disfrute de vacaciones.

## 1.1 Alcance

Esta política aplica a todos los empleados permanentes.

## 1.2 Responsables

- RRHH: Administración del proceso
- Supervisores: Aprobación de solicitudes
- Empleados: Solicitud oportuna

# 2. Días de Vacaciones

## 2.1 Asignación Anual

Todos los empleados tienen derecho a 22 días hábiles de vacaciones.

## 2.2 Acumulación

Las vacaciones no utilizadas pueden acumularse hasta 10 días.

# 3. Proceso de Solicitud

## 3.1 Pasos

1. Completar formulario en portal RRHH
2. Obtener aprobación del supervisor
3. Notificar al equipo (2 semanas anticipación)

## 3.2 Excepciones

Casos especiales requieren aprobación de Gerencia.
""",
        "xlsx/test_merged_cells.txt": """
Catálogo de Productos 2025
==========================

Hoja 1: Laptops
--------------

| Modelo       | Procesador  | RAM  | Almacenamiento | Precio    |
|--------------|-------------|------|----------------|-----------|
| ThinkPad X1  | i7-12th     | 16GB | 512GB SSD      | $1,499    |
| MacBook Pro  | M3 Pro      | 18GB | 512GB SSD      | $2,299    |
| Dell XPS 15  | i9-13th     | 32GB | 1TB SSD        | $2,199    |
| HP Spectre   | i7-12th     | 16GB | 512GB SSD      | $1,699    |

Hoja 2: Monitores
----------------

| Marca  | Tamaño | Resolución | Tipo   | Precio |
|--------|--------|------------|--------|--------|
| Dell   | 27"    | 4K UHD     | IPS    | $599   |
| LG     | 32"    | 4K UHD     | IPS    | $799   |
| Samsung| 34"    | UWQHD      | VA     | $899   |
| ASUS   | 27"    | QHD        | IPS    | $449   |
"""
    }
    
    for filename, content in placeholders.items():
        file_path = canary_dir / filename
        file_path.write_text(content.strip())
        print(f"✅ Creado: {file_path}")
    
    print(f"\n📄 Archivos de texto placeholder creados en {canary_dir}")
    print("\n⚠️  NOTA: Para tests completos, reemplaza estos archivos .txt con:")
    print("   - PDFs reales (test_simple.pdf, test_table.pdf)")
    print("   - DOCX reales (test_headings.docx)")
    print("   - XLSX reales (test_merged_cells.xlsx)")
    print("   - Imagen PNG con texto (test_screenshot.png)")


if __name__ == "__main__":
    create_text_files()
    print("\n✅ Generación de archivos canario completada")

