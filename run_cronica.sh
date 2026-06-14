#!/usr/bin/env bash
# Agendamento automático da coluna "Cafezinho & Planeta, Urgente!"
# Cron sugerido (crontab -e):  0 10 * * 6  (sábado 10:00 UTC)
#
# Detecta arquivos .md novos em cronicas/ e agenda no WordPress
# para o próximo domingo 08:00 UTC. Ignora arquivos já agendados
# (marcador .agendado criado ao lado do .md após sucesso).

set -e

cd /home/cafezinho/cafezinho-europa
source .venv/bin/activate

mkdir -p logs
LOG_FILE="logs/cronica-$(date +%Y-%m-%d).log"

echo "$(date) - iniciando run_cronica.sh" >> "$LOG_FILE"

python -m pipeline.cronica --auto >> "$LOG_FILE" 2>&1
EXIT=$?

if [ $EXIT -eq 0 ]; then
    echo "$(date) - cronica OK" >> "$LOG_FILE"
else
    echo "$(date) - cronica FAIL (exit $EXIT)" >> "$LOG_FILE"
fi

exit $EXIT
