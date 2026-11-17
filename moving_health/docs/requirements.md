# Requisitos e definição do problema

## Problema nesta etapa

O Moving Health é uma plataforma de mobilidade voltada à saúde que pretende conectar pacientes a unidades e permitir que profissionais credenciados atendam pacientes em domicílio. O projeto está em estágio inicial; não há histórico de solicitações próprias confirmado.

Para cumprir a atividade com dados reais e rastreáveis, o protótipo prevê a quantidade aprovada do SIA/SUS por município de atendimento e mês. Essa medida é produção ambulatorial agregada; não representa pessoas únicas, demanda de transporte, corridas, necessidade clínica ou disponibilidade atual de atendimento.

O resultado pode ser exibido como contexto em um painel de planejamento regional. A interpretação de sua utilidade para mobilidade permanece uma hipótese, não uma relação validada.

Além do modelo SIA/SUS, o notebook agora contém um experimento separado de simulação sintética da demanda horária de solicitações. Seu objetivo é demonstrar como uma previsão de contagens e cenários de capacidade poderiam aparecer no Moving Health. Os registros gerados são explicitamente sintéticos e não alteram a semântica nem as métricas do SIA/SUS.

## Dados confirmados

- Fonte oficial investigada: SIA/SUS TABNET/DATASUS, recorte do estado de São Paulo.
- Dimensões selecionadas: município de atendimento × mês de atendimento.
- Variável: `Qtd.aprovada`.
- Extração preservada: janeiro de 2008 a agosto de 2026, 224 meses e 645 municípios.
- Inspeção executada: 1.280 marcadores de zero convertidos; zero células vazias; nenhuma duplicação municipal ou valor fora do formato inteiro.
- Nenhum dado pessoal ou clínico individual é usado.

Procedência e limites estão descritos em `data_sources.md`.

## Protocolo e resultado

- Série mensal; ajuste por município.
- Modelo candidato: mínimos quadrados com tendência linear e efeitos fixos de mês.
- Comparador: baseline sazonal que repete o valor 12 meses antes.
- Holdout cronológico: os 12 meses finais (set. 2025–ago. 2026); 212 meses anteriores para treino.
- Histórico mínimo: 36 meses antes do horizonte de avaliação.
- Métricas agregadas: MAE, RMSE, WAPE e R² sobre 7.740 pares município-mês.
- Método recomendado pela API: o de menor WAPE no holdout. No resultado atual, foi o baseline sazonal.

Resultado atual: baseline MAE 23.511,19, RMSE 118.449,14, WAPE 11,57%; regressão MAE 34.368,34, RMSE 145.817,43, WAPE 16,91%. O candidato de regressão foi treinado e exportado, mas perdeu para o baseline nesta avaliação. Consulte `experiments.md`.

## Integração

O protótipo existente expõe a previsão SIA/SUS via API local. No Colab, o experimento sintético gera uma previsão de contagens, gráficos de cenário e um artefato scikit-learn exportável. Os dois fluxos declaram a origem do alvo. Nenhuma ação clínica, despacho ou alocação automática é executada.

## Bibliotecas do experimento sintético

- Pandas para leitura, preparação, agrupamentos e séries temporais.
- NumPy para geração pseudoaleatória reproduzível das contagens.
- scikit-learn para pipeline de preparação e `PoissonRegressor`.
- Matplotlib para gráficos e comparação de cenários.

As dependências Colab estão em `requirements-colab.txt`. A versão instalada é registrada no notebook. O parser específico TABNET continua responsável pela exportação real com preâmbulo, separador ponto e vírgula e codificações possíveis.

## Fora de escopo e condições para revisão

- Prever viagens, solicitações, passageiros ou tempo de chegada.
- Diagnóstico, triagem ou priorização clínica.
- Matching operacional de motoristas/profissionais.
- Produção, implantação pública ou decisão automatizada.

Rever o problema quando existirem pedidos próprios do Moving Health, com definição explícita do evento a prever e armazenamento minimizado. Rever o método estatístico com validação por janelas temporais e em novas extrações antes de qualquer uso operacional. Confirmar os termos de redistribuição antes de publicar a base.
