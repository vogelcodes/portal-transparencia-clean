const EMPENHOS = [
  { num:'2024NE800123', data:'15/03/2024', orgao:'Ministério da Saúde',              ug:'250005', fav:'Fundação Oswaldo Cruz',           valor:1245678.90, status:'EMITIDO' },
  { num:'2024NE800198', data:'22/03/2024', orgao:'Ministério da Educação',           ug:'153056', fav:'Universidade Federal de Minas Gerais', valor: 892340.00, status:'LIQUIDADO' },
  { num:'2024NE800241', data:'04/04/2024', orgao:'Ministério da Ciência e Tecnologia', ug:'240101', fav:'CNPq — Conselho Nacional',       valor:3412099.55, status:'EMITIDO' },
  { num:'2024NE800257', data:'11/04/2024', orgao:'Ministério da Saúde',              ug:'250005', fav:'Laboratório Farmanguinhos',       valor: 156000.00, status:'CANCELADO' },
  { num:'2024NE800289', data:'18/04/2024', orgao:'Ministério da Defesa',             ug:'160089', fav:'Indústria Aeronáutica SA',        valor:9872140.12, status:'EMITIDO' },
  { num:'2024NE800312', data:'02/05/2024', orgao:'Ministério dos Transportes',       ug:'390003', fav:'Construtora Norte-Sul LTDA',      valor:4210880.00, status:'LIQUIDADO' },
];
const fmtBRL = (n) => 'R$ ' + n.toLocaleString('pt-BR', { minimumFractionDigits:2, maximumFractionDigits:2 });
const statusColor = (s) => ({
  EMITIDO:    { bg:'#E8F0FE', fg:'#0D47A1' },
  LIQUIDADO:  { bg:'#ECEFF1', fg:'#37474F' },
  CANCELADO:  { bg:'#FDECEA', fg:'#B00020' },
})[s] || { bg:'#F0F0F0', fg:'#333' };

function ResultList({ onOpen }) {
  return (
    <section style={{padding:'32px 24px',maxWidth:1240,margin:'0 auto'}}>
      <div style={{display:'flex',alignItems:'baseline',marginBottom:16,gap:16}}>
        <h2 style={{fontSize:24,fontWeight:500}}>Resultados da consulta</h2>
        <span style={{fontSize:13,color:'#333'}}>{EMPENHOS.length} registros encontrados</span>
        <div style={{marginLeft:'auto',display:'flex',gap:10}}>
          <button className="btn btn-secondary"><i className="fas fa-download"></i>BAIXAR CSV</button>
          <button className="btn btn-ghost"><i className="fas fa-chart-bar"></i>VISUALIZAR GRÁFICOS</button>
        </div>
      </div>

      <div style={{background:'#FFF',border:'1px solid #E8E8E8',borderRadius:6,overflow:'hidden'}}>
        <table style={{width:'100%',borderCollapse:'collapse',fontFamily:'var(--font-sans)',fontSize:14}}>
          <thead>
            <tr style={{background:'#F8F8F8',borderBottom:'1px solid #CCC'}}>
              {['Documento','Data','Órgão superior','Favorecido','Valor','Status',''].map((h,i) => (
                <th key={i} style={{textAlign: i===4 ? 'right' : 'left',padding:'14px 16px',fontSize:11,fontWeight:600,textTransform:'uppercase',letterSpacing:'0.05em',color:'#333'}}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {EMPENHOS.map((e, i) => {
              const c = statusColor(e.status);
              return (
                <tr key={e.num} style={{borderBottom:'1px solid #F0F0F0',cursor:'pointer'}}
                    onClick={() => onOpen(e)}
                    onMouseEnter={ev => ev.currentTarget.style.background = '#FAFAFA'}
                    onMouseLeave={ev => ev.currentTarget.style.background = ''}>
                  <td style={{padding:'14px 16px',color:'#1351B4',fontWeight:500,fontVariantNumeric:'tabular-nums'}}>{e.num}</td>
                  <td style={{padding:'14px 16px',fontVariantNumeric:'tabular-nums'}}>{e.data}</td>
                  <td style={{padding:'14px 16px'}}>{e.orgao}</td>
                  <td style={{padding:'14px 16px',color:'#333'}}>{e.fav}</td>
                  <td style={{padding:'14px 16px',textAlign:'right',fontVariantNumeric:'tabular-nums',fontWeight:500}}>{fmtBRL(e.valor)}</td>
                  <td style={{padding:'14px 16px'}}>
                    <span style={{display:'inline-block',padding:'4px 12px',borderRadius:9999,background:c.bg,color:c.fg,fontSize:11,fontWeight:600,letterSpacing:'0.05em'}}>{e.status}</span>
                  </td>
                  <td style={{padding:'14px 16px',color:'#1351B4'}}><i className="fas fa-chevron-right"/></td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div style={{display:'flex',justifyContent:'center',alignItems:'center',gap:8,marginTop:20,fontFamily:'var(--font-sans)',fontSize:14}}>
        <button className="btn btn-ghost" style={{padding:'6px 10px'}}><i className="fas fa-chevron-left"/></button>
        {[1,2,3,4,5].map(n => (
          <button key={n} className="btn" style={{
            padding:'6px 12px',minHeight:32,
            background: n===1 ? '#1351B4' : 'transparent',
            color:    n===1 ? '#FFF'    : '#1351B4',
            border: 'none',
          }}>{n}</button>
        ))}
        <span>…</span>
        <button className="btn btn-ghost" style={{padding:'6px 10px'}}><i className="fas fa-chevron-right"/></button>
      </div>
    </section>
  );
}
window.ResultList = ResultList;
window.__EMPENHOS_fmtBRL = fmtBRL;
window.__EMPENHOS_statusColor = statusColor;
