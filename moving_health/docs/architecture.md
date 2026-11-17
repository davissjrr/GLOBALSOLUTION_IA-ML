# Arquitetura do protótipo

## Fluxo

```text
SIA/SUS TABNET
    │ CSV preservado
    ▼
scripts/sia_tabnet_data.py ── parsing, meses, zeros e formato
    │
    ├── scripts/inspect_sia_tabnet.py ── resumo de qualidade
    ▼
scripts/train_sia_forecast.py
    ├── prepara tabela longa em data/processed/
    ├── avalia holdout e baseline em reports/
    └── exporta coeficientes e últimas observações em models/*.json
    │
    ▼
scripts/forecast_service.py ── API HTTP somente leitura
    └── GET /previsao?municipio=...&horizonte=...

scripts/simulate_trip_demand.py ── NumPy/Pandas, dataset marcado como sintético
    └── notebook Colab ── PoissonRegressor, baseline temporal, cenários e gráficos
        ├── models/*.joblib + metadados JSON
        └── reports/synthetic/ + CSVs e PNGs
```

## Responsabilidades

- `sia_tabnet_data.py` lê a tabela PRN/CSV, reconhece os meses, trata `-` como zero e mantém célula vazia como ausência.
- `inspect_sia_tabnet.py` reporta período, municípios, marcadores zero, vazios, duplicações e valores fora do formato esperado.
- `train_sia_forecast.py` valida sequência temporal, deriva um painel longo, ajusta regressão linear por município, avalia contra o baseline sazonal e exporta previsões e artefato JSON.
- `forecast_service.py` carrega o JSON ao iniciar e devolve previsão para um município. O método padrão é o que obteve menor WAPE no holdout atual; neste experimento, o baseline sazonal.
- `simulate_trip_demand.py` gera contagens sintéticas reproduzíveis por hora, zona genérica e serviço. Não lê nem mistura pedidos simulados com a extração pública.
- O notebook documenta o problema, a fonte, a análise, a avaliação, as previsões e a integração.

## Execução no Google Colab

O notebook pode ser aberto sem GitHub ou Google Drive. Se a raiz do projeto não estiver no ambiente, a primeira célula solicita o ZIP portátil, verifica os caminhos internos antes da extração e localiza os scripts e o CSV pelo nome relativo. O treino usa a mesma implementação Python do repositório. A última célula agrupa modelo, relatórios e painel derivado para download, pois o sistema de arquivos de uma sessão Colab é temporário.

O experimento sintético usa dependências listadas em `requirements-colab.txt`; instala apenas quando ausentes no runtime. O artefato scikit-learn é salvo com joblib e metadados JSON contendo semente, versões, período temporal e métricas. O pacote final inclui esse artefato, o CSV sintético e as figuras do experimento.

## Contrato do modelo

Entrada da API: nome do município ou rótulo municipal com código IBGE, horizonte de 1 a 12 meses e opção de método.

Saída: indicador, município, método, métricas observadas no holdout, previsões mensais e aviso semântico sobre o alvo.

O artefato contém os parâmetros ajustados do modelo experimental, o método selecionado pela validação, métricas, recorte temporal e as últimas 12 observações usadas pelo baseline. O arquivo é JSON legível, não um binário dependente de versão de biblioteca.

## Limites e evolução

A API roda em `127.0.0.1` e ilustra a integração com o backend. Ela não tem autenticação, persistência, monitoramento, implantação ou vínculo com a aplicação completa. Para produção, será necessário substituir o servidor demonstrativo por um serviço de aplicação adequado, versionar os dados/modelos, observar desempenho e tratar falhas.

O uso do SIA/SUS dá contexto de produção assistencial. Uma previsão de corridas exige dados próprios do Moving Health, como pedidos com horário, área geográfica aproximada e estado operacional, além de outra definição de alvo e validação.
