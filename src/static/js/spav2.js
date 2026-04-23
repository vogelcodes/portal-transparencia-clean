// Dashboard de ARPs — SPAv2
// Consumes window.SPAV2_PAYLOAD (real UASG data) and renders the
// prototype dashboard (KPIs · ARP list · ARP detail · item breakdown).

const fmtBRL = (n) => 'R$ ' + (n || 0).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const fmtNum = (n) => (Number(n) || 0).toLocaleString('pt-BR');
const pct    = (a, b) => b > 0 ? Math.round((a / b) * 100) : 0;

const TODAY = new Date();

function parseISO(s) {
  if (!s) return null;
  const base = String(s).slice(0, 10);
  const [y, m, d] = base.split('-').map(Number);
  if (!y || !m || !d) return null;
  return new Date(y, m - 1, d);
}
function parseBR(s) {
  const [d, m, y] = s.split('/').map(Number);
  return new Date(y, m - 1, d);
}
function isoToBR(s) {
  const dt = parseISO(s);
  if (!dt) return '—';
  const dd = String(dt.getDate()).padStart(2, '0');
  const mm = String(dt.getMonth() + 1).padStart(2, '0');
  return `${dd}/${mm}/${dt.getFullYear()}`;
}

// --- Adapter: API payload → prototype data shape ---

function adaptPayload(P) {
  const atas = (P.arps || []).map((arp) => {
    const itens = (arp.itens || []).map((it) => ({
      numero:               String(it.numero_item || '').padStart(5, '0'),
      descricao:            it.descricao || '—',
      fornecedor:           it.fornecedor || 'Fornecedor não informado',
      cnpj:                 it.fornecedor_documento || '—',
      quantidadeHomologada: Number(it.quantidade_homologada || 0),
      valorUnitario:        Number(it.valor_unitario || 0),
      valorTotal:           Number(it.valor_total || 0),
      empenhos:             (it.empenhos || []).map((e) => ({
        unidade:    e.unidade    || 'Unidade não informada',
        tipo:       e.tipo       || 'N/A',
        registrada: Number(e.quantidade_registrada || 0),
        empenhada:  Number(e.quantidade_empenhada  || 0),
        saldo:      Number(
          e.saldo_empenho != null
            ? e.saldo_empenho
            : (Number(e.quantidade_registrada || 0) - Number(e.quantidade_empenhada || 0))
        ),
      })),
    }));

    const valorTotal = itens.reduce((s, it) => s + (it.valorTotal || 0), 0);

    return {
      numero:          arp.numero_ata_registro_preco || arp.numero_controle_pncp_ata || '—',
      orgao:           P.uasg?.nome_uasg || '',
      modalidade:      'ARP',
      vigenciaInicial: isoToBR(arp.data_vigencia_inicial),
      vigenciaFinal:   isoToBR(arp.data_vigencia_final),
      valorTotal,
      objeto:          arp.objeto || '—',
      quantidadeItens: itens.length,
      itens,
    };
  });

  return {
    uasg:                     P.uasg?.codigo_uasg || '',
    nomeUnidadeGerenciadora:  P.uasg?.nome_uasg   || '',
    periodoBusca:             derivePeriodo(atas),
    totalARPs:                atas.length,
    atas,
  };
}

function derivePeriodo(atas) {
  const withDates = atas.filter((a) => a.vigenciaInicial !== '—' && a.vigenciaFinal !== '—');
  if (!withDates.length) return '';
  const inis = withDates.map((a) => parseBR(a.vigenciaInicial));
  const fims = withDates.map((a) => parseBR(a.vigenciaFinal));
  const min = new Date(Math.min(...inis));
  const max = new Date(Math.max(...fims));
  const f = (d) => `${String(d.getDate()).padStart(2,'0')}/${String(d.getMonth()+1).padStart(2,'0')}/${d.getFullYear()}`;
  return `${f(min)} até ${f(max)}`;
}

// --- Aggregates ---

