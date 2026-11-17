# Registro de decisões

## 12 nov. 2026 — descoberta e fonte inicial

- **Fato verificado:** o repositório estava na branch `main`, commit base `e920f28`, com apenas um README curto e sem dados ou documentação de projeto.
- **Decisão aprovada pelo usuário:** consultar o SIA/SUS de São Paulo e preparar `data/raw/sia_sus_sp/tabnet_qasp_municipio_mes_qtd_aprovada.csv` e `scripts/inspect_sia_tabnet.py`.
- **Configuração observada:** Município × Ano/mês de atendimento, conteúdo Qtd.aprovada, saída separada por `;`.
- **Resultado naquela sessão:** a consulta foi exibida, mas não foi transferida para arquivo local; o CSV ficou pendente.

## 15 nov. 2026 — avanço para modelagem

- **Decisão aprovada pelo usuário:** avançar com a criação do modelo.
- **Interpretação de trabalho:** prever a quantidade aprovada agregada por município e mês, como indicador indireto de atividade assistencial.
- **Limite naquele momento:** a inspeção da tabela real continuava pendente. Nenhum modelo foi treinado, nenhum desempenho foi medido e a hipótese não representa demanda de viagens.

## 16 nov. 2026 — organização dos arquivos

- **Decisão aprovada pelo usuário:** reunir o material em uma estrutura organizada de pastas e subpastas.
- **Implementação:** índice no README e registros em `docs/`.
- **Alternativa adiada naquele ponto:** criar notebook e código de treinamento. A tabela local ainda não existia; implementar avaliação sem os dados validados produziria um artefato não reproduzível.

## 16 nov. 2026 — aquisição e pipeline de modelagem

- **Pedido atual do usuário:** pesquisar CSVs válidos para este projeto, introduzir a base e escrever o treinamento e a avaliação.
- **Fonte escolhida:** formulário oficial TABNET/DATASUS para São Paulo por local de atendimento, Município × Ano/mês de atendimento, conteúdo Qtd.aprovada.
- **Implementação:** `scripts/download_sia_tabnet.py` baixa a consulta, preserva a resposta HTML recebida e só grava o CSV após validar os meses e a estrutura. `scripts/sia_tabnet_data.py` centraliza a leitura e as regras de zeros/vazios. `scripts/train_sia_forecast.py` prepara tabela derivada, compara regressão de tendência sazonal com baseline de 12 meses e mantém os últimos 12 meses como holdout cronológico.
- **Estado inicial dos dados:** as primeiras chamadas expiraram. Depois, a consulta completa foi obtida e salva como CSV e resposta HTML; cobertura jan/2008–ago/2026, 224 meses e 646 linhas incluindo total. Cabeçalho e largura das linhas passaram pela verificação da transferência.
- **Estado do treinamento:** não executado; o interpretador Python não está disponível neste ambiente. A validação dos valores com `scripts/inspect_sia_tabnet.py` ainda precisa preceder o treino. Não há métricas ou previsões observadas.
- **Limites mantidos:** o alvo é produção ambulatorial aprovada, um indicador indireto. Não representa viagem, corrida, pessoa única ou demanda de transporte.

## 16 nov. 2026 — validação, notebook e API de demonstração

- **Fato verificado:** a inspeção Python confirmou 645 séries municipais completas, 224 meses (jan/2008–ago/2026), 1.280 marcadores zero, nenhuma célula vazia, duplicação ou contagem irregular.
- **Fato verificado:** o holdout cronológico set/2025–ago/2026 contém 7.740 pares município-mês. O baseline sazonal obteve MAE 23.511,19, RMSE 118.449,14, WAPE 11,5693% e R² 0,993944. A regressão treinada obteve MAE 34.368,34, RMSE 145.817,43, WAPE 16,9119% e R² 0,990823.
- **Implementação:** notebook reproduzível para Google Colab, com envio de um ZIP portátil e caminhos relativos, artefato JSON do modelo candidato, previsões comparadas e API HTTP local opcional para consulta por município e horizonte.
- **Resultado operacional da validação:** a API recomenda o método com menor WAPE no holdout vigente; neste treino é o baseline. A regressão permanece no artefato como modelo experimental treinado.
- **Limite:** esse fluxo prediz Qtd.aprovada do SIA/SUS, não viagens ou pedidos do Moving Health.

## Registro de decisão

**ID:** MH-ADR-002  
**Título:** Primeiro componente preditivo para demonstração acadêmica  
**Status:** Implementado para protótipo; emprego em produção pendente  
**Data:** 16 nov. 2026  
**Contexto:** O Moving Health ainda não tem histórico de pedidos próprio confirmado, mas a atividade exige modelo treinado, métrica, previsão integrada e base com procedência.

**Alternativas consideradas:**

| Alternativa | Potencial | Lacuna atual | Situação |
|---|---|---|---|
| Previsão de pedidos de viagem | Útil para cobertura por região/horário | Ainda não há pedidos históricos do Moving Health | Adiada até existir alvo operacional real |
| ETA | Útil para informar chegada | Exige origem, destino, horário e trajetos confiáveis | Adiada até integração de roteamento e dados próprios |
| Matching | Útil para conectar pedido a profissional/motorista | Exige disponibilidade, localização e credenciamento atualizados | Adiada até existir operação e regras validadas |
| Disponibilidade assistencial | Útil para encontrar alternativas | Exige agenda/capacidade atualizada e fontes operacionais | Adiada até integração de agendas confiáveis |
| Produção ambulatorial SIA/SUS | Base pública real, série histórica mensal e recorte municipal | Não é uma medida de transporte nem disponibilidade | Escolhida como proxy contextual acadêmico |
| Dados simulados de corridas | Permitem exercitar um fluxo que se pareça com a plataforma | Não demonstram desempenho no mundo real e não foram necessários para treinar a base pública | Não selecionados nesta versão |

