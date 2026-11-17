# Moving Health — IA para acessibilidade e planejamento em saúde

Protótipo acadêmico em Python para apoiar o planejamento de uma plataforma que conecta pessoas a serviços de saúde. O projeto demonstra preparação de dados, modelos, métricas, cenários de capacidade e pontos de integração.

## Escopo e interpretação

O repositório contém duas trilhas separadas:

1. **Contexto real (SIA/SUS):** previsão mensal da quantidade aprovada de procedimentos ambulatoriais por município. É um indicador agregado de atividade assistencial; não contém pedidos, viagens, pacientes ou disponibilidade operacional do Moving Health.
2. **Simulação sintética:** geração de solicitações horárias fictícias, comparação de capacidade e cenários, e treino de um `PoissonRegressor`. Os números e previsões desta trilha são didáticos e não medem desempenho em corridas reais.

Ainda não há histórico operacional do Moving Health confirmado. Portanto, este protótipo apoia uma demonstração da abordagem e não deve ser usado para decisões clínicas, despacho real ou promessa de tempo de chegada.

## Entregáveis conferidos

- Notebook reproduzível: `notebooks/01_moving_health_previsao_contextual.ipynb`.
- Dados e origem: extração agregada do SIA/SUS em `data/raw/sia_sus_sp/`; dados sintéticos gerados com semente fixa em `data/synthetic/`; detalhes em [`docs/data_sources.md`](docs/data_sources.md) e [`docs/synthetic_data.md`](docs/synthetic_data.md).
- Modelos: artefato de previsão contextual SIA/SUS em `models/moving_health_sia_sus.json`; modelo sintético treinado em `models/moving_health_demanda_sintetica.joblib` e metadados ao lado.
- Avaliação: métricas, previsões, cobertura, tabelas de cenários e gráficos em `reports/`.
- Integração demonstrativa: API local de previsão SIA/SUS em `scripts/forecast_service.py`; o notebook também gera uma previsão sintética para 24 horas e cenários de capacidade.
- Pacote portátil para executar o notebook no Colab: `exports/moving_health_pacote.zip`.

O notebook local contém o código completo e é reproduzível. Ao abrir no Colab, execute as células na ordem para que os gráficos, métricas e previsões apareçam na sessão.

## Resultados registrados

### Indicador SIA/SUS

Holdout cronológico de setembro de 2025 a agosto de 2026, com 7.740 observações de 645 municípios. O baseline repete o valor do mesmo mês do ano anterior.

| Método | MAE | RMSE | WAPE | R² |
|---|---:|---:|---:|---:|
| Baseline sazonal de 12 meses | 23.511,19 | 118.449,14 | 11,57% | 0,993944 |
| Regressão linear com tendência e mês do ano | 34.368,34 | 145.817,43 | 16,91% | 0,990823 |

O baseline teve menor MAE, RMSE e WAPE e é o método recomendado pelo endpoint para esta extração. O alvo continua sendo produção aprovada de procedimentos, não demanda de viagens.

### Demanda sintética

O CSV contém 25.920 linhas geradas para 90 dias, seis zonas genéricas e dois tipos de serviço. O holdout final contém 4.032 observações (14 dias).

| Método | MAE | RMSE | WAPE | Desvio Poisson |
|---|---:|---:|---:|---:|
| Baseline de média histórica | 0,620 | 0,849 | 102,49% | 1,342 |
| `PoissonRegressor` | 0,696 | 0,887 | 115,00% | 1,178 |

O baseline teve menor MAE, RMSE e WAPE; o `PoissonRegressor` teve menor desvio Poisson. Como o WAPE sintético passa de 100%, a previsão ainda é fraca para contagens esparsas. O modelo está treinado e exportado para demonstrar o fluxo, mas não deve ser apresentado como eficaz para viagens reais.

Na simulação de 14 dias, a cobertura da capacidade hipotética foi 69,43% no cenário normal, 62,53% no pico de demanda e 22,52% com frota reduzida. Esses resultados dependem das hipóteses descritas em [`docs/synthetic_data.md`](docs/synthetic_data.md).

## Como colocar o notebook no seu repositório GitHub

1. Crie um repositório no GitHub. Se for usar o botão do Colab, deixe-o público ou confirme que a sua conta Google tem acesso ao repositório privado.
2. Envie a estrutura inteira do projeto para a raiz do repositório, preservando as pastas `notebooks/`, `data/`, `models/`, `reports/`, `scripts/`, `docs/` e `exports/`. O notebook precisa permanecer neste caminho: `notebooks/01_moving_health_previsao_contextual.ipynb`.
3. Inclua `requirements-colab.txt` e `exports/moving_health_pacote.zip`. O ZIP é o pacote que o notebook pede para carregar no ambiente temporário do Colab.
4. No link abaixo, troque `SEU_USUARIO/SEU_REPOSITORIO` pelo proprietário e nome do seu repositório. Se a branch principal não se chamar `main`, ajuste esse trecho também.