function aggregateItem(item) {
  const totalReg   = item.empenhos.reduce((s, e) => s + e.registrada, 0);
  const totalEmp   = item.empenhos.reduce((s, e) => s + e.empenhada,  0);
  const totalSaldo = item.empenhos.reduce((s, e) => s + e.saldo,      0);
  const valorEmp   = totalEmp   * item.valorUnitario;
  const valorSaldo = totalSaldo * item.valorUnitario;
  return { totalReg, totalEmp, totalSaldo, valorEmp, valorSaldo, execPct: pct(totalEmp, totalReg) };
}
function aggregateAta(ata) {
  let totalReg=0, totalEmp=0, totalSaldo=0, valorEmp=0, valorSaldo=0;
  for (const it of ata.itens) {
    const a = aggregateItem(it);
    totalReg += a.totalReg; totalEmp += a.totalEmp; totalSaldo += a.totalSaldo;
    valorEmp += a.valorEmp; valorSaldo += a.valorSaldo;
  }
  return { totalReg, totalEmp, totalSaldo, valorEmp, valorSaldo, execPct: pct(totalEmp, totalReg) };
}
function aggregateAll(atas) {
  let valorTotal=0, valorEmp=0, valorSaldo=0, itensRisco=0;
  for (const a of atas) {
    valorTotal += a.valorTotal;
    const ag = aggregateAta(a);
    valorEmp   += ag.valorEmp;
    valorSaldo += ag.valorSaldo;
    for (const it of a.itens) {
      const ai = aggregateItem(it);
      const vigFim = parseBR(a.vigenciaFinal);
      const diasRestantes = (vigFim - TODAY) / (1000*60*60*24);
      if (ai.execPct < 60 && diasRestantes < 120 && ai.totalSaldo > 0) itensRisco++;
    }
  }
  return { valorTotal, valorEmp, valorSaldo, itensRisco };
}

// --- Components ---

function KpiStrip({ data }) {
  const agg = aggregateAll(data.atas);
  const Card = ({ label, value, sub, accent, icon }) => (
    <div style={{
      flex:1, minWidth:200, padding:'20px 22px',
      background:'#FFF', border:'1px solid #E8E8E8', borderRadius:6,
      borderLeft: accent ? `4px solid ${accent}` : '1px solid #E8E8E8',
      display:'flex', flexDirection:'column', gap:6,
    }}>
      <div style={{display:'flex',alignItems:'center',gap:8}}>
        <i className={"fas "+icon} style={{color:accent || '#1351B4',fontSize:12}}></i>
        <div style={{fontSize:11,fontWeight:600,color:'#333',textTransform:'uppercase',letterSpacing:'0.05em'}}>{label}</div>
      </div>
      <div style={{fontSize:28,fontWeight:600,lineHeight:1.1,letterSpacing:'-0.01em',fontVariantNumeric:'tabular-nums',color:'#1a1a1a'}}>{value}</div>
      {sub && <div style={{fontSize:12,color:'#333'}}>{sub}</div>}
    </div>
  );
  return (
    <div style={{display:'flex',gap:14,flexWrap:'wrap'}}>
      <Card label="ARPs ativas"         value={fmtNum(data.totalARPs)} sub={data.periodoBusca ? ('período '+data.periodoBusca) : 'todas as ARPs da UASG'} icon="fa-folder-open" accent="#1351B4"/>
      <Card label="Valor total das ARPs"  value={fmtBRL(agg.valorTotal)}  sub="somatório de todos os itens" icon="fa-coins" accent="#071D41"/>
      <Card label="Valor empenhado"     value={fmtBRL(agg.valorEmp)}     sub={`${pct(agg.valorEmp, agg.valorTotal)}% executado`} icon="fa-check-circle" accent="#0D47A1"/>
      <Card label="Itens em risco"      value={fmtNum(agg.itensRisco)}   sub="execução baixa · vigência próxima" icon="fa-exclamation-triangle" accent="#B00020"/>
    </div>
  );
}

