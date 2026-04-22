function PortalHeader({ onHome }) {
  return (
    <header style={{
      background: '#FFF',
      borderBottom: '1px solid #E8E8E8',
      padding: '18px 24px',
      display: 'flex',
      alignItems: 'center',
      gap: 24,
    }}>
      <a href="#" onClick={(e) => { e.preventDefault(); onHome && onHome(); }} style={{textDecoration:'none'}}>
        <img src="../../assets/portal-transparencia-logo.svg" alt="Portal da Transparência" style={{height:48}}/>
      </a>
      <nav style={{display:'flex',gap:24,marginLeft:32,fontFamily:'var(--font-sans)',fontSize:14,fontWeight:500}}>
        {['Receitas','Despesas','Convênios','Servidores','Benefícios'].map(l => (
          <a key={l} href="#" style={{color:'#1a1a1a',textDecoration:'none',paddingBottom:4,borderBottom: l==='Despesas' ? '2px solid #1351B4' : '2px solid transparent'}}>{l}</a>
        ))}
      </nav>
      <div style={{marginLeft:'auto',display:'flex',gap:12,alignItems:'center'}}>
        <button className="btn btn-ghost" style={{padding:'8px'}}><i className="fas fa-search"></i></button>
        <button className="btn btn-secondary">ENTRAR COM GOV.BR</button>
      </div>
    </header>
  );
}
window.PortalHeader = PortalHeader;
