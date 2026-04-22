# Portal da Transparência - API Documentation

> **Official API**: `https://api.portaldatransparencia.gov.br`  
> **Swagger UI**: [http://api.portaldatransparencia.gov.br](http://api.portaldatransparencia.gov.br)  
> **OpenAPI Spec**: `/v3/api-docs`  
> **Contact**: listaapitransparencia@cgu.gov.br

## Overview

This is the official REST API for the Brazilian Federal Government's Transparency Portal (Portal da Transparência). The API provides programmatic access to public federal government data including contracts, bids, expenses, civil servants, and social benefits.

**No browser automation required** - This is a public API designed for programmatic access.

---

## Authentication

The API requires an API key passed via the `Authorization` header.

```http
GET /api-de-dados/contratos?pagina=1&codigoOrgao=25000
Authorization: Bearer YOUR_API_KEY
```

> **Note**: To get an API key, register at the [Portal da Transparência](https://portaldatransparencia.gov.br).
"[{"key":"chave-api-dados","value":"3072e25079414eb2e9136328173d9cf0"}]

---

## Common Parameters

Most endpoints share these common query parameters:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `pagina` | integer | Yes | Page number (default: 1) |
| `dataInicial` | string | Varies | Start date (DD/MM/YYYY) |
| `dataFinal` | string | Varies | End date (DD/MM/YYYY) |
| `codigoOrgao` | string | Varies | SIAFI organ code |

---

## API Endpoints by Category

### 1. Contratos (Contracts)

#### List All Contracts
```http
GET /api-de-dados/contratos
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `codigoOrgao` | string | Yes | SIAFI organ code |
| `dataInicial` | string | No | Start date (DD/MM/YYYY) |
| `dataFinal` | string | No | End date (DD/MM/YYYY) |
| `pagina` | integer | Yes | Page number |

**Response:** `ContratoDTO[]`
```json
{
  "id": 12345,
  "numero": "12345/2024",
  "objeto": "Contract description",
  "numeroProcesso": "00000.000000/2024-00",
  "fundamentoLegal": "Lei 14.133/2021",
  "situacaoContrato": "Vigente",
  "modalidadeCompra": "Pregão Eletrônico",
  "dataAssinatura": "2024-01-15",
  "dataInicioVigencia": "2024-01-20",
  "dataFimVigencia": "2025-01-20",
  "valorInicialCompra": 100000.00,
  "valorFinalCompra": 95000.00,
  "fornecedor": {
    "id": 1,
    "cnpjFormatado": "00.000.000/0001-00",
    "nome": "Company Name"
  },
  "unidadeGestora": {
    "codigo": "123456",
    "nome": "Managing Unit Name"
  }
}
```

#### Get Contract by ID
```http
GET /api-de-dados/contratos/id?id={id}
```

#### Get Contract by Number
```http
GET /api-de-dados/contratos/numero?numero={numero}&pagina=1
```

#### Get Contract by Process Number
```http
GET /api-de-dados/contratos/processo?processo={processo}&pagina=1
```

#### Get Contracts by Supplier CPF/CNPJ
```http
GET /api-de-dados/contratos/cpf-cnpj?cpfCnpj={cpfCnpj}&pagina=1
```

#### Get Contract Items
```http
GET /api-de-dados/contratos/itens-contratados?id={contratoId}&pagina=1
```

**Response:** `ItemContratadoDTO[]`

#### Get Contract Amendments (Termos Aditivos)
```http
GET /api-de-dados/contratos/termo-aditivo?id={contratoId}
```

**Response:** `TermoAditivoDTO[]`

#### Get Contract Endorsements (Apostilamentos)
```http
GET /api-de-dados/contratos/apostilamento?id={contratoId}
```

**Response:** `ApostilamentoDTO[]`

#### Get Related Documents
```http
GET /api-de-dados/contratos/documentos-relacionados?id={contratoId}
```

**Response:** `EmpenhoComprasDTO[]`

---

### 2. Licitações (Bids/Procurements)

#### List All Bids
```http
GET /api-de-dados/licitacoes
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `codigoOrgao` | string | Yes | SIAFI organ code |
| `dataInicial` | string | No | Opening date start (DD/MM/YYYY) |
| `dataFinal` | string | No | Opening date end (DD/MM/YYYY) |
| `pagina` | integer | Yes | Page number |

**Response:** `LicitacaoDTO[]`
```json
{
  "id": 67890,
  "licitacao": {
    "numero": "1/2024",
    "objeto": "Procurement description",
    "numeroProcesso": "00000.000000/2024-00"
  },
  "dataAbertura": "2024-02-01",
  "dataResultadoCompra": "2024-02-15",
  "situacaoCompra": "Homologada",
  "modalidadeLicitacao": "Pregão Eletrônico",
  "valor": 500000.00,
  "unidadeGestora": {...},
  "municipio": {...}
}
```

#### Get Bid by ID
```http
GET /api-de-dados/licitacoes/{id}
```

#### Get Bid by UG/Modality/Number
```http
GET /api-de-dados/licitacoes/por-ug-modalidade-numero?codigoUG={ug}&numero={numero}&codigoModalidade={mod}
```

#### Get Bid by Process Number
```http
GET /api-de-dados/licitacoes/por-processo?processo={processo}
```

#### Get Bid Items
```http
GET /api-de-dados/licitacoes/itens-licitados?id={licitacaoId}&pagina=1
```

#### Get Bid Participants
```http
GET /api-de-dados/licitacoes/participantes?codigoUG={ug}&numero={numero}&codigoModalidade={mod}&pagina=1
```

#### Get Related Contracts
```http
GET /api-de-dados/licitacoes/contratos-relacionados-licitacao?codigoUG={ug}&numero={numero}&codigoModalidade={mod}
```

#### Get Bid Modalities
```http
GET /api-de-dados/licitacoes/modalidades
```

**Response:** `CodigoDescricaoDTO[]` (list of modality codes and descriptions)

#### Get Managing Units
```http
GET /api-de-dados/licitacoes/ugs?pagina=1
```

---

### 3. Despesas (Public Expenses)

#### By Organization
```http
GET /api-de-dados/despesas/por-orgao
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `ano` | integer | Yes | Year (YYYY) |
| `orgaoSuperior` | string | No | Superior organ (SIAFI code) |
| `orgao` | string | No | Linked organ (SIAFI code) |
| `pagina` | integer | Yes | Page number |

**Response:** `DespesaAnualPorOrgaoDTO[]`

#### By Functional Classification
```http
GET /api-de-dados/despesas/por-funcional-programatica
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `ano` | integer | Yes | Year |
| `funcao` | string | No | Function (SIAFI code) |
| `subfuncao` | string | No | Subfunction (SIAFI code) |
| `programa` | string | No | Program (SIAFI code) |
| `acao` | string | No | Action (SIAFI code) |
| `pagina` | integer | Yes | Page number |

#### Documents by Date
```http
GET /api-de-dados/despesas/documentos
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `dataEmissao` | string | Yes | Emission date (DD/MM/YYYY) - single day only |
| `fase` | integer | Yes | Phase (1=Commitment, 2=Settlement, 3=Payment) |
| `unidadeGestora` | string | No | Managing unit (SIAFI) |
| `pagina` | integer | Yes | Page number |

#### Document by Code
```http
GET /api-de-dados/despesas/documentos/{codigo}
```

#### Documents by Beneficiary
```http
GET /api-de-dados/despesas/documentos-por-favorecido
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `codigoPessoa` | string | Yes | CPF, CNPJ, or SIAFI code |
| `fase` | integer | Yes | Phase (1, 2, or 3) |
| `ano` | integer | Yes | Year |
| `pagina` | integer | Yes | Page number |

#### Resources Received
```http
GET /api-de-dados/despesas/recursos-recebidos
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `mesAnoInicio` | string | Yes | Start month/year (MM/YYYY) |
| `mesAnoFim` | string | Yes | End month/year (MM/YYYY) |
| `codigoFavorecido` | string | No | CPF/CNPJ |
| `pagina` | integer | Yes | Page number |

---

### 4. Servidores (Federal Civil Servants)

#### List Servants
```http
GET /api-de-dados/servidores
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `tipoServidor` | integer | No | Type (1=Civil, 2=Military) |
| `situacaoServidor` | integer | No | Status (1=Active, 2=Inactive, 3=Pensioner) |
| `cpf` | string | No | CPF number |
| `nome` | string | No | Name |
| `orgaoServidorLotacao` | string | No | SIAPE organ code (assignment) |
| `orgaoServidorExercicio` | string | No | SIAPE organ code (exercise) |
| `pagina` | integer | Yes | Page number |

**Response:** `CadastroServidorDTO[]`

#### Get Servant by ID
```http
GET /api-de-dados/servidores/{id}
```

#### Get Servant Remuneration
```http
GET /api-de-dados/servidores/remuneracao
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `cpf` | string | Conditional | CPF (required if no `id`) |
| `id` | integer | Conditional | Servant ID (required if no `cpf`) |
| `mesAno` | integer | Yes | Month/Year (YYYYMM) |
| `pagina` | integer | Yes | Page number |

**Response:** `ServidorRemuneracaoDTO[]` - includes base salary, deductions, bonuses

#### Servants by Organization
```http
GET /api-de-dados/servidores/por-orgao?pagina=1
```

#### Functions and Positions
```http
GET /api-de-dados/servidores/funcoes-e-cargos?pagina=1
```

#### Politically Exposed Persons (PEPs)
```http
GET /api-de-dados/peps
```

---

### 5. Órgãos (Government Organizations)

#### SIAFI Organizations
```http
GET /api-de-dados/orgaos-siafi
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `codigo` | string | No | SIAFI code |
| `descricao` | string | No | Description |
| `pagina` | integer | Yes | Page number |

**Response:** `CodigoDescricaoDTO[]`

#### SIAPE Organizations
```http
GET /api-de-dados/orgaos-siape
```

---

### 6. Convênios (Agreements/Grants)

#### List Agreements
```http
GET /api-de-dados/convenios
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `dataInicial` | string | No | Reference date start (DD/MM/YYYY) |
| `dataFinal` | string | No | Reference date end (DD/MM/YYYY) |
| `codigoOrgao` | string | No | SIAFI organ code |
| `numero` | string | No | Agreement number |
| `uf` | string | No | State abbreviation |
| `codigoIBGE` | string | No | Municipality IBGE code |
| `pagina` | integer | Yes | Page number |

**Response:** `ConvenioDTO[]`

#### Get Agreement by ID
```http
GET /api-de-dados/convenios/id?id={id}
```

#### Get Agreement by Number
```http
GET /api-de-dados/convenios/numero?numero={numero}&pagina=1
```

#### Agreement Instrument Types
```http
GET /api-de-dados/convenios/tipo-instrumento
```

---

### 7. Benefícios Sociais (Social Benefits)

#### Bolsa Família (by Municipality)
```http
GET /api-de-dados/bolsa-familia-por-municipio
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `mesAno` | integer | Yes | Month/Year (YYYYMM) |
| `codigoIbge` | string | Yes | IBGE municipality code |
| `pagina` | integer | Yes | Page number |

#### Bolsa Família (by NIS)
```http
GET /api-de-dados/bolsa-familia-sacado-por-nis
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `nis` | string | Yes | NIS number (numbers only) |
| `anoMesReferencia` | integer | No | Reference month/year (YYYYMM) |
| `anoMesCompetencia` | integer | No | Competency month/year (YYYYMM) |
| `pagina` | integer | Yes | Page number |

#### Novo Bolsa Família
```http
GET /api-de-dados/novo-bolsa-familia-por-municipio
GET /api-de-dados/novo-bolsa-familia-sacado-por-nis
GET /api-de-dados/novo-bolsa-familia-sacado-beneficiario-por-municipio
```

#### Auxílio Brasil
```http
GET /api-de-dados/auxilio-brasil-por-municipio
GET /api-de-dados/auxilio-brasil-sacado-por-nis
GET /api-de-dados/auxilio-brasil-sacado-beneficiario-por-municipio
```

#### Auxílio Emergencial (COVID-19)
```http
GET /api-de-dados/auxilio-emergencial-por-municipio
GET /api-de-dados/auxilio-emergencial-por-cpf-ou-nis
GET /api-de-dados/auxilio-emergencial-beneficiario-por-municipio
```

#### BPC (Continuous Payment Benefit)
```http
GET /api-de-dados/bpc-por-municipio
GET /api-de-dados/bpc-por-cpf-ou-nis
GET /api-de-dados/bpc-beneficiario-por-municipio
```

#### Garantia-Safra
```http
GET /api-de-dados/safra-por-municipio
GET /api-de-dados/safra-codigo-por-cpf-ou-nis
GET /api-de-dados/safra-beneficiario-por-municipio
```

#### Seguro Defeso
```http
GET /api-de-dados/seguro-defeso-por-municipio
GET /api-de-dados/seguro-defeso-codigo
GET /api-de-dados/seguro-defeso-beneficiario-por-municipio
```

#### PETI (Child Labor Eradication)
```http
GET /api-de-dados/peti-por-municipio
GET /api-de-dados/peti-por-cpf-ou-nis
GET /api-de-dados/peti-beneficiario-por-municipio
```

---

### 8. Sanções (Sanctions)

#### CEIS (Ineligible Companies)
```http
GET /api-de-dados/ceis
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `codigoSancionado` | string | No | CPF or CNPJ |
| `nomeSancionado` | string | No | Name/Trade name |
| `orgaoSancionador` | string | No | Sanctioning body |
| `dataInicialSancao` | string | No | Start date (DD/MM/YYYY) |
| `dataFinalSancao` | string | No | End date (DD/MM/YYYY) |
| `pagina` | integer | Yes | Page number |

```http
GET /api-de-dados/ceis/{id}
```

#### CNEP (Non-Profit Entities)
```http
GET /api-de-dados/cnep
GET /api-de-dados/cnep/{id}
```

#### CEPIM (Impeded Entities)
```http
GET /api-de-dados/cepim
GET /api-de-dados/cepim/{id}
```

#### CEAF (Federal Servants Expulsion)
```http
GET /api-de-dados/ceaf
GET /api-de-dados/ceaf/{id}
```

#### Leniency Agreements
```http
GET /api-de-dados/acordos-leniencia
GET /api-de-dados/acordos-leniencia/{id}
```

---

### 9. Viagens (Official Travel)

#### List Travels
```http
GET /api-de-dados/viagens
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `dataIdaDe` | string | Yes | Departure date from (DD/MM/YYYY) |
| `dataIdaAte` | string | Yes | Departure date to (DD/MM/YYYY) |
| `dataRetornoDe` | string | Yes | Return date from (DD/MM/YYYY) |
| `dataRetornoAte` | string | Yes | Return date to (DD/MM/YYYY) |
| `codigoOrgao` | string | Yes | SIAFI organ code |
| `pagina` | integer | Yes | Page number |

> **Note**: Maximum period of 1 month allowed.

**Response:** `ViagemDTO[]`

#### Get Travel by ID
```http
GET /api-de-dados/viagens/{id}
```

#### Travels by CPF
```http
GET /api-de-dados/viagens-por-cpf?cpf={cpf}&pagina=1
```

---

### 10. Cartões de Pagamento (Payment Cards)

```http
GET /api-de-dados/cartoes
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `mesExtratoInicio` | string | No | Statement start (MM/YYYY) |
| `mesExtratoFim` | string | No | Statement end (MM/YYYY) |
| `tipoCartao` | integer | No | Card type (1=CPGF, 2=CPCC, 3=CPDC) |
| `codigoOrgao` | string | No | SIAFI organ code |
| `cpfPortador` | string | No | Cardholder CPF |
| `cpfCnpjFavorecido` | string | No | Merchant CPF/CNPJ |
| `pagina` | integer | Yes | Page number |

---

### 11. Notas Fiscais (Electronic Invoices)

#### List Invoices
```http
GET /api-de-dados/notas-fiscais
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `cnpjEmitente` | string | No | Issuer CNPJ |
| `codigoOrgao` | string | No | SIAFI organ code |
| `nomeProduto` | string | No | Product name |
| `pagina` | integer | Yes | Page number |

#### Get Invoice by Key
```http
GET /api-de-dados/notas-fiscais-por-chave?chaveUnicaNotaFiscal={chave}
```

---

### 12. Imóveis Funcionais (Government Properties)

#### List Properties
```http
GET /api-de-dados/imoveis
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `codigoOrgaoSiafiResponsavelGestao` | string | No | Responsible organ (SIAFI) |
| `situacao` | string | No | Property status |
| `regiao` | string | No | Region |
| `cep` | string | No | ZIP code |
| `endereco` | string | No | Address |
| `pagina` | integer | Yes | Page number |

#### Property Statuses
```http
GET /api-de-dados/situacao-imovel
```

#### Occupants
```http
GET /api-de-dados/permissionarios
```

---

### 13. Emendas Parlamentares (Parliamentary Amendments)

```http
GET /api-de-dados/emendas
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `codigoEmenda` | string | No | Amendment code |
| `numeroEmenda` | string | No | Amendment number |
| `nomeAutor` | string | No | Author name |
| `tipoEmenda` | string | No | Amendment type |
| `ano` | integer | No | Year |
| `pagina` | integer | Yes | Page number |

#### Related Documents
```http
GET /api-de-dados/emendas/documentos/{codigo}
```

---

### 14. Renúncias Fiscais (Tax Waivers)

#### Waived Values
```http
GET /api-de-dados/renuncias-valor
```

#### Immune/Exempt Companies
```http
GET /api-de-dados/renuncias-fiscais-empresas-imunes-isentas
```

#### Companies with Tax Benefits
```http
GET /api-de-dados/renuncias-fiscais-empresas-habilitadas-beneficios-fiscais
```

---

### 15. Pessoas (People/Entities)

#### Legal Entities (Companies)
```http
GET /api-de-dados/pessoa-juridica?cnpj={cnpj}
```

**Response:** `PessoaJuridicaDTO`
```json
{
  "cnpj": "00.000.000/0001-00",
  "razaoSocial": "Company Name",
  "nomeFantasia": "Trade Name",
  "favorecidoDespesas": true,
  "possuiContratacao": true,
  "sancionadoCEIS": false,
  "sancionadoCNEP": false,
  ...
}
```

#### Natural Persons
```http
GET /api-de-dados/pessoa-fisica
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `cpf` | string | Conditional | CPF number |
| `nis` | string | Conditional | NIS number |

**Response:** `PessoaFisicaDTO`

---

### 16. Coronavírus (COVID-19 Spending)

#### COVID Transfers
```http
GET /api-de-dados/coronavirus/transferencias
```

**Parameters:**
| Name | Type | Required | Description |
|------|------|----------|-------------|
| `mesAno` | integer | Yes | Month/Year (YYYYMM) |
| `codigoOrgao` | string | No | SIAFI organ code |
| `tipoTransferencia` | integer | No | Transfer type ID |
| `uf` | string | No | State abbreviation |
| `codigoIbge` | string | No | Municipality code |
| `pagina` | integer | Yes | Page number |

#### COVID Net Movement
```http
GET /api-de-dados/coronavirus/movimento-liquido-despesa
```

---

## Data Types Reference

### Common DTO Structures

#### PessoaDTO
```json
{
  "id": 1,
  "cpfFormatado": "000.000.000-00",
  "cnpjFormatado": "00.000.000/0001-00",
  "nome": "Name",
  "tipo": "FISICA|JURIDICA"
}
```

#### MunicipioDTO
```json
{
  "codigoIBGE": "3550308",
  "nomeIBGE": "São Paulo",
  "uf": {
    "sigla": "SP",
    "nome": "São Paulo"
  }
}
```

#### UnidadeGestoraDTO
```json
{
  "codigo": "123456",
  "nome": "Managing Unit Name",
  "descricaoPoder": "Executivo",
  "orgaoVinculado": {...},
  "orgaoMaximo": {...}
}
```

#### OrgaoDTO
```json
{
  "nome": "Organ Name",
  "codigoSIAFI": "25000",
  "cnpj": "00.000.000/0001-00",
  "sigla": "ORG",
  "descricaoPoder": "Executivo"
}
```

---

## Example: Fetching Contracts for Ministry of Economy

```bash
curl -X GET "https://api.portaldatransparencia.gov.br/api-de-dados/contratos?codigoOrgao=25000&pagina=1" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Accept: application/json"
```

---

## Rate Limits and Best Practices

1. **Pagination**: Always use the `pagina` parameter and iterate through results
2. **Date Ranges**: Some endpoints require date ranges of maximum 1 month/day
3. **Required Filters**: Most endpoints require at least one filter besides pagination
4. **Error Handling**: Handle 400 (Bad Request), 401 (Unauthorized), 500 (Server Error)
5. **Caching**: Consider caching responses for reference data (organs, modalities)

---

## Quick Reference - Most Useful Endpoints

| Use Case | Endpoint |
|----------|----------|
| Find contracts by supplier | `/api-de-dados/contratos/cpf-cnpj` |
| List bids for an organ | `/api-de-dados/licitacoes` |
| Check company sanctions | `/api-de-dados/ceis`, `/api-de-dados/cnep` |
| Servant remuneration | `/api-de-dados/servidores/remuneracao` |
| Social benefits by municipality | `/api-de-dados/bolsa-familia-por-municipio` |
| Government expenses | `/api-de-dados/despesas/recursos-recebidos` |

---

## Related Resources

- **Portal Web Interface**: [portaldatransparencia.gov.br](https://portaldatransparencia.gov.br)
- **Swagger UI Documentation**: [api.portaldatransparencia.gov.br](http://api.portaldatransparencia.gov.br)
- **IBGE Municipality Codes**: [cidades.ibge.gov.br](https://cidades.ibge.gov.br/brasil)
- **Legal Basis**: [Decree 8.777/2016](https://www.planalto.gov.br/ccivil_03/_ato2015-2018/2016/decreto/d8777.htm)

---

*Documentation generated from OpenAPI 3.0 specification*  
*Last updated: January 2026*
