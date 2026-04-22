# UI Kit — Portal da Transparência (Empenho)

Recreation of the public `portaldatransparencia.gov.br` Empenho search + detail flow.

- `index.html` — mounts the interactive prototype
- `GovbrBar.jsx` — the black institutional strip (gov.br branding + util links)
- `PortalHeader.jsx` — Portal-scoped header with logo, search, login
- `Breadcrumb.jsx` — standard breadcrumb
- `SearchPanel.jsx` — Empenho search form with filters
- `ResultList.jsx` — tabular list of empenhos
- `EmpenhoDetail.jsx` — the detail view for a single empenho
- `Footer.jsx` — CGU institutional footer

Flow: landing (search form) → submit → results list → click row → detail page. Data is fake but formatted in the real gov.br conventions (`R$ 1.234,56`, `DD/MM/AAAA`, `2024NE800123`).

All components read from `colors_and_type.css` at the project root.