function ArpList({ atas, selectedIdx, onSelect }) {
  return (
    <aside style={{width:360,flexShrink:0,background:'#FFF',border:'1px solid #E8E8E8',borderRadius:6,overflow:'hidden'}}>
      <div style={{padding:'14px 16px',borderBottom:'1px solid #E8E8E8',background:'#F8F8F8'}}>
        <div style={{fontSize:11,fontWeight:600,color:'#333',textTransform:'uppercase',letterSpacing:'0.05em'}}>Atas de Registro de Preços</div>
        <div style={{fontSize:13,color:'#1a1a1a',marginTop:2}}>{atas.length} ata(s)</div>
      </div>
      <div style={{maxHeight:680,overflowY:'auto'}}>
        {atas.map((ata, i) => {
          const ag = aggregateAta(ata);
          const vigFim = parseBR(ata.vigenciaFinal);
          const diasRest = Math.round((vigFim - TODAY) / (1000*60*60*24));
          const risco = ag.execPct < 60 && diasRest < 180;
          const active = i === selectedIdx;
          return (
            <div key={ata.numero + '-' + i}
                 onClick={() => onSelect(i)}
                 style={{
                   padding:'14px 16px', borderBottom:'1px solid #F0F0F0',
                   cursor:'pointer',
                   background: active ? '#E8F0FE' : 'transparent',
                   borderLeft: active ? '3px solid #1351B4' : '3px solid transparent',
                 }}>
              <div style={{display:'flex',justifyContent:'space-between',alignItems:'baseline',marginBottom:4}}>
                <div style={{fontSize:14,fontWeight:600,color: active ? '#0D47A1' : '#1a1a1a',fontVariantNumeric:'tabular-nums'}}>ARP {ata.numero}</div>
                <span style={{fontSize:10,fontWeight:600,letterSpacing:'0.05em',padding:'2px 8px',borderRadius:9999,
                   background: risco ? '#FDECEA' : '#ECEFF1', color: risco ? '#B00020' : '#37474F'}}>{risco ? 'ATENÇÃO' : 'NO PRAZO'}</span>
              </div>
              <div style={{fontSize:12,color:'#333',marginBottom:8,lineHeight:1.4,overflow:'hidden',display:'-webkit-box',WebkitLineClamp:2,WebkitBoxOrient:'vertical'}}>{ata.objeto}</div>
              <div style={{display:'flex',justifyContent:'space-between',fontSize:11,color:'#333',fontVariantNumeric:'tabular-nums'}}>
                <span>{fmtBRL(ata.valorTotal)}</span>
                <span>{ata.itens.length} itens · {ag.execPct}% exec.</span>
              </div>
              <div style={{height:4,background:'#F0F0F0',borderRadius:2,marginTop:8,overflow:'hidden'}}>
                <div style={{width:ag.execPct+'%',height:'100%',background: risco ? '#B00020' : '#1351B4'}}/>
              </div>
            </div>
          );
        })}
      </div>
    </aside>
  );
}

function VigenciaTimeline({ ata }) {
  const ini = parseBR(ata.vigenciaInicial);
  const fim = parseBR(ata.vigenciaFinal);
  if (isNaN(ini) || isNaN(fim)) return null;
  const total = fim - ini;
  const elapsed = Math.max(0, Math.min(total, TODAY - ini));
  const pctNow = total > 0 ? (elapsed / total) * 100 : 0;
  const future = TODAY < ini;
  const past   = TODAY > fim;
  const todayStr = `${String(TODAY.getDate()).padStart(2,'0')}/${String(TODAY.getMonth()+1).padStart(2,'0')}/${TODAY.getFullYear()}`;
  return (
    <div style={{background:'#FAFAFA',borderRadius:6,padding:'18px 20px'}}>
      <div style={{display:'flex',justifyContent:'space-between',alignItems:'baseline',marginBottom:10}}>
        <div style={{fontSize:11,fontWeight:600,color:'#333',textTransform:'uppercase',letterSpacing:'0.05em'}}>Vigência da ata</div>
        <div style={{fontSize:12,color:'#333',fontVariantNumeric:'tabular-nums'}}>
          {ata.vigenciaInicial} → {ata.vigenciaFinal}
        </div>
      </div>
      <div style={{position:'relative',height:8,background:'#E8E8E8',borderRadius:4,overflow:'visible'}}>
        <div style={{width:pctNow+'%',height:'100%',background:'#1351B4',borderRadius:4}}/>
        {!future && !past && (
          <div style={{position:'absolute',left:`calc(${pctNow}% - 1px)`,top:-6,width:2,height:20,background:'#B00020'}}/>
        )}
      </div>
      <div style={{display:'flex',justifyContent:'space-between',marginTop:6,fontSize:11,color:'#666',fontVariantNumeric:'tabular-nums'}}>
        <span>início</span>
        {!future && !past && <span style={{color:'#B00020',fontWeight:600}}>hoje · {todayStr}</span>}
        <span>término</span>
      </div>
    </div>
  );
}

