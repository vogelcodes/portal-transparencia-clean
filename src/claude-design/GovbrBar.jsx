function GovbrBar() {
  return (
    <div style={{
      background: 'var(--color-tertiary)',
      color: '#FFF',
      padding: '0 24px',
      height: 40,
      display: 'flex',
      alignItems: 'center',
      gap: 24,
      fontFamily: 'var(--font-sans)',
      fontSize: 13,
    }}>
      <a href="#" style={{display:'flex',alignItems:'center',gap:8,color:'#FFF',textDecoration:'none'}}>
        <img src="../../assets/govbr-logo-negative.svg" alt="gov.br" style={{height:20}}/>
      </a>
      <nav style={{display:'flex',gap:16,marginLeft:'auto',fontSize:12}}>
        <a href="#" style={{color:'#FFF',textDecoration:'none',opacity:.9}}>COMUNICA</a>
        <a href="#" style={{color:'#FFF',textDecoration:'none',opacity:.9}}>PARTICIPE</a>
        <a href="#" style={{color:'#FFF',textDecoration:'none',opacity:.9}}>ACESSO À INFORMAÇÃO</a>
        <a href="#" style={{color:'#FFF',textDecoration:'none',opacity:.9}}>LEGISLAÇÃO</a>
        <a href="#" style={{color:'#FFF',textDecoration:'none',opacity:.9}}>ÓRGÃOS DO GOVERNO</a>
      </nav>
    </div>
  );
}
window.GovbrBar = GovbrBar;
