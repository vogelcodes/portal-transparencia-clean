# Portal da Transparência — API Reference

Base URL: `https://api.portaldatransparencia.gov.br`  
Auth header: `chave-api-dados: <API_KEY>`  
Rate limit: 400 req/min (dia) · 700 req/min (00h–06h)  
Docs: https://api.portaldatransparencia.gov.br/swagger-ui/index.html

---

## Despesas — Fluxo principal do app

### Documentos por Favorecido ⭐ (busca inicial)
```
GET /api-de-dados/despesas/documentos-por-favorecido
```
| Param | Tipo | Req | Descrição |
|-------|------|-----|-----------|
| `codigoPessoa` | string | ✅ | CNPJ/CPF/código SIAFI sem pontuação |
| `fase` | int | ✅ | 1=Empenho 2=Liquidação 3=Pagamento |
| `ano` | int | ✅ | Ano do documento |
| `pagina` | int | ✅ | Default: 1 (15 items/página) |
| `ug` | string | | Unidade gestora |
| `gestao` | string | | Código de gestão |
| `ordenacaoResultado` | int | | 1=Valor↑ 2=Valor↓ 3=Data↑ 4=Data↓ |

### Documento por Código ⭐ (detalhes do empenho)
```
GET /api-de-dados/despesas/documentos/{codigo}
```
| Param | Tipo | Req | Descrição |
|-------|------|-----|-----------|
| `codigo` | path | ✅ | UG + Gestão + Número do documento |

---

## Detalhamento do Gasto ⭐ (enrichment)

### Itens de Empenho
```
GET /api-de-dados/despesas/itens-de-empenho
```
> Retorna os **itens** dentro de um documento de empenho (o que foi comprado).

| Param | Tipo | Req | Descrição |
|-------|------|-----|-----------|
| `codigoDocumento` | string | ✅ | Código UG + Gestão + Número |
| `pagina` | int | ✅ | Default: 1 |

### Histórico de Item de Empenho
```
GET /api-de-dados/despesas/itens-de-empenho/historico
```
| Param | Tipo | Req | Descrição |
|-------|------|-----|-----------|
| `codigoDocumento` | string | ✅ | Código do empenho |
| `sequencial` | int | ✅ | Número sequencial do item |
| `pagina` | int | ✅ | Default: 1 |

---

## Dados Relacionados ⭐ (enrichment)

### Documentos Relacionados
```
GET /api-de-dados/despesas/documentos-relacionados
```
> Retorna liquidações e pagamentos vinculados a um empenho (ou vice-versa).

| Param | Tipo | Req | Descrição |
|-------|------|-----|-----------|
| `codigoDocumento` | string | ✅ | UG + Gestão + Número |
| `fase` | int | ✅ | 1=Empenho 2=Liquidação 3=Pagamento |

### Empenhos Impactados
```
GET /api-de-dados/despesas/empenhos-impactados
```
> Dado uma liquidação ou pagamento, retorna os empenhos afetados.

| Param | Tipo | Req | Descrição |
|-------|------|-----|-----------|
| `codigoDocumento` | string | ✅ | Código do documento |
| `fase` | int | ✅ | 2=Liquidação ou 3=Pagamento apenas |
| `pagina` | int | ✅ | Default: 1 |

### Favorecidos Finais por Documento
```
GET /api-de-dados/despesas/favorecidos-finais-por-documento
```
| Param | Tipo | Req | Descrição |
|-------|------|-----|-----------|
| `codigoDocumento` | string | ✅ | Código do documento |
| `pagina` | int | ✅ | Default: 1 |

---

## Todos os Documentos (por data)
```
GET /api-de-dados/despesas/documentos
```
| Param | Tipo | Req | Descrição |
|-------|------|-----|-----------|
| `dataEmissao` | string | ✅ | DD/MM/AAAA — máx janela de 1 dia |
| `fase` | int | ✅ | 1/2/3 |
| `pagina` | int | ✅ | Default: 1 |
| `unidadeGestora` | string | | Código SIAFI |
| `gestao` | string | | Código de gestão |

---