Para enviar pelo site do GitHub, abra o repositório, escolha **Add file → Upload files**, arraste os arquivos e pastas do projeto e confirme o commit. Também é possível clonar o repositório, copiar o conteúdo do projeto para a pasta clonada e enviar com `git add`, `git commit` e `git push`; veja a [documentação do GitHub para adicionar arquivos](https://docs.github.com/en/repositories/working-with-files/managing-files/adding-a-file-to-a-repository). O Colab pode abrir notebooks diretamente do GitHub. Quando abrir o original do repositório, salve o resultado como uma cópia no GitHub ou baixe o `.ipynb` editado e envie/substitua o arquivo no repositório; executar o notebook não atualiza automaticamente o arquivo de origem. Consulte o [FAQ oficial do Colab](https://research.google.com/colaboratory/faq.html?hl=pt-BR).

```markdown
[![Abrir no Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/SEU_USUARIO/SEU_REPOSITORIO/blob/main/notebooks/01_moving_health_previsao_contextual.ipynb)
```

Você pode colar esse bloco no início deste README. Ao clicar no selo, o Colab abre o notebook diretamente do GitHub. Depois, execute as células em ordem; quando solicitado, envie `moving_health_pacote.zip` que você baixou da pasta `exports/` do repositório. O ambiente do Colab é temporário, então baixe o `moving_health_resultados.zip` gerado ao final se quiser guardar as saídas da sessão.

## Fluxo principal: Google Colab

Este é o ambiente usado para desenvolver e registrar os resultados do projeto.

1. Abra o notebook pelo selo do README ou use **Arquivo → Fazer upload de notebook**.
2. Execute as células em ordem. A primeira etapa procura o projeto e, se necessário, pede o ZIP portátil.
3. O notebook usa caminhos relativos ao projeto, verifica as dependências de `requirements-colab.txt` e carrega o CSV sintético incluído. Não é preciso montar o Google Drive nem usar caminhos do computador de quem desenvolveu.
4. Execute a célula final para baixar `moving_health_resultados.zip`, que reúne modelo, métricas, previsões e gráficos.

## Alternativa: instalar e executar no VS Code (Windows)

O VS Code é uma opção para trabalhar com os mesmos arquivos no computador. Esta configuração local é independente do Colab: os arquivos e resultados ficam na pasta do projeto, e não é necessário enviar o ZIP portátil.

### 1. Instalar os programas

1. Instale Python 3.12 pela [página oficial do Python para Windows](https://www.python.org/downloads/windows/). O projeto requer Python 3.10 ou superior.
2. Instale [Visual Studio Code](https://code.visualstudio.com/).
3. No VS Code, abra **Extensions** (`Ctrl+Shift+X`) e instale as extensões **Python** e **Jupyter**, ambas publicadas pela Microsoft.
4. Baixe o projeto do GitHub (ou extraia o ZIP do projeto) e, no VS Code, escolha **File → Open Folder**. Selecione a pasta raiz, aquela que contém `README.md`, `requirements-colab.txt`, `notebooks/` e `scripts/`.

### 2. Criar ambiente virtual e instalar bibliotecas

No VS Code, abra **Terminal → New Terminal** e use o terminal PowerShell. Execute os comandos a partir da raiz do projeto:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -r requirements-colab.txt
.\.venv\Scripts\python.exe -m pip install ipykernel
```

No VS Code, pressione `Ctrl+Shift+P`, escolha **Python: Select Interpreter** e selecione o Python dentro de `.venv`. Se o comando `py` não existir, instale Python pelo link acima, feche e reabra o VS Code e tente novamente.

### 3. Executar o notebook

Abra `notebooks/01_moving_health_previsao_contextual.ipynb`. No seletor **Select Kernel**, escolha o ambiente `.venv` e use **Run All**. O notebook encontra os arquivos a partir da pasta do projeto; no VS Code, não é necessário fazer upload de `moving_health_pacote.zip`. Os artefatos são gravados nas pastas `models/` e `reports/`. A última célula informa que o download ZIP é específico do Colab.

### 4. Executar os scripts (opcional)

Para executar as etapas pelo terminal em vez do notebook:

```powershell
.\.venv\Scripts\python.exe scripts/inspect_sia_tabnet.py
.\.venv\Scripts\python.exe scripts/train_sia_forecast.py
.\.venv\Scripts\python.exe scripts/simulate_trip_demand.py
```

O treino SIA/SUS cria ou atualiza o painel derivado, relatórios e artefato JSON. O simulador gera novamente o CSV sintético com semente fixa. A aquisição de uma nova extração pública é opcional; veja [`docs/data_sources.md`](docs/data_sources.md) antes de baixar ou redistribuir dados.

## Integração demonstrativa pela API

Para consultar a previsão contextual localmente, inicie o serviço:

```powershell
.\.venv\Scripts\python.exe scripts/forecast_service.py
```

Em outro terminal, solicite três meses para São Paulo:

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/previsao?municipio=S%C3%A3o%20Paulo&horizonte=3"
```

O endpoint `/previsao` aceita horizonte de 1 a 12 meses e seleciona o método com menor WAPE no holdout atual. Esta API demonstra a integração de uma previsão contextual agregada; não é ainda um backend de despacho de viagens. No notebook, a previsão sintética de 24 horas e os cenários ilustram como resultados poderiam alimentar uma tela de planejamento.

## Estrutura principal

```text
data/raw/sia_sus_sp/                 # extração pública agregada e resposta preservada
data/processed/sia_sus_sp/           # painel mensal derivado
data/synthetic/                      # solicitações fictícias e documentação da geração
docs/                                 # fontes, hipóteses, arquitetura, experimentos e vídeo
exports/moving_health_pacote.zip      # pacote portátil para carregar no Colab
models/                               # artefatos SIA/SUS e modelo sintético treinado
notebooks/01_moving_health_previsao_contextual.ipynb
reports/sia_sus_sp/                  # métricas, cobertura e previsões do indicador público
reports/synthetic/                   # métricas, cenários, previsões e gráficos sintéticos
scripts/                              # inspeção, treino, simulação e API demonstrativa
requirements-colab.txt
```