function UnidadesBreakdown({ item }) {
  const maxReg = Math.max(1, ...item.empenhos.map((e) => e.registrada));
  return (
    <div style={{padding:'18px 20px',background:'#FAFAFA',borderTop:'1px solid #E8E8E8'}}>
      <div style={{display:'grid',gridTemplateColumns:'3fr 1.5fr 1fr 1fr 1fr',gap:12,fontSize:10,fontWeight:600,color:'#333',textTransform:'uppercase',letterSpacing:'0.05em',paddingBottom:10,borderBottom:'1px solid #E8E8E8'}}>
        <div>Unidade</div>
        <div>Execução</div>
        <div style={{textAlign:'right'}}>Registrada</div>
        <div style={{textAlign:'right'}}>Empenhada</div>
        <div style={{textAlign:'right'}}>Saldo</div>
      </div>
      {item.empenhos.length === 0 && (
        <div style={{padding:'12px 0',color:'#666',fontSize:12}}>Sem empenhos registrados.</div>
      )}
      {item.empenhos.map((e, i) => {
        const pp = pct(e.empenhada, e.registrada);
        const risk = pp < 50 && e.saldo > 0;
        const fullBar = (e.registrada / maxReg) * 100;
        const empBar  = (e.empenhada / maxReg) * 100;
        return (
          <div key={i} style={{display:'grid',gridTemplateColumns:'3fr 1.5fr 1fr 1fr 1fr',gap:12,padding:'12px 0',borderBottom:'1px solid #F0F0F0',alignItems:'center'}}>
            <div>
              <div style={{fontSize:13,color:'#1a1a1a',fontWeight:500}}>{e.unidade}</div>
              <div style={{fontSize:10,fontWeight:600,letterSpacing:'0.05em',color: e.tipo==='PARTICIPANTE'?'#0D47A1':'#455A64',textTransform:'uppercase',marginTop:2}}>
                {e.tipo}
              </div>
            </div>
            <div style={{position:'relative',height:18,background:'#E8E8E8',borderRadius:3,overflow:'hidden'}}>
              <div style={{position:'absolute',left:0,top:0,height:'100%',width:fullBar+'%',background:'#CCC'}}/>
              <div style={{position:'absolute',left:0,top:0,height:'100%',width:empBar+'%',background: risk ? '#B00020' : '#1351B4'}}/>
              <div style={{position:'absolute',right:4,top:0,height:'100%',display:'flex',alignItems:'center',fontSize:10,color:'#1a1a1a',fontWeight:600,fontVariantNumeric:'tabular-nums',mixBlendMode:'multiply'}}>
                {pp}%
              </div>
            </div>
            <div style={{textAlign:'right',fontSize:13,fontVariantNumeric:'tabular-nums'}}>{fmtNum(e.registrada)}</div>
            <div style={{textAlign:'right',fontSize:13,fontVariantNumeric:'tabular-nums',fontWeight:500}}>{fmtNum(e.empenhada)}</div>
            <div style={{textAlign:'right',fontSize:13,fontVariantNumeric:'tabular-nums',color: e.saldo>0 ? '#B00020' : '#333',fontWeight: e.saldo>0?600:400}}>{fmtNum(e.saldo)}</div>
          </div>
        );
      })}
    </div>
  );
}

