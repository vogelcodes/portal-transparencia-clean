"""
Test enrichment endpoints using known empenho 2025NE000587.
Usage: python test_enrichment.py
"""
import json
import requests

api_key = None
try:
    with open(".env.local") as f:
        for line in f:
            if line.startswith("API_KEY_PORTAL="):
                api_key = line.strip().split("=", 1)[1]
                break
except FileNotFoundError:
    print("ERROR: .env.local not found"); exit(1)

HEADERS = {"chave-api-dados": api_key, "Accept": "application/json"}
BASE = "https://api.portaldatransparencia.gov.br/api-de-dados"
CNPJ = "47149673000171"
TARGET = "2025NE000587"


def get(path, params=None):
    r = requests.get(f"{BASE}{path}", headers=HEADERS, params=params, timeout=10)
    print(f"  [{r.status_code}] GET {path}" + (f"  params={params}" if params else ""))
    if r.status_code == 200:
        return r.json()
    print(f"  ERROR: {r.text[:300]}")
    return None


def pp(obj):
    print(json.dumps(obj, ensure_ascii=False, indent=2))


# ── 1. Find full codigoDocumento for 2025NE000587 ─────────────────────────────
print(f"\n{'='*60}")
print(f"1. Localizando {TARGET} via documentos-por-favorecido")
print('='*60)

doc_id = None
for pagina in range(1, 10):
    data = get("/despesas/documentos-por-favorecido", {
        "codigoPessoa": CNPJ, "ano": 2025, "fase": 1, "pagina": pagina
    })
    if not data:
        break
    for item in data:
        if item.get("documentoResumido") == TARGET:
            doc_id = item["documento"]
            print(f"\n  ENCONTRADO!")
            print(f"  codigoDocumento (completo): {doc_id}")
            print(f"  documentoResumido:          {item['documentoResumido']}")
            print(f"  valor:                      {item['valor']}")
            print(f"  orgao:                      {item['orgao']}")
            break
    if doc_id or len(data) < 15:
        break

if not doc_id:
    print(f"  {TARGET} não encontrado. Abortando."); exit(1)


# ── 2. Detalhes do documento ──────────────────────────────────────────────────
print(f"\n{'='*60}")
print("2. Detalhes do empenho")
print('='*60)
detail = get(f"/despesas/documentos/{doc_id}")
if detail:
    print(f"\n  Campos disponíveis: {list(detail.keys())}")
    print(f"\n  favorecido:      {detail.get('nomeFavorecido')}")
    print(f"  codigoFavorecido:{detail.get('codigoFavorecido')}")
    print(f"  valor:           {detail.get('valor')}")
    print(f"  numeroProcesso:  {detail.get('numeroProcesso')}")
    print(f"  observacao:      {detail.get('observacao', '')[:100]}")


# ── 3. Itens de empenho (detalhamento do gasto) ───────────────────────────────
print(f"\n{'='*60}")
print("3. Itens de empenho (detalhamento do gasto)")
print('='*60)
itens = get("/despesas/itens-de-empenho", {"codigoDocumento": doc_id, "pagina": 1})
if itens:
    print(f"\n  {len(itens)} itens encontrados")
    print(f"  Campos: {list(itens[0].keys())}")
    print()
    for item in itens:
        print(f"  Seq {item['sequencial']} | {item['descricao'][:60]}")
        print(f"           subelemento: {item['codigoSubelemento']} - {item['descricaoSubelemento']}")
        print(f"           valor atual: {item['valorAtual']}")
else:
    print("  Nenhum item retornado")


# ── 4. Documentos relacionados ────────────────────────────────────────────────
print(f"\n{'='*60}")
print("4. Documentos relacionados (fase=1 = empenho)")
print('='*60)
relacionados = get("/despesas/documentos-relacionados", {
    "codigoDocumento": doc_id, "fase": 1
})
if relacionados:
    print(f"\n  {len(relacionados)} documentos relacionados")
    print(f"  Campos: {list(relacionados[0].keys())}")
    print()
    for rel in relacionados:
        print(f"  {rel.get('data')} | {rel.get('especie','?')} | {rel.get('documentoResumido') or rel.get('documento')}")
else:
    print("  Nenhum. Tentando fase=2 (liquidação)...")
    relacionados2 = get("/despesas/documentos-relacionados", {
        "codigoDocumento": doc_id, "fase": 2
    })
    if relacionados2:
        print(f"\n  {len(relacionados2)} docs (fase=2)")
        pp(relacionados2[0])


# ── 5. Pessoa jurídica ────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print("5. Pessoa jurídica (empresa)")
print('='*60)
empresa = get("/pessoa-juridica", {"cnpj": CNPJ})
if empresa:
    print(f"\n  Razão social:   {empresa.get('razaoSocial')}")
    print(f"  Nome fantasia:  {empresa.get('nomeFantasia')}")
    print(f"  Sancionado CEIS:{empresa.get('sancionadoCEIS')}")
    print(f"  Sancionado CNEP:{empresa.get('sancionadoCNEP')}")
    print(f"  Possui contrato:{empresa.get('possuiContratacao')}")
    print(f"  Participa licit:{empresa.get('participanteLicitacao')}")
    print(f"  Emitiu NF-e:    {empresa.get('emitiuNFe')}")
    print(f"\n  Todos os campos: {list(empresa.keys())}")


# ── 6. Resumo ─────────────────────────────────────────────────────────────────
print(f"\n{'='*60}")
print("RESUMO — enrichment_json shape esperado por resultado:")
print('='*60)
print("""
{
  "itens_empenho": [
    { "sequencial", "descricao", "codigoSubelemento",
      "descricaoSubelemento", "valorAtual" }
  ],
  "documentos_relacionados": [
    { "data", "especie", "documento", "documentoResumido", ... }
  ],
  "empresa": {
    "razaoSocial", "nomeFantasia",
    "sancionadoCEIS", "sancionadoCNEP", "sancionadoCEPIM",
    "possuiContratacao", "participanteLicitacao", "emitiuNFe"
  }
}
""")
