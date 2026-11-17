# Fontes de dados e procedência

## Fonte em investigação

- [SES-SP — Informações de Saúde / TABNET](https://www.saude.sp.gov.br/links/informacoes-de-saude-tabnet)
- [DATASUS — Produção Ambulatorial SIA/SUS](https://datasus.saude.gov.br/acesso-a-informacao/producao-ambulatorial-sia-sus/)
- [Formulário TABNET — São Paulo por local de atendimento](https://tabnet.datasus.gov.br/cgi/deftohtm.exe?sia/cnv/qasp.def)
- [Notas técnicas — Produção Ambulatorial por local de atendimento](https://tabnet.datasus.gov.br/cgi/sia/Prod_amb_loc_atend_2008.pdf)

## Consulta observada

- **Acesso observado:** 12 nov. 2026 na investigação inicial; formulário oficial consultado novamente em 16 nov. 2026.
- **Linhas:** Município.
- **Colunas:** Ano/mês de atendimento.
- **Conteúdo:** Qtd.aprovada.
- **Formato selecionado:** texto com colunas separadas por ponto e vírgula (`PRN`).
- **Período listado:** jan/2008 a ago/2026. A página alerta que os seis meses mais recentes estão sujeitos a atualização.
- **Arquivo local:** obtido em 16 nov. 2026 em `data/raw/sia_sus_sp/`. O export retornou 224 meses (jan/2008–ago/2026) e 646 linhas de tabela incluindo total, ou 645 municípios mais a linha total.
- **Arquivos preservados:** CSV em `tabnet_qasp_municipio_mes_qtd_aprovada.csv` e resposta HTML recebida em `tabnet_qasp_municipio_mes_qtd_aprovada_response.html`.
- **Baixador:** `scripts/download_sia_tabnet.py` reproduz a seleção, valida a cobertura mensal e não sobrescreve arquivos.
- **Licença/redistribuição:** termos específicos não foram confirmados. Revisar antes de redistribuir a base.

## Semântica e limites

As notas técnicas definem município por local de atendimento: município onde a unidade de saúde está estabelecida. `Ano/mês de atendimento` corresponde ao período do atendimento; processamento é uma referência temporal distinta. `Quantidade aprovada` se refere à produção aprovada para pagamento.

Esses registros agregados não representam pessoas únicas nem viagens. Diferenças de oferta, registro e processamento entre municípios podem afetar comparações. Os meses recentes podem ser revisados.

A legenda do TABNET identifica `-` como zero numérico sem arredondamento. A leitura converte esse marcador em `0`; células realmente vazias permanecem ausentes e não são imputadas. A coluna `Total`, quando presente, é apenas um agregado de conferência e não entra como observação mensal.

## Inspeção executada

Em 16 nov. 2026, `scripts/inspect_sia_tabnet.py` validou o CSV preservado. Resultado: 224 colunas mensais contínuas; 645 rótulos municipais, sem duplicações; 1.280 marcadores TABNET de zero; nenhuma célula realmente vazia e nenhum valor fora do formato inteiro esperado. O painel de treino manteve todas as 645 séries completas.

## Tentativas de extração

1. A consulta completa foi montada e exibida no navegador em formato delimitado por `;` na investigação anterior.
2. Nesta sessão, o primeiro acesso HTTP isolado falhou por DNS. O formulário oficial respondeu e confirmou os campos e meses disponíveis.
3. As primeiras tentativas POST expiraram; uma chamada posterior com `curl` recebeu a série completa, que passou pelas verificações de cabeçalho, 224 meses contínuos e largura das linhas antes de ser salva.
4. O baixador preserva a resposta HTML recebida e não sobrescreve arquivos existentes.

## Caminho de reprodução

Executar `python scripts/inspect_sia_tabnet.py` para reproduzir a inspeção e então `python scripts/train_sia_forecast.py` para gerar o painel derivado, métricas, previsões e artefato. A origem bruta não deve ser editada; nova aquisição nunca sobrescreve a cópia existente.

## Dataset sintético de mobilidade

O arquivo `data/synthetic/moving_health_pedidos_sinteticos.csv` é criado pelo projeto em `scripts/simulate_trip_demand.py`; não é um download nem uma fonte de pedidos do Moving Health. Usa NumPy/Pandas, semente 2026 e parâmetros hipotéticos definidos no código. Contém 25.920 linhas agregadas por hora, zona genérica e serviço, com marca `is_synthetic=True`.

Não foi incorporado CSV externo de táxis ou transporte urbano: esses registros não teriam rótulos equivalentes a solicitações de saúde do Moving Health e poderiam sugerir uma transferência de domínio sem validação. A base sintética serve apenas para demonstrar o pipeline, cenários e gráficos. O SIA/SUS permanece identificado separadamente como dado público real. Hipóteses, campos e licença do arquivo gerado estão descritos em `synthetic_data.md`.