function ItemCard({ item, expanded, onToggle }) {
  const ag = aggregateItem(item);
  const riskExec = ag.execPct < 50;
  return (
    <div style={{border:'1px solid #E8E8E8',borderRadius:6,background:'#FFF',overflow:'hidden'}}>
      <div onClick={onToggle} style={{padding:'16px 20px',cursor:'pointer',display:'grid',gridTemplateColumns:'60px 1fr 160px 140px 28px',gap:16,alignItems:'center'}}>
        <div style={{fontSize:12,fontWeight:700,color:'#1351B4',fontVariantNumeric:'tabular-nums',letterSpacing:'0.03em'}}>#{item.numero}</div>
        <div>
          <div style={{fontSize:14,fontWeight:600,color:'#1a1a1a',marginBottom:4,lineHeight:1.3}}>{item.descricao}</div>
          <div style={{fontSize:11,color:'#333',letterSpacing:'0.02em'}}>
            <strong style={{fontWeight:600}}>{item.fornecedor}</strong> · CNPJ {item.cnpj}
          </div>
        </div>
        <div style={{textAlign:'right'}}>
          <div style={{fontSize:10,fontWeight:600,color:'#333',textTransform:'uppercase',letterSpacing:'0.05em'}}>Valor empenhado</div>
          <div style={{fontSize:18,fontWeight:600,lineHeight:1.1,fontVariantNumeric:'tabular-nums',color:'#1a1a1a'}}>{fmtBRL(ag.valorEmp)}</div>
          <div style={{fontSize:11,color:'#333',fontVariantNumeric:'tabular-nums'}}>de {fmtBRL(item.valorTotal)}</div>
        </div>
        <div>
          <div style={{display:'flex',alignItems:'baseline',gap:4}}>
            <div style={{fontSize:22,fontWeight:600,color: riskExec ? '#B00020' : '#1351B4',fontVariantNumeric:'tabular-nums',lineHeight:1}}>{ag.execPct}%</div>
            <div style={{fontSize:11,color:'#333'}}>executado</div>
          </div>
          <div style={{height:6,background:'#F0F0F0',borderRadius:3,marginTop:6,overflow:'hidden',display:'flex'}}>
            <div style={{width:ag.execPct+'%',background: riskExec ? '#B00020' : '#1351B4'}}/>
          </div>
          <div style={{fontSize:10,color:'#666',marginTop:4,fontVariantNumeric:'tabular-nums'}}>
            {fmtNum(ag.totalEmp)}/{fmtNum(ag.totalReg)} unidades empenhadas
          </div>
        </div>
        <i className={"fas fa-chevron-"+(expanded?'up':'down')} style={{color:'#1351B4',fontSize:14,justifySelf:'end'}}/>
      </div>
      {expanded && <UnidadesBreakdown item={item}/>}
    </div>
  );
}

function Metric({ label, value, sub, big }) {
  return (
    <div style={{padding:'14px 16px',background:'#FAFAFA',borderRadius:6}}>
      <div style={{fontSize:11,fontWeight:600,color:'#333',textTransform:'uppercase',letterSpacing:'0.05em',marginBottom:6}}>{label}</div>
      <div style={{fontSize: big ? 22 : 18,fontWeight:600,lineHeight:1.15,letterSpacing:'-0.01em',fontVariantNumeric:'tabular-nums',color:'#1a1a1a'}}>{value}</div>
      {sub && <div style={{fontSize:11,color:'#333',marginTop:4,lineHeight:1.4}}>{sub}</div>}
    </div>
  );
}

