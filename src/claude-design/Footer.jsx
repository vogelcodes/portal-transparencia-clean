function Footer() {
  return (
    <footer style={{background:'#071D41',color:'#FFF',padding:'40px 24px',marginTop:48}}>
      <div style={{maxWidth:1240,margin:'0 auto',display:'grid',gridTemplateColumns:'1fr 1fr 1fr',gap:32}}>
        <div>
          <img src="../../assets/govbr-logo-negative.svg" alt="gov.br" style={{height:28,marginBottom:16}}/>
          <p style={{fontSize:13,lineHeight:1.6,color:'#90CAF9'}}>
            O Portal da Transparência é uma iniciativa da Controladoria-Geral da União (CGU)
            que permite ao cidadão acompanhar a execução financeira do Governo Federal.
          </p>
        </div>
        <div>
          <div style={{fontSize:11,fontWeight:600,textTransform:'uppercase',letterSpacing:'0.05em',marginBottom:12,color:'#90CAF9'}}>Consultas</div>
          {['Despesas','Receitas','Convênios','Servidores','Benefícios sociais'].map(l => (
            <a key={l} href="#" style={{display:'block',color:'#FFF',textDecoration:'none',fontSize:14,padding:'4px 0',opacity:.9}}>{l}</a>
          ))}
        </div>
        <div>
          <div style={{fontSize:11,fontWeight:600,textTransform:'uppercase',letterSpacing:'0.05em',marginBottom:12,color:'#90CAF9'}}>Informações</div>
          {['Sobre o Portal','Glossário','Perguntas frequentes','Dados abertos','Fale conosco'].map(l => (
            <a key={l} href="#" style={{display:'block',color:'#FFF',textDecoration:'none',fontSize:14,padding:'4px 0',opacity:.9}}>{l}</a>
          ))}
        </div>
      </div>
      <div style={{maxWidth:1240,margin:'32px auto 0',paddingTop:20,borderTop:'1px solid rgba(255,255,255,.1)',fontSize:12,color:'#90CAF9',display:'flex',justifyContent:'space-between'}}>
        <span>© Controladoria-Geral da União · Governo Federal do Brasil</span>
        <span>Atualizado em 22/04/2026</span>
      </div>
    </footer>
  );
}
window.Footer = Footer;
