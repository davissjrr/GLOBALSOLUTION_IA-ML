# Experimentos e avaliações

## Fonte e preparação — 16 nov. 2026

- Consulta oficial SIA/SUS TABNET para São Paulo: Município × mês de atendimento, conteúdo Qtd.aprovada.
- Cobertura obtida: 224 meses, jan/2008–ago/2026; 645 municípios e uma linha total.
- Inspeção executada pelo script: 1.280 marcadores `-` como zero; 0 células vazias; 0 rótulos municipais duplicados; 0 valores fora do formato inteiro; sequência mensal contínua.
- Painel derivado: formato longo, 645 × 224 = 144.480 observações município-mês.
- Nenhuma viagem simulada é misturada ao experimento SIA/SUS; não há atributos pessoais.

## Protocolo de avaliação

- Holdout cronológico: os 12 meses finais, set/2025–ago/2026.
- Treino: os 212 meses anteriores. Mínimo de histórico definido em 36 meses.
- Unidade de avaliação: município-mês; 7.740 observações em 645 municípios.
- Baseline: repetir para cada mês o valor do mesmo mês um ano antes.
- Candidato treinado: regressão linear de mínimos quadrados com tendência temporal e indicadores de mês (dezembro como referência), ajustada separadamente por município.
- Métricas agregadas: MAE, RMSE, WAPE e R². WAPE é a métrica usada para selecionar o método de demonstração; não substitui a inspeção de métricas por município.

## Resultado registrado

| Método | MAE | RMSE | WAPE | R² |
|---|---:|---:|---:|---:|
| Baseline sazonal de 12 meses | 23.511,19 | 118.449,14 | 11,5693% | 0,993944 |
| Regressão linear com tendência e sazonalidade mensal | 34.368,34 | 145.817,43 | 16,9119% | 0,990823 |

O baseline teve menor erro absoluto médio, raiz do erro quadrático e WAPE. Por isso, o artefato e a API o recomendam para esta demonstração. O R² alto dos dois métodos é influenciado pela grande variação entre municípios e não contradiz os erros menores do baseline. A regressão foi ajustada e exportada, mas permaneceu como candidata experimental por não vencer a referência.

## Explorações adicionais

Foram comparadas, no mesmo holdout exploratório, regressões ajustadas em janelas recentes de 36, 48, 60, 72, 84 e 120 meses, além da série completa; médias sazonais históricas e mistura ponderada das observações sazonais mais recentes. Nenhuma dessas explorações foi promovida ao pipeline principal.

- A regressão com janela de 84 meses obteve WAPE de 11,76%, MAE de 23.894,31 e RMSE de 105.765,50. Teve RMSE menor, mas WAPE e MAE maiores que o baseline.
- A mistura de 70% do último valor sazonal e 30% do anterior obteve WAPE de 12,08%, MAE de 24.551,06 e RMSE de 121.895,40.
- O baseline de 12 meses manteve a menor WAPE (11,57%) e MAE (23.511,19) entre as alternativas comparadas.

Essas explorações compartilham o mesmo período de holdout e não são uma validação independente. Uma nova seleção deve usar validação por janelas temporais e uma extração posterior antes de qualquer promoção do modelo candidato.

## Artefatos e reprodução

- `data/processed/sia_sus_sp/qtd_aprovada_municipio_mes.csv`: tabela longa derivada.
- `reports/sia_sus_sp/metricas_avaliacao.csv`: métricas do holdout.
- `reports/sia_sus_sp/previsoes_validacao.csv`: valores reais e previsões comparadas.
- `reports/sia_sus_sp/previsoes_futuras.csv`: previsão do baseline, candidato e método recomendado para até 12 meses.
- `models/moving_health_sia_sus.json`: coeficientes treinados, métricas, janela e últimas observações do baseline.

O notebook executável e o serviço HTTP local reproduzem o fluxo principal. Nenhuma previsão foi validada contra viagens reais do Moving Health.

## Simulação de demanda para Colab — 17 nov. 2026

- **Dataset sintético:** gerado por `scripts/simulate_trip_demand.py`, semente 2026, 90 dias, seis zonas genéricas × dois serviços × 24 intervalos/hora = 25.920 linhas.
- **Contagens no cenário-base:** 15.931 solicitações simuladas; 11.082 atendidas pela capacidade simulada; 4.849 não atendidas, sob a hipótese de uma solicitação por veículo/hora.
- **Cenários determinísticos de 14 dias:** normal (2.496 solicitadas, 1.733 atendidas, 763 não atendidas); pico de demanda com fator 1,40 (3.483, 2.178, 1.305); frota reduzida com fator 0,65 (2.496, 562, 1.934).
- **Modelo e protocolo:** `PoissonRegressor` da scikit-learn, comparado a médias históricas por zona, serviço, dia da semana e hora; holdout temporal dos últimos 14 dias, de 18 a 31 mar. 2025, com 4.032 observações. O pipeline foi treinado nos dados anteriores ao holdout.

| Método | MAE | RMSE | WAPE | Desvio Poisson |
|---|---:|---:|---:|---:|
| Baseline de média histórica | 0,61997 | 0,84909 | 102,4891% | 1,34236 |
| `PoissonRegressor` | 0,69566 | 0,88659 | 115,0024% | 1,17824 |

O baseline teve menor MAE, RMSE e WAPE; o `PoissonRegressor` teve menor desvio Poisson. Como os dois WAPEs excedem 100%, o experimento revela desempenho fraco para esta distribuição esparsa. O resultado é apenas sintético e não estima a qualidade em pedidos ou corridas reais. O notebook exporta o pipeline treinado como `models/moving_health_demanda_sintetica.joblib`, metadados JSON, previsões, tabelas e gráficos.

- **Versões registradas no Colab:** pandas 2.2.3, NumPy 2.4.6, scikit-learn 1.6.1, Matplotlib 3.10.0 e joblib 1.6.0.
- **Visualizações produzidas:** padrão horário e semanal, pedidos versus capacidade por cenário e observado versus previsto no holdout.
- **Arquivos:** dataset em `data/synthetic/`; métricas e previsões em `reports/synthetic/`; gráficos PNG na mesma pasta; modelo e metadados em `models/`.
