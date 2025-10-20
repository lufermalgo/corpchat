#!/bin/bash
set -e

# Test E2E para Pipeline Completo de Documentos
# Valida que todos los formatos soportados se procesen correctamente

echo "🚀 CorpChat Document Pipeline - E2E Tests"
echo "=========================================="

# Configuración
INGESTOR_URL="https://corpchat-ingestor-2s63drefva-uc.a.run.app"
TEST_USER="test-pipeline-user"
TEST_CHAT="test-pipeline-chat"
PROJECT_ID="genai-385616"
BIGQUERY_DATASET="corpchat"
GCS_BUCKET="corpchat-genai-385616-attachments"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para crear archivos de prueba
create_test_files() {
    echo -e "${BLUE}📁 Creando archivos de prueba...${NC}"
    
    # Crear directorio de test si no existe
    mkdir -p test_files
    
    # 1. PDF simple con texto
    echo "Este es un documento PDF de prueba para CorpChat." > test_files/simple.txt
    echo "Contiene información sobre el proyecto de IA generativa." >> test_files/simple.txt
    echo "Se usa para validar el pipeline de procesamiento de documentos." >> test_files/simple.txt
    
    # Convertir a PDF (requiere pdftk o similar)
    if command -v ps2pdf &> /dev/null; then
        echo "Generando PDF con ps2pdf..."
        ps2pdf test_files/simple.txt test_files/test.pdf
    else
        echo -e "${YELLOW}⚠️ ps2pdf no disponible, creando PDF simple...${NC}"
        # Crear PDF básico usando Python
        python3 -c "
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
c = canvas.Canvas('test_files/test.pdf', pagesize=letter)
c.drawString(100, 750, 'Documento PDF de Prueba')
c.drawString(100, 700, 'Este es un documento de prueba para CorpChat.')
c.drawString(100, 650, 'Contiene información sobre IA generativa.')
c.drawString(100, 600, 'Se usa para validar el pipeline de documentos.')
c.save()
" 2>/dev/null || {
            echo -e "${YELLOW}⚠️ reportlab no disponible, usando archivo de texto como PDF...${NC}"
            cp test_files/simple.txt test_files/test.pdf
        }
    fi
    
    # 2. Archivo de texto plano
    cp test_files/simple.txt test_files/test.txt
    
    # 3. Archivo CSV
    echo "Nombre,Edad,Ciudad,Profesion" > test_files/test.csv
    echo "Juan Pérez,30,Madrid,Desarrollador" >> test_files/test.csv
    echo "María García,25,Barcelona,Diseñadora" >> test_files/test.csv
    echo "Carlos López,35,Valencia,Analista" >> test_files/test.csv
    
    echo -e "${GREEN}✅ Archivos de prueba creados${NC}"
}

