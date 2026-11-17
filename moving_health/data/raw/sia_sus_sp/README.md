# Exportação bruta SIA/SUS — São Paulo

Fonte: formulário oficial [TABNET/DATASUS para produção ambulatorial por local de atendimento](https://tabnet.datasus.gov.br/cgi/deftohtm.exe?sia/cnv/qasp.def), com Município nas linhas, Ano/mês de atendimento nas colunas e `Qtd.aprovada` como conteúdo.

Arquivos preservados:

- `tabnet_qasp_municipio_mes_qtd_aprovada.csv`: resposta tabular PRN do TABNET.
- `tabnet_qasp_municipio_mes_qtd_aprovada_response.html`: resposta HTML recebida.

Extração obtida em 16 nov. 2026: 224 meses (jan/2008–ago/2026), 645 municípios e uma linha total. Inspeção executada: sequência mensal contínua, sem rótulos municipais duplicados, 1.280 marcadores de zero, sem células vazias e sem valores irregulares.

O script `scripts/download_sia_tabnet.py` não sobrescreve arquivos brutos existentes. Os termos de redistribuição da base ainda devem ser confirmados antes de publicá-la. Consulte `docs/data_sources.md` para semântica, procedência e limitações.
