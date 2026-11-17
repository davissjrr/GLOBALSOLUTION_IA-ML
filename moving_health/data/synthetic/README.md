# Dataset sintético de pedidos por hora

`moving_health_pedidos_sinteticos.csv` é um dataset criado localmente pelo script `scripts/simulate_trip_demand.py`, com 90 dias simulados, seis zonas genéricas e dois tipos de serviço. Ele não veio de uma base pública nem representa corridas reais.

Para reproduzir o CSV, instale `requirements-colab.txt` e rode na raiz do repositório:

```powershell
python scripts/simulate_trip_demand.py
```

O gerador usa semente 2026 por padrão e salva em UTF-8 com BOM e separador vírgula. As hipóteses e limites estão em `docs/synthetic_data.md`.
