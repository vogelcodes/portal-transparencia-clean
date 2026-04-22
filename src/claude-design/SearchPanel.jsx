function SearchPanel({ onSearch }) {
  const [ano, setAno] = React.useState('2024');
  const [orgao, setOrgao] = React.useState('');
  const [numero, setNumero] = React.useState('');

  const Field = ({ label, children }) => (
    <div style={{display:'flex',flexDirection:'column',gap:6}}>
      <label style={{fontSize:12,fontWeight:600,color:'#333',textTransform:'uppercase',letterSpacing:'0.05em'}}>{label}</label>
      {children}
    </div>
  );

  return (
    <section style={{padding:'32px 24px',maxWidth:1240,margin:'0 auto'}}>
      <h1 style={{fontSize:28,fontWeight:500,letterSpacing:'-0.01em',marginBottom:8}}>Empenhos</h1>
      <p style={{fontSize:16,lineHeight:'24px',color:'#333',marginBottom:24,maxWidth:780}}>
        Consulte os empenhos emitidos pelo Governo Federal para o detalhamento da despesa.
        Para refinar os resultados, preencha ao menos um dos campos abaixo.
      </p>

      <div className="card-elevated" style={{padding:24,boxShadow:'0 6px 6px rgba(0,0,0,.16)'}}>
        <div style={{display:'grid',gridTemplateColumns:'1fr 2fr 1fr',gap:20,marginBottom:20}}>
          <Field label="Ano do empenho">
            <select className="input-field" value={ano} onChange={e=>setAno(e.target.value)}>
              <option>2024</option><option>2023</option><option>2022</option>
            </select>
          </Field>
          <Field label="Órgão superior">
            <input className="input-field" value={orgao} onChange={e=>setOrgao(e.target.value)}
              placeholder="Ex: Ministério da Saúde"/>
          </Field>
          <Field label="Número do documento">
            <input className="input-field" value={numero} onChange={e=>setNumero(e.target.value)}
              placeholder="2024NE800123"/>
          </Field>
        </div>
        <div style={{display:'flex',flexWrap:'wrap',gap:10,marginBottom:20}}>
          {['Nota de Empenho','Reforço','Anulação','Cancelamento'].map((t,i) => (
            <label key={t} style={{display:'inline-flex',alignItems:'center',gap:8,fontSize:14,cursor:'pointer'}}>
              <input type="checkbox" defaultChecked={i<2}
                style={{accentColor:'#1351B4',width:16,height:16}}/>
              {t}
            </label>
          ))}
        </div>
        <div style={{display:'flex',gap:12,justifyContent:'flex-end',borderTop:'1px solid #F0F0F0',paddingTop:20}}>
          <button className="btn btn-ghost">LIMPAR</button>
          <button className="btn btn-secondary"><i className="fas fa-filter"></i>MAIS FILTROS</button>
          <button className="btn btn-primary" onClick={() => onSearch({ ano, orgao, numero })}>
            <i className="fas fa-search"></i>CONSULTAR
          </button>
        </div>
      </div>
    </section>
  );
}
window.SearchPanel = SearchPanel;