function AtaDetail({ ata }) {
  const [expanded, setExpanded] = React.useState({ 0: true });
  const ag = aggregateAta(ata);

  return (
    <div style={{flex:1,display:'flex',flexDirection:'column',gap:16,minWidth:0}}>
      <div style={{background:'#FFF',border:'1px solid #E8E8E8',borderRadius:6,padding:'22px 24px'}}>
        <div style={{display:'flex',alignItems:'baseline',gap:14,marginBottom:6,flexWrap:'wrap'}}>
          <h2 style={{fontSize:28,fontWeight:500,letterSpacing:'-0.01em',margin:0}}>
            ARP <span style={{fontVariantNumeric:'tabular-nums'}}>{ata.numero}</span>
          </h2>
          <span style={{padding:'4px 12px',borderRadius:9999,background:'#E8F0FE',color:'#0D47A1',fontSize:11,fontWeight:600,letterSpacing:'0.05em'}}>{(ata.modalidade||'').toUpperCase()}</span>
          {ata.orgao && <span style={{padding:'4px 12px',borderRadius:9999,background:'#071D41',color:'#FFF',fontSize:11,fontWeight:600,letterSpacing:'0.05em'}}>{ata.orgao}</span>}
        </div>
        <p style={{fontSize:14,color:'#333',lineHeight:1.5,margin:'0 0 18px 0',maxWidth:900}}>{ata.objeto}</p>

        <div style={{display:'grid',gridTemplateColumns:'repeat(4,1fr)',gap:12,marginBottom:18}}>
          <Metric label="Valor total"     value={fmtBRL(ata.valorTotal)} big/>
          <Metric label="Valor empenhado" value={fmtBRL(ag.valorEmp)}    sub={`${pct(ag.valorEmp, ata.valorTotal)}% de execução financeira`}/>
          <Metric label="Saldo disponível" value={fmtBRL(ag.valorSaldo)}  sub="pode ser empenhado até o fim da vigência"/>
          <Metric label="Itens na ata"    value={fmtNum(ata.itens.length)} sub={`${fmtNum(ag.totalReg)} unidades registradas`}/>
        </div>

        <VigenciaTimeline ata={ata}/>
      </div>

      <div>
        <div style={{display:'flex',alignItems:'baseline',justifyContent:'space-between',marginBottom:12}}>
          <h3 style={{fontSize:18,fontWeight:500,margin:0}}>Itens da ata</h3>
          <div style={{display:'flex',gap:10}}>
            <button className="btn btn-secondary" style={{minHeight:32,padding:'6px 14px'}} disabled><i className="fas fa-filter"></i> FILTRAR</button>
            <button className="btn btn-primary" style={{minHeight:32,padding:'6px 14px'}} disabled><i className="fas fa-download"></i> EXPORTAR CSV</button>
          </div>
        </div>
        <div style={{display:'flex',flexDirection:'column',gap:10}}>
          {ata.itens.length === 0 && (
            <div style={{padding:20,background:'#FFF',border:'1px solid #E8E8E8',borderRadius:6,color:'#666'}}>
              Esta ata não possui itens registrados.
            </div>
          )}
          {ata.itens.map((it, i) => (
            <ItemCard key={it.numero + '-' + i} item={it} expanded={!!expanded[i]}
                      onToggle={() => setExpanded((e) => ({ ...e, [i]: !e[i] }))}/>
          ))}
        </div>
      </div>
    </div>
  );
}

function UasgSwitcher({ options, selectedId }) {
  if (!options || options.length <= 1) {
    const one = options && options[0];
    return one ? (
      <span style={{marginLeft:'auto',opacity:.75}}>UASG {one.codigo_uasg} · {one.nome_uasg}</span>
    ) : null;
  }
  return (
    <select
      className="spav2-uasg-select"
      defaultValue={String(selectedId || '')}
      onChange={(ev) => { window.location.href = `/SPAv2?uasg=${ev.target.value}`; }}
    >
      {options.map((o) => (
        <option key={o.id} value={o.id}>UASG {o.codigo_uasg} · {o.nome_uasg}</option>
      ))}
    </select>
  );
}