## Empresa / CNPJ
```
GET /api-de-dados/pessoa-juridica?cnpj=<CNPJ>
```
> Dados cadastrais da empresa favorecida. Útil para enriquecer o perfil do fornecedor.

---

## Sanções e Impedimentos (compliance)

```
GET /api-de-dados/ceis          # Cadastro de Empresas Inidôneas e Suspensas
GET /api-de-dados/ceis/{id}
GET /api-de-dados/cnep          # Cadastro Nacional de Empresas Punidas
GET /api-de-dados/cnep/{id}
GET /api-de-dados/cepim         # Entidades privadas sem fins lucrativos impedidas
GET /api-de-dados/cepim/{id}
GET /api-de-dados/ceaf          # Cadastro de Exclusão Administrativa Federal
GET /api-de-dados/ceaf/{id}
```
> Todos aceitam `cnpj` como parâmetro de busca.

---

## Notas Fiscais
```
GET /api-de-dados/notas-fiscais
```
| Param | Tipo | Req | Descrição |
|-------|------|-----|-----------|
| `cnpj` | string | | CNPJ do emitente |
| `orgao` | string | | Órgão receptor |
| `produto` | string | | Descrição do produto |

```
GET /api-de-dados/notas-fiscais-por-chave
```
| Param | Tipo | Req | Descrição |
|-------|------|-----|-----------|
| `chave` | string | ✅ | Chave única da NF-e |

---

## Convênios
```
GET /api-de-dados/convenios
GET /api-de-dados/convenios/numero
GET /api-de-dados/convenios/numero-processo
GET /api-de-dados/convenios/id
```
> Transferências voluntárias a estados, municípios e entidades privadas.

---

## Despesas por Classificação

```
GET /api-de-dados/despesas/por-orgao
```
| Param | Obrig | |
|-------|-------|---|
| `ano` | ✅ | |
| `pagina` | ✅ | |
| `orgaoSuperior` / `orgao` | | |

```
GET /api-de-dados/despesas/por-funcional-programatica
GET /api-de-dados/despesas/por-funcional-programatica/movimentacao-liquida
GET /api-de-dados/despesas/recursos-recebidos
GET /api-de-dados/despesas/plano-orcamentario
```

### Dimensões (lookup tables)
```
GET /api-de-dados/despesas/funcional-programatica/funcoes
GET /api-de-dados/despesas/funcional-programatica/subfuncoes
GET /api-de-dados/despesas/funcional-programatica/programas
GET /api-de-dados/despesas/funcional-programatica/acoes
GET /api-de-dados/despesas/funcional-programatica/listar
GET /api-de-dados/orgaos-siafi
GET /api-de-dados/orgaos-siape
```

---

## Outros endpoints relevantes

| Endpoint | Descrição |
|----------|-----------|
| `GET /api-de-dados/cartoes` | Gastos com cartão corporativo (período, órgão, portador, favorecido) |
| `GET /api-de-dados/emendas` | Emendas parlamentares |
| `GET /api-de-dados/emendas/documentos/{codigo}` | Docs vinculados a emenda |
| `GET /api-de-dados/servidores` | Servidores do executivo federal |
| `GET /api-de-dados/servidores/remuneracao` | Remunerações por CPF + mês/ano |
| `GET /api-de-dados/peps` | Pessoas Expostas Politicamente |
| `GET /api-de-dados/viagens` | Viagens a serviço |
| `GET /api-de-dados/pessoa-fisica` | Dados de CPF/NIS |

---

## Mapeamento enrichment_json (por SearchResult)

Campos planejados para `enrichment_json` JSONB:

```json
{
  "itens_empenho": [...],          // /itens-de-empenho
  "documentos_relacionados": [...], // /documentos-relacionados (fase=1)
  "favorecidos_finais": [...],      // /favorecidos-finais-por-documento
  "empresa": {...},                 // /pessoa-juridica
  "sancoes": {
    "ceis": [...],
    "cnep": [...],
    "cepim": [...]
  },
  "notas_fiscais": [...]            // /notas-fiscais (por CNPJ)
}
```
