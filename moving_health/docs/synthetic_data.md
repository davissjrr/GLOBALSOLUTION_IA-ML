# Dados sintéticos de solicitações

## Origem e finalidade

`data/synthetic/moving_health_pedidos_sinteticos.csv` é gerado pelo projeto em `scripts/simulate_trip_demand.py`. Não foi baixado de uma fonte externa e não contém pedidos observados do Moving Health. Foi criado para demonstrar preparação tabular, previsão de contagens, comparação de cenários e gráficos no Google Colab.

## Estrutura

- Unidade da linha: hora × zona genérica × tipo de serviço.
- Cobertura simulada: 90 dias, de 2025-01-01 a 2025-03-31, 24 horas/dia, seis zonas e dois serviços; 25.920 linhas.
- Variáveis: `timestamp`, `zone_id`, `service_type`, hora, dia da semana, fim de semana, solicitações, veículos disponíveis, capacidade horária, solicitações atendidas, não atendidas, cenário e `is_synthetic`.
- Semente pseudoaleatória: 2026. Com os mesmos parâmetros e versões compatíveis de NumPy/Pandas, a geração é reproduzível.
- Codificação CSV: UTF-8 com BOM e separador vírgula. A leitura do notebook declara a codificação e interpreta `timestamp` como data.

## Hipóteses da simulação

As seis zonas são identificadores genéricos, sem correspondência geográfica. A taxa-base de cada zona varia entre 0,45 e 1,15 solicitações esperadas por zona/serviço/hora. O fator de visita domiciliar de profissional é 0,7 em relação ao transporte de paciente. Fatores horários representam picos hipotéticos de manhã e fim da tarde; fins de semana recebem fator 0,72.

A taxa horária recebe variação Gamma e a contagem é sorteada com Poisson. Essa composição cria sobre-dispersão para ilustrar picos aleatórios. A frota é hipotética; a capacidade assume uma solicitação atendível por veículo em cada intervalo de uma hora. Os multiplicadores de demanda e frota são parâmetros de cenário, não estimativas reais.

## Resultado ilustrativo da semente 2026

No arquivo-base de 90 dias foram geradas 15.931 solicitações, das quais 11.082 caberiam na capacidade simulada e 4.849 ficariam sem atendimento nesse modelo simplificado.

Uma comparação de 14 dias, com a mesma semente, produziu:

| Cenário | Fator de demanda | Fator de frota | Solicitações simuladas | Atendidas pela capacidade simulada | Não atendidas | Cobertura simulada |
|---|---:|---:|---:|---:|---:|---:|
| Normal | 1,00 | 1,00 | 2.496 | 1.733 | 763 | 69,43% |
| Pico de demanda | 1,40 | 1,00 | 3.483 | 2.178 | 1.305 | 62,53% |
| Frota reduzida | 1,00 | 0,65 | 2.496 | 562 | 1.934 | 22,52% |

Esses números verificam que os controles alteram os resultados conforme as regras programadas. Não são previsões para São Paulo ou para a operação real do Moving Health.

## Uso no modelo

O alvo do modelo experimental é `trips_requested`, a quantidade simulada de pedidos por hora, zona e serviço. A avaliação temporal reserva os últimos 14 dias. As features não incluem contagens realizadas, capacidade futura ou resultados do período de teste.

O notebook compara um `PoissonRegressor` com o baseline de média histórica para a mesma combinação de zona, serviço, dia da semana e hora. MAE, RMSE, WAPE e desvio Poisson medem a recuperação do processo sintético. Não medem desempenho real.