**Decisão:** treinar uma regressão linear de tendência e sazonalidade por município usando o SIA/SUS como indicador contextual e compará-la com um baseline sazonal de 12 meses. Selecionar para a API de demonstração o método com menor WAPE no holdout atual; o baseline venceu. A API deixa a regressão disponível como experimental.

**Justificativa:** essa escolha usa uma extração pública real já disponível, permite validação temporal reproduzível e produz uma resposta consultável sem criar dados artificiais. O comparador impede apresentar a regressão como boa sem evidência.

**Vantagens:** procedência verificável; sem dados pessoais; execução sem dependências externas; notebook, relatório e API compartilham os mesmos artefatos.

**Desvantagens e riscos:** a variável é proxy de produção assistencial; pode refletir oferta, registro e revisão dos dados; a métrica agregada privilegia municípios de maior volume; a regressão não venceu o baseline; a extração recente pode mudar.

**Consequências:** a previsão pode ser exibida como informação contextual para planejamento regional, com aviso explícito. Nenhuma ação de despacho, priorização clínica ou estimativa de viagens deve derivar dela.

**Alternativas adiadas, não descartadas:** demanda de viagens, ETA, matching, disponibilidade de atendimento, FastAPI, bibliotecas de análise de dados e validação por janelas temporais. FastAPI e bibliotecas externas podem ser adotadas quando houver necessidade operacional e ambiente definidos.

**Condições de revisão:** obtenção de solicitações próprias minimizadas e suficientes; definição do evento-alvo; validação por janelas temporais e por município/faixa de volume; nova extração para verificar estabilidade; confirmação de termos de redistribuição antes da publicação.

**Evidências:** `reports/sia_sus_sp/metricas_avaliacao.csv`, `cobertura.csv`, `previsoes_validacao.csv`, `previsoes_futuras.csv`, notebook e inspeção registrados em `docs/experiments.md`.

**Aprovação:** o usuário solicitou o desenvolvimento do componente em Python. A escolha do proxy é autorizada para o protótipo acadêmico; uso do indicador como decisão operacional permanece pendente.

## 17 nov. 2026 — simulação sintética e bibliotecas de análise

**ID:** MH-ADR-003  
**Título:** Simulação reproduzível de solicitações horárias no Colab  
**Status:** Aprovada pelo usuário e implementada como experimento separado  
**Data:** 17 nov. 2026  
**Contexto:** O usuário autorizou incluir Pandas, NumPy e scikit-learn e pediu gráficos e números simulados de corridas, com arquivos portáteis para execução no Google Colab.

**Alternativas consideradas:** CSV público de táxis/transporte; CSV sintético do Moving Health; converter produção SIA/SUS em número de corridas. O CSV público genérico teria outro domínio e não rotularia pedidos de transporte de saúde. Converter SIA/SUS em corridas não tem relação validada. A simulação sintética própria foi escolhida para demonstrar explicitamente as hipóteses sem apresentar esses dados como observados.

**Decisão:** gerar uma tabela sintética horária por zona genérica e tipo de serviço, usar NumPy com semente fixa para as contagens, Pandas para análise, scikit-learn com PoissonRegressor para previsão e Matplotlib para visualizações. Manter a avaliação SIA/SUS real, os dados sintéticos e suas métricas em diretórios e seções distintos. O notebook registra versões de bibliotecas e oferece o CSV e os artefatos no ZIP portátil do projeto.

**Justificativa:** a base não contém dados pessoais nem exige download externo; a unidade horária permite mostrar demanda, capacidade e pedidos hipoteticamente não atendidos. O modelo de Poisson é um primeiro candidato apropriado para contagens não negativas, a comparar com um baseline. O corte temporal preserva a ordem dos dados.

**Hipóteses explicitadas:** seis zonas sem correspondência geográfica; dois serviços; fatores horários e de fim de semana escolhidos para demonstração; contagem Gamma-Poisson para sobre-dispersão; uma solicitação por veículo por hora como capacidade simulada. Os números não descrevem a cidade nem o desempenho operacional real.

**Benefícios:** torna observável o fluxo de dados, treino, previsão e comparação de cenários; gera um CSV transportável; permite variar demanda e frota de modo controlado.

**Desvantagens e limites:** resultados dependem das taxas inventadas; métrica mede a recuperação de uma distribuição simulada; o modelo não deve ser usado como previsão real de viagens até existirem registros próprios.

**Condições de revisão:** quando o Moving Health tiver pedidos próprios suficientes, substituir as hipóteses por dados operacionais minimizados, refazer a definição do alvo e reavaliar em períodos reais ainda não vistos.

**Evidências:** `scripts/simulate_trip_demand.py`, `data/synthetic/moving_health_pedidos_sinteticos.csv`, `docs/synthetic_data.md`, notebook Colab e `requirements-colab.txt`.

**Aprovação:** usuário aprovou expressamente a inclusão das bibliotecas e a construção da simulação.

## Decisões ainda pendentes

- Confirmar os termos de redistribuição antes de publicar a cópia da base.
- Coletar registros próprios do Moving Health antes de chamar qualquer saída de previsão de viagens.
- Fazer validação por janelas temporais e métricas por município antes de propor uso operacional.
