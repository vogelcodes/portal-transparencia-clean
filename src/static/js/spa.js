(() => {
  const app = document.getElementById('spa-app');
  if (!app) return;

  const brNumber = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 2 });

  function statusClass(status) {
    if (status === 'done') return 'status-done';
    if (status === 'pending') return 'status-pending';
    if (status === 'syncing') return 'status-syncing';
    if (status === 'error') return 'status-error';
    return 'status-unknown';
  }

  function empenhoLabel(percentual) {
    if (percentual >= 90) return 'Crítico (quase esgotado)';
    if (percentual >= 60) return 'Atenção';
    if (percentual > 0) return 'Em andamento';
    return 'Sem empenho';
  }

  function money(v) {
    if (v === null || v === undefined) return '—';
    return `R$ ${brNumber.format(Number(v))}`;
  }

  async function apiGet(url) {
    const response = await fetch(url, { headers: { Accept: 'application/json' } });
    if (!response.ok) throw new Error(`Erro ${response.status}`);
    return response.json();
  }

  function dashboardHtml(data) {
    const totals = data.uasgs.reduce((acc, u) => {
      acc.arps += u.arp_count;
      acc.itens += u.item_count;
      acc.empenhos += u.empenho_count;
      return acc;
    }, { arps: 0, itens: 0, empenhos: 0 });

    return `
      <section class="spa-grid">
        <article class="card metric-card">
          <div class="font-label-sm text-on-surface-variant">UASGs</div>
          <div class="font-display-lg">${data.uasgs.length}</div>
        </article>
        <article class="card metric-card">
          <div class="font-label-sm text-on-surface-variant">ARPs</div>
          <div class="font-display-lg">${totals.arps}</div>
        </article>
        <article class="card metric-card">
          <div class="font-label-sm text-on-surface-variant">Itens</div>
          <div class="font-display-lg">${totals.itens}</div>
        </article>
        <article class="card metric-card">
          <div class="font-label-sm text-on-surface-variant">Empenhos</div>
          <div class="font-display-lg">${totals.empenhos}</div>
        </article>
      </section>

      <section class="card">
        <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;">
          <h2 class="font-headline-md">UASGs</h2>
          <small class="text-on-surface-variant">cache: ${data.cache.cached ? 'HIT' : 'MISS'} (${data.cache.ttl_seconds}s)</small>
        </div>
        <div style="display:grid;gap:10px;">
          ${data.uasgs.map((u) => `
            <article class="card arp-card">
              <div style="display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap;">
                <div>
                  <div><strong>${u.nome_uasg || u.codigo_uasg}</strong> <span class="text-on-surface-variant">(${u.codigo_uasg})</span></div>
                  <div class="item-meta">${u.nome_municipio || ''} ${u.sigla_uf ? `- ${u.sigla_uf}` : ''}</div>
                </div>
                <span class="status-pill ${statusClass(u.sync_status)}">${u.sync_status}</span>
              </div>
              <div class="spa-grid" style="margin-top:10px;">
                <div><strong>${u.arp_count}</strong><div class="item-meta">ARPs</div></div>
                <div><strong>${u.item_count}</strong><div class="item-meta">Itens</div></div>
                <div><strong>${u.empenho_count}</strong><div class="item-meta">Empenhos</div></div>
              </div>
              <div style="margin-top:10px;">
                <a class="btn btn-secondary" href="#/uasg/${u.id}">Ver situação dos empenhos</a>
              </div>
            </article>
          `).join('') || '<p>Sem UASGs.</p>'}
        </div>
      </section>
    `;
  }

  function uasgHtml(data) {
    const u = data.uasg;
    return `
      <section class="card">
        <a href="#/" class="btn btn-ghost">← Voltar</a>
        <h2 class="font-headline-md" style="margin-top:8px;">${u.nome_uasg || u.codigo_uasg}</h2>
        <div class="item-meta">${u.codigo_uasg} • ${u.nome_municipio || '—'} ${u.sigla_uf || ''}</div>
      </section>

      <section class="card">
        <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;">
          <h3 class="font-headline-md">ARPs (${data.arps.length})</h3>
          <small class="text-on-surface-variant">cache: ${data.cache.cached ? 'HIT' : 'MISS'}</small>
        </div>
        <div style="display:grid;gap:12px;">
          ${data.arps.map((arp) => `
            <article class="card arp-card">
              <div style="display:flex;justify-content:space-between;gap:8px;flex-wrap:wrap;">
                <div>
                  <div><strong>${arp.numero_ata_registro_preco || arp.numero_controle_pncp_ata}</strong></div>
                  <div class="item-meta">${arp.objeto || 'Sem objeto'}</div>
                </div>
                <div style="min-width:180px;">
                  <div class="item-meta">Situação da ARP: ${empenhoLabel(arp.percentual_empenhado)}</div>
                  <div class="progress-wrap"><div class="progress-bar" style="width:${arp.percentual_empenhado}%;"></div></div>
                  <div class="item-meta">${arp.percentual_empenhado}% empenhado (${brNumber.format(arp.total_quantidade_empenhada)} / ${brNumber.format(arp.total_quantidade_homologada)})</div>
                </div>
              </div>

              ${arp.itens.map((item) => `
                <div class="item-card">
                  <div class="item-header">
                    <div>
                      <strong>Item ${item.numero_item}</strong> — ${item.descricao || 'Sem descrição'}
                      <div class="item-meta">Fornecedor: ${item.fornecedor || '—'} ${item.fornecedor_documento ? `(${item.fornecedor_documento})` : ''}</div>
                      <div class="item-meta">Valor unitário: ${money(item.valor_unitario)} | Valor total: ${money(item.valor_total)}</div>
                    </div>
                    <div style="min-width:180px;">
                      <div class="item-meta">Situação: ${empenhoLabel(item.percentual_empenhado)}</div>
                      <div class="progress-wrap"><div class="progress-bar" style="width:${item.percentual_empenhado}%;"></div></div>
                      <div class="item-meta">${item.percentual_empenhado}% (${brNumber.format(item.quantidade_empenhada_total)} / ${brNumber.format(item.quantidade_homologada)})</div>
                    </div>
                  </div>

                  ${item.empenhos.length ? `
                    <table class="small-table">
                      <thead>
                        <tr>
                          <th>Unidade</th>
                          <th>Tipo</th>
                          <th>Qtd. empenhada</th>
                        </tr>
                      </thead>
                      <tbody>
                        ${item.empenhos.map((e) => `
                          <tr>
                            <td>${e.unidade || '—'}</td>
                            <td>${e.tipo || '—'}</td>
                            <td>${e.quantidade_empenhada ?? '—'}</td>
                          </tr>
                        `).join('')}
                      </tbody>
                    </table>
                  ` : '<div class="item-meta" style="margin-top:8px;">Sem empenhos neste item.</div>'}
                </div>
              `).join('')}
            </article>
          `).join('') || '<p>Nenhuma ARP encontrada.</p>'}
        </div>
      </section>
    `;
  }

  async function renderRoute() {
    app.innerHTML = '<section class="card">Carregando...</section>';
    try {
      const hash = location.hash || '#/';
      const match = hash.match(/^#\/uasg\/(\d+)$/);
      if (match) {
        const data = await apiGet(`/api/spa/uasg/${match[1]}`);
        app.innerHTML = uasgHtml(data);
        return;
      }

      const data = await apiGet('/api/spa/dashboard');
      app.innerHTML = dashboardHtml(data);
    } catch (err) {
      app.innerHTML = `<section class="card"><strong>Falha ao carregar SPA.</strong><div class="item-meta">${err.message}</div></section>`;
    }
  }

  window.addEventListener('hashchange', renderRoute);
  renderRoute();
})();
