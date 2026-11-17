# Roteiro do vídeo demonstrativo — até 2 minutos

Roteiro pronto para gravação. A duração estimada é de 1min45s a 1min55s, em ritmo natural. As indicações entre colchetes são ações na tela, não falas.

## 0:00–0:20 — Problema e dados

**Tela:** título Moving Health; depois, mostre a seção de problema no notebook.

**Fala:** “O Moving Health busca melhorar o acesso a serviços de saúde conectando pessoas a atendimentos e transporte. Como ainda não temos histórico próprio de solicitações e viagens, separamos o projeto em duas trilhas: dados públicos agregados do SIA/SUS para contexto de saúde e dados sintéticos para simular pedidos e capacidade. Assim, não confundimos produção assistencial com corridas reais.”

## 0:20–0:42 — Preparação e análise

**Tela:** mostre a inspeção e o resumo do CSV.

**Fala:** “A base pública cobre 224 meses e 645 municípios. Tratamos os marcadores de ausência do TABNET, organizamos uma série mensal e reservamos os 12 meses finais para teste. Na simulação, geramos 25.920 registros horários com uma semente fixa, seis zonas e dois serviços. Também comparamos cenários normal, pico de demanda e frota reduzida.”

## 0:42–1:07 — Modelo e treino

**Tela:** mostre a célula do corte temporal e do treino.

**Fala:** “Para o indicador SIA/SUS, comparamos a repetição sazonal do ano anterior com uma regressão linear por município, usando tendência e mês. Na trilha sintética, treinamos um PoissonRegressor com zona, serviço e características de calendário, comparando-o a uma média histórica. A separação temporal evita usar o período de teste no treino.”

## 1:07–1:30 — Avaliação com métricas

**Tela:** mostre as tabelas de métricas dos dois experimentos.

**Fala:** “No SIA/SUS, o baseline sazonal venceu a regressão: WAPE de 11,57%, contra 16,91%. Na simulação, o baseline teve WAPE de 102,49%, contra 115% do PoissonRegressor; o modelo teve menor desvio Poisson. Esse WAPE alto mostra que a previsão sintética ainda é fraca para contagens esparsas. Nenhuma dessas métricas representa desempenho em viagens reais.”

## 1:30–1:52 — Integração na solução

**Tela:** mostre a previsão de 24 horas, o comparativo de cenários e, se couber, o endpoint `/previsao`.

**Fala:** “Na demonstração, o notebook gera uma previsão sintética para as próximas 24 horas e estima solicitações atendidas e não atendidas em cada cenário. O serviço local também expõe uma previsão mensal do indicador SIA/SUS por município. Com dados reais do piloto, essa arquitetura poderá evoluir para apoiar planejamento de capacidade e acessibilidade, após validação com a equipe e com as pessoas usuárias.”

## Preparação da gravação

1. Abra `notebooks/01_moving_health_previsao_contextual.ipynb` no Colab e envie `exports/moving_health_pacote.zip` quando solicitado.
2. Execute as células em ordem e deixe as tabelas e gráficos aparecerem antes de iniciar a gravação.
3. Mostre os resultados SIA/SUS e sintéticos em momentos separados, para não sugerir que os dados simulados são corridas observadas.
4. Grave a tela com a narração acima; evite exibir credenciais, dados pessoais ou caminhos de arquivos da sua máquina.