# Función para testear upload de archivo
test_file_upload() {
    local file_path=$1
    local file_type=$2
    local expected_chunks=$3
    
    echo -e "${BLUE}🧪 Probando upload de $file_type...${NC}"
    
    # Upload archivo
    response=$(curl -s -X POST "$INGESTOR_URL/extract/process" \
        -F "file=@$file_path" \
        -F "user_id=$TEST_USER" \
        -F "chat_id=$TEST_CHAT" \
        -w "%{http_code}")
    
    http_code="${response: -3}"
    response_body="${response%???}"
    
    if [ "$http_code" -eq 200 ]; then
        echo -e "${GREEN}✅ Upload exitoso para $file_type${NC}"
        
        # Verificar que se crearon chunks en BigQuery
        sleep 5  # Esperar procesamiento
        
        chunk_count=$(bq query --use_legacy_sql=false --format=csv \
            "SELECT COUNT(*) as count FROM \`$PROJECT_ID.$BIGQUERY_DATASET.embeddings\` 
             WHERE user_id='$TEST_USER' AND chat_id='$TEST_CHAT'" | tail -n +2)
        
        if [ "$chunk_count" -ge "$expected_chunks" ]; then
            echo -e "${GREEN}✅ Chunks creados en BigQuery: $chunk_count >= $expected_chunks${NC}"
        else
            echo -e "${RED}❌ Chunks insuficientes: $chunk_count < $expected_chunks${NC}"
            return 1
        fi
        
        # Verificar que el archivo está en GCS
        filename=$(basename "$file_path")
        gcs_path="openwebui/$TEST_USER/$filename"
        
        if gsutil ls "gs://$GCS_BUCKET/$gcs_path" &>/dev/null; then
            echo -e "${GREEN}✅ Archivo guardado en GCS: gs://$GCS_BUCKET/$gcs_path${NC}"
        else
            echo -e "${RED}❌ Archivo no encontrado en GCS: $gcs_path${NC}"
            return 1
        fi
        
        return 0
    else
        echo -e "${RED}❌ Error en upload de $file_type: HTTP $http_code${NC}"
        echo "Response: $response_body"
        return 1
    fi
}

# Función para verificar embeddings en BigQuery
verify_embeddings() {
    echo -e "${BLUE}🔍 Verificando embeddings en BigQuery...${NC}"
    
    # Verificar estructura de la tabla
    table_info=$(bq show --format=json "$PROJECT_ID:$BIGQUERY_DATASET.embeddings" 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Tabla embeddings existe${NC}"
        
        # Verificar que hay datos recientes
        recent_count=$(bq query --use_legacy_sql=false --format=csv \
            "SELECT COUNT(*) as count FROM \`$PROJECT_ID.$BIGQUERY_DATASET.embeddings\` 
             WHERE created_at >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)" | tail -n +2)
        
        if [ "$recent_count" -gt 0 ]; then
            echo -e "${GREEN}✅ Embeddings recientes encontrados: $recent_count${NC}"
        else
            echo -e "${YELLOW}⚠️ No hay embeddings recientes${NC}"
        fi
        
        # Verificar estructura de embeddings
        embedding_sample=$(bq query --use_legacy_sql=false --format=csv \
            "SELECT ARRAY_LENGTH(embedding) as embedding_dim FROM \`$PROJECT_ID.$BIGQUERY_DATASET.embeddings\` 
             WHERE embedding IS NOT NULL LIMIT 1" | tail -n +2)
        
        if [ "$embedding_sample" = "768" ]; then
            echo -e "${GREEN}✅ Dimensión de embeddings correcta: $embedding_sample${NC}"
        else
            echo -e "${RED}❌ Dimensión de embeddings incorrecta: $embedding_sample (esperado: 768)${NC}"
            return 1
        fi
        
    else
        echo -e "${RED}❌ Tabla embeddings no existe o no accesible${NC}"
        return 1
    fi
}

# Función para testear re-lectura de documentos
test_document_reread() {
    echo -e "${BLUE}🔄 Probando re-lectura de documentos...${NC}"
    
    # Listar archivos del usuario
    files_response=$(curl -s -X GET "$INGESTOR_URL/files/$TEST_USER")
    
    if echo "$files_response" | grep -q "files_count"; then
        echo -e "${GREEN}✅ Lista de archivos obtenida${NC}"
        
        # Intentar re-leer el primer archivo
        filename=$(echo "$files_response" | python3 -c "
import sys, json
data = json.load(sys.stdin)
if data['files']:
    print(data['files'][0]['filename'])
else:
    print('')
")
        
        if [ -n "$filename" ]; then
            reread_response=$(curl -s -X POST "$INGESTOR_URL/re-read/$TEST_USER" \
                -H "Content-Type: application/json" \
                -d "{\"filename\": \"$filename\", \"force_refresh\": true}")
            
            if echo "$reread_response" | grep -q "success"; then
                echo -e "${GREEN}✅ Re-lectura exitosa para: $filename${NC}"
                return 0
            else
                echo -e "${RED}❌ Error en re-lectura: $reread_response${NC}"
                return 1
            fi
        else
            echo -e "${YELLOW}⚠️ No hay archivos para re-leer${NC}"
            return 0
        fi
    else
        echo -e "${RED}❌ Error obteniendo lista de archivos${NC}"
        return 1
    fi
}

# Función para testear búsqueda RAG
test_rag_search() {
    echo -e "${BLUE}🔍 Probando búsqueda RAG...${NC}"
    
    # Realizar búsqueda en embeddings
    query="documento prueba"
    
    search_results=$(bq query --use_legacy_sql=false --format=csv \
        "SELECT text, source_filename, chunk_index, 
                ML.DISTANCE(embedding, (
                    SELECT embedding FROM \`$PROJECT_ID.$BIGQUERY_DATASET.embeddings\` 
                    WHERE text LIKE '%prueba%' LIMIT 1
                ), 'COSINE') as distance
         FROM \`$PROJECT_ID.$BIGQUERY_DATASET.embeddings\`
         WHERE user_id='$TEST_USER' AND chat_id='$TEST_CHAT'
         ORDER BY distance ASC
         LIMIT 3")
    
    if [ $? -eq 0 ]; then
        result_count=$(echo "$search_results" | wc -l)
        if [ "$result_count" -gt 1 ]; then  # Más de 1 porque incluye header
            echo -e "${GREEN}✅ Búsqueda RAG exitosa: $((result_count-1)) resultados${NC}"
            return 0
        else
            echo -e "${YELLOW}⚠️ Búsqueda RAG sin resultados${NC}"
            return 0
        fi
    else
        echo -e "${RED}❌ Error en búsqueda RAG${NC}"
        return 1
    fi
}

# Función principal
main() {
    echo -e "${BLUE}🚀 Iniciando tests E2E del pipeline de documentos...${NC}"
    
    # Verificar dependencias
    if ! command -v bq &> /dev/null; then
        echo -e "${RED}❌ BigQuery CLI (bq) no está instalado${NC}"
        exit 1
    fi
    
    if ! command -v gsutil &> /dev/null; then
        echo -e "${RED}❌ Google Cloud Storage CLI (gsutil) no está instalado${NC}"
        exit 1
    fi
    
    # Crear archivos de prueba
    create_test_files
    
    # Tests por tipo de archivo
    tests_passed=0
    tests_total=0
    
    # Test 1: PDF
    tests_total=$((tests_total + 1))
    if test_file_upload "test_files/test.pdf" "PDF" 1; then
        tests_passed=$((tests_passed + 1))
    fi
    
    # Test 2: TXT
    tests_total=$((tests_total + 1))
    if test_file_upload "test_files/test.txt" "TXT" 1; then
        tests_passed=$((tests_passed + 1))
    fi
    
    # Test 3: CSV
    tests_total=$((tests_total + 1))
    if test_file_upload "test_files/test.csv" "CSV" 1; then
        tests_passed=$((tests_passed + 1))
    fi
    
    # Test 4: Verificar embeddings
    tests_total=$((tests_total + 1))
    if verify_embeddings; then
        tests_passed=$((tests_passed + 1))
    fi
    
    # Test 5: Re-lectura de documentos
    tests_total=$((tests_total + 1))
    if test_document_reread; then
        tests_passed=$((tests_passed + 1))
    fi
    
    # Test 6: Búsqueda RAG
    tests_total=$((tests_total + 1))
    if test_rag_search; then
        tests_passed=$((tests_passed + 1))
    fi
    
    # Resumen final
    echo ""
    echo "=========================================="
    echo -e "${BLUE}📋 RESUMEN DE TESTS DEL PIPELINE${NC}"
    echo "=========================================="
    echo -e "✅ Tests pasados: $tests_passed/$tests_total"
    
    if [ $tests_passed -eq $tests_total ]; then
        echo -e "${GREEN}🎉 ¡Todos los tests del pipeline pasaron!${NC}"
        echo ""
        echo -e "${BLUE}📋 PRÓXIMOS PASOS:${NC}"
        echo "1. Probar con formatos adicionales (DOCX, XLSX, imágenes)"
        echo "2. Validar procesamiento de archivos grandes"
        echo "3. Probar con múltiples usuarios simultáneos"
        echo "4. Monitorear métricas de rendimiento"
        
        # Limpiar archivos de prueba
        echo ""
        echo -e "${BLUE}🧹 Limpiando archivos de prueba...${NC}"
        rm -rf test_files
        echo -e "${GREEN}✅ Limpieza completada${NC}"
        
        exit 0
    else
        echo -e "${RED}❌ $((tests_total - tests_passed)) tests fallaron${NC}"
        echo ""
        echo -e "${BLUE}🔧 ACCIONES RECOMENDADAS:${NC}"
        echo "1. Revisar logs del servicio Ingestor"
        echo "2. Verificar configuración de BigQuery"
        echo "3. Validar permisos de Cloud Storage"
        echo "4. Comprobar conectividad de servicios"
        
        exit 1
    fi
}

# Ejecutar tests
main "$@"
