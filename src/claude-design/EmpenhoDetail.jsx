function EmpenhoDetail({ empenho, onBack }) {
  const fmtBRL = window.__EMPENHOS_fmtBRL;
  const c = window.__EMPENHOS_statusColor(empenho.status);

  const Metric = ({ label, value, big }) => (
    <div style={{padding:'18px 20px',background:'#FAFAFA',borderRadius:6,flex:1,minWidth:180}}>
      <div style={{fontSize:11,fontWeight:600,color:'#333',textTransform:'uppercase',letterSpacing:'0.05em',marginBottom:8}}>{label}</div>
      <div style={{fontSize: big ? 28 : 18,fontWeight: big ? 600 : 500,lineHeight:1.2,color:'#1a1a1a',letterSpacing: big ? '-0.01em' : 0,fontVariantNumeric:'tabular-nums'}}>{value}</div>
    </div>
  );
  const Row = ({ label, value }) => (
    <div style={{display:'grid',gridTemplateColumns:'220px 1fr',gap:16,padding:'14px 0',borderBottom:'1px solid #F0F0F0'}}>
      <div style={{fontSize:12,fontWeight:600,color:'#333',textTransform:'uppercase',letterSpacing:'0.05em'}}>{label}</div>
      <div style={{fontSize:15,color:'#1a1a1a'}}>{value}</div>
    </div>
  );

  return (
    <section style={{padding:'32px 24px',maxWidth:1240,margin:'0 auto'}}>
      <button className="btn btn-ghost" onClick={onBack} style={{padding:0,marginBottom:16}}>
        <i className="fas fa-chevron-left"/>VOLTAR PARA RESULTADOS
      </button>

      <div style={{display:'flex',alignItems:'center',gap:16,marginBottom:8}}>
        <h1 style={{fontSize:34.832,fontWeight:600,letterSpacing:'-0.02em',lineHeight:'40px'}}>
          Empenho {empenho.num}
        </h1>
        <span style={{display:'inline-block',padding:'6px 14px',borderRadius:9999,background:c.bg,color:c.fg,fontSize:12,fontWeight:600,letterSpacing:'0.05em'}}>{empenho.status}</span>
      </div>
      <p style={{fontSize:16,color:'#333',marginBottom:24}}>
        Nota de Empenho emitida em <strong style={{color:'#1a1a1a'}}>{empenho.data}</strong> pelo {empenho.orgao}.
      </p>

      <div style={{display:'flex',gap:12,marginBottom:32,flexWrap:'wrap'}}>
        <Metric label="Valor empenhado" value={fmtBRL(empenho.valor)} big/>
        <Metric label="Valor liquidado" value={fmtBRL(empenho.valor * 0.6)}/>
        <Metric label="Valor pago" value={fmtBRL(empenho.valor * 0.4)}/>
      </div>

      <div className="card-elevated" style={{padding:24,boxShadow:'0 6px 6px rgba(0,0,0,.16)',marginBottom:24}}>
        <h2 style={{fontSize:20,fontWeight:500,marginBottom:8}}>Informações do documento</h2>
        <Row label="Órgão superior" value={empenho.orgao}/>
        <Row label="Unidade Gestora" value={`${empenho.ug} · ${empenho.orgao.replace('Ministério da ','').replace('Ministério dos ','')}`}/>
        <Row label="Favorecido" value={empenho.fav}/>
        <Row label="CNPJ do favorecido" value="00.394.544/0001-85"/>
        <Row label="Modalidade de aplicação" value="90 — Aplicações diretas"/>
        <Row label="Fonte de recursos" value="0100 — Recursos ordinários"/>
        <Row label="Elemento de despesa" value="33.90.39 — Outros serviços de terceiros — PJ"/>
      </div>

      <div style={{display:'flex',gap:12}}>
        <button className="btn btn-primary"><i className="fas fa-download"/>BAIXAR NOTA DE EMPENHO (PDF)</button>
        <button className="btn btn-secondary"><i className="fas fa-table"/>DADOS EM CSV</button>
        <button className="btn btn-ghost"><i className="fas fa-external-link-alt"/>ABRIR NO SIAFI</button>
      </div>
    </section>
  );
}
window.EmpenhoDetail = EmpenhoDetail;
