#!/bin/bash

# Script para monitorear consumo de Google Cloud Speech-to-Text específico de CorpChat
# Autor: CorpChat Team
# Fecha: 2025-10-18

# Configuración
PROJECT_ID=$(gcloud config get-value project)
REGION="us-central1"
START_DATE=$(date -d "30 days ago" +%Y-%m-%d)
END_DATE=$(date +%Y-%m-%d)

echo "📊 MONITOREO DE CONSUMO GOOGLE STT - CORPCHAT"
echo "=============================================="
echo "Proyecto: $PROJECT_ID"
echo "Período: $START_DATE a $END_DATE"
echo ""

# 1. Consumo total de Speech-to-Text API
echo "🔍 1. CONSUMO TOTAL SPEECH-TO-TEXT API:"
echo "---------------------------------------"
bq query --use_legacy_sql=false --format=table "
SELECT 
  service.description as service_name,
  sku.description as sku_description,
  SUM(usage.amount) as total_usage,
  SUM(cost) as total_cost_usd,
  currency
FROM \`$PROJECT_ID.billing_export.gcp_billing_export_v1_015A9C_3B7F1C_3F8A2D\`
WHERE 
  service.description = 'Cloud Speech-to-Text API'
  AND _PARTITIONTIME >= TIMESTAMP('$START_DATE')
  AND _PARTITIONTIME < TIMESTAMP('$END_DATE')
GROUP BY service.description, sku.description, currency
ORDER BY total_cost_usd DESC
"

echo ""

# 2. Consumo por día (últimos 30 días)
echo "📈 2. CONSUMO POR DÍA (ÚLTIMOS 30 DÍAS):"
echo "----------------------------------------"
bq query --use_legacy_sql=false --format=table "
SELECT 
  DATE(usage_start_time) as fecha,
  SUM(usage.amount) as total_usage,
  SUM(cost) as total_cost_usd
FROM \`$PROJECT_ID.billing_export.gcp_billing_export_v1_015A9C_3B7F1C_3F8A2D\`
WHERE 
  service.description = 'Cloud Speech-to-Text API'
  AND usage_start_time >= TIMESTAMP('$START_DATE')
  AND usage_start_time < TIMESTAMP('$END_DATE')
GROUP BY DATE(usage_start_time)
ORDER BY fecha DESC
LIMIT 30
"

echo ""

# 3. Consumo por región (si aplica)
echo "🌍 3. CONSUMO POR REGIÓN:"
echo "-------------------------"
bq query --use_legacy_sql=false --format=table "
SELECT 
  location.region as region,
  SUM(usage.amount) as total_usage,
  SUM(cost) as total_cost_usd
FROM \`$PROJECT_ID.billing_export.gcp_billing_export_v1_015A9C_3B7F1C_3F8A2D\`
WHERE 
  service.description = 'Cloud Speech-to-Text API'
  AND usage_start_time >= TIMESTAMP('$START_DATE')
  AND usage_start_time < TIMESTAMP('$END_DATE')
GROUP BY location.region
ORDER BY total_cost_usd DESC
"

echo ""

# 4. Logs de CorpChat STT (últimas 24 horas)
echo "📝 4. LOGS DE CORPCHAT STT (ÚLTIMAS 24 HORAS):"
echo "----------------------------------------------"
gcloud logging read "
resource.type=cloud_run_revision 
AND resource.labels.service_name=corpchat-gateway 
AND textPayload:\"✅ Transcripción completada\"
AND timestamp>=\"$(date -d '24 hours ago' --iso-8601=seconds)\"
" --limit=10 --format="table(timestamp,textPayload)" --project="$PROJECT_ID"

echo ""

# 5. Métricas de uso (duración total transcrita)
echo "⏱️ 5. MÉTRICAS DE USO (DURACIÓN TRANSCRITA):"
echo "--------------------------------------------"
gcloud logging read "
resource.type=cloud_run_revision 
AND resource.labels.service_name=corpchat-gateway 
AND textPayload:\"✅ Transcripción completada\"
AND timestamp>=\"$(date -d '7 days ago' --iso-8601=seconds)\"
" --format="value(textPayload)" --project="$PROJECT_ID" | grep -o '"duration_seconds":[0-9.]*' | sed 's/"duration_seconds"://' | awk '{sum += $1} END {printf "Total duración transcrita (7 días): %.2f segundos (%.2f minutos)\n", sum, sum/60}'

echo ""

# 6. Estimación de costos por uso
echo "💰 6. ESTIMACIÓN DE COSTOS POR USO:"
echo "-----------------------------------"
echo "Google Cloud Speech-to-Text Pricing (Oct 2025):"
echo "• Audio hasta 60 segundos: \$0.006 por 15 segundos"
echo "• Audio > 60 segundos: \$0.006 por 15 segundos (mismo precio)"
echo ""
echo "Para calcular costos específicos de CorpChat:"
echo "1. Ve a Google Cloud Console > Billing"
echo "2. Selecciona tu proyecto: $PROJECT_ID"
echo "3. Filtra por 'Cloud Speech-to-Text API'"
echo "4. Usa los labels de billing configurados:"
echo "   - project: corpchat"
echo "   - service: stt"
echo "   - team: corpchat-dev"

echo ""
echo "✅ Monitoreo completado. Para análisis detallado, revisa Google Cloud Console > Billing"