function App() {
  const raw = window.SPAV2_PAYLOAD;
  const data = React.useMemo(() => adaptPayload(raw), [raw]);

  const storageKey = `spav2_sel_${data.uasg}`;
  const [sel, setSel] = React.useState(() => {
    const v = parseInt(localStorage.getItem(storageKey) || '0', 10);
    return data.atas.length ? Math.min(Math.max(0, v), data.atas.length - 1) : 0;
  });
  React.useEffect(() => localStorage.setItem(storageKey, String(sel)), [sel, storageKey]);

  return (
    <div data-screen-label="01 Dashboard ARPs">
      <div className="spav2-bar">
        <span style={{letterSpacing:'0.02em',fontWeight:600}}>gov.br</span>
        <span style={{opacity:.75}}>/</span>
        <span style={{letterSpacing:'0.02em'}}>Portal da Transparência</span>
        <UasgSwitcher options={window.SPAV2_UASGS || []} selectedId={window.SPAV2_SELECTED}/>
        <a href="/SPA" style={{color:'#FFF',opacity:.8,textDecoration:'none',marginLeft:12}}>SPA v1</a>
        <a href="/dashboard" style={{color:'#FFF',opacity:.8,textDecoration:'none'}}>Painel</a>
        <a href="/auth/logout" style={{color:'#FFF',opacity:.8,textDecoration:'none'}}>Sair</a>
      </div>

      <div className="spav2-head">
        <div className="spav2-shell" style={{padding:'0 24px'}}>
          <div style={{display:'flex',alignItems:'flex-end',gap:20,marginBottom:18,flexWrap:'wrap'}}>
            <div>
              <div style={{fontSize:11,fontWeight:600,color:'#333',textTransform:'uppercase',letterSpacing:'0.05em',marginBottom:4}}>
                Gestor · {data.nomeUnidadeGerenciadora}
              </div>
              <h1 style={{fontSize:34.832,fontWeight:600,letterSpacing:'-0.02em',lineHeight:'40px',margin:0}}>
                Minhas Atas de Registro de Preços
              </h1>
              <div style={{fontSize:14,color:'#333',marginTop:6}}>
                Acompanhe a execução financeira e quantitativa dos itens registrados nas suas ARPs.
              </div>
            </div>
            <div style={{marginLeft:'auto',display:'flex',gap:10}}>
              <form method="POST" action={`/uasg/${window.SPAV2_SELECTED}/resync`} style={{margin:0}}>
                <input type="hidden" name="csrf_token" value={document.querySelector('meta[name="csrf-token"]').content}/>
                <button type="submit" className="btn btn-secondary"><i className="fas fa-sync"></i> ATUALIZAR</button>
              </form>
              <form method="POST" action={`/uasg/${window.SPAV2_SELECTED}/export/xlsx`} style={{margin:0}}>
                <input type="hidden" name="csrf_token" value={document.querySelector('meta[name="csrf-token"]').content}/>
                <button type="submit" className="btn btn-primary"><i className="fas fa-file-export"></i> RELATÓRIO COMPLETO</button>
              </form>
            </div>
          </div>
          <KpiStrip data={data}/>
        </div>
      </div>

      <div className="spav2-shell" style={{display:'flex',gap:20,alignItems:'flex-start',flexWrap:'wrap'}}>
        {data.atas.length === 0 ? (
          <div style={{flex:1,padding:40,background:'#FFF',border:'1px solid #E8E8E8',borderRadius:6,textAlign:'center',color:'#666'}}>
            Nenhuma ARP encontrada para esta UASG. Execute a sincronização para buscar os dados.
          </div>
        ) : (
          <>
            <ArpList atas={data.atas} selectedIdx={sel} onSelect={setSel}/>
            <AtaDetail ata={data.atas[sel]}/>
          </>
        )}
      </div>
    </div>
  );
}

const rootEl = document.getElementById('spav2-root');
if (rootEl && window.SPAV2_PAYLOAD) {
  ReactDOM.createRoot(rootEl).render(<App/>);
}
