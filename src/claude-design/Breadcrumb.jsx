function Breadcrumb({ items, onNavigate }) {
  return (
    <nav style={{
      padding: '16px 24px',
      background: 'var(--color-surface-container)',
      fontFamily: 'var(--font-sans)',
      fontSize: 12,
      fontWeight: 600,
      letterSpacing: '0.05em',
      textTransform: 'uppercase',
      color: '#333',
      borderBottom: '1px solid #E8E8E8',
    }}>
      {items.map((it, i) => (
        <span key={i}>
          {i > 0 && <i className="fas fa-chevron-right" style={{fontSize:9,margin:'0 10px',color:'#999'}}/>}
          {it.href && i < items.length - 1 ? (
            <a href="#" onClick={(e) => { e.preventDefault(); onNavigate && onNavigate(it.target); }}
               style={{color:'#1351B4',textDecoration:'none'}}>{it.label}</a>
          ) : (
            <span style={{color:'#1a1a1a'}}>{it.label}</span>
          )}
        </span>
      ))}
    </nav>
  );
}
window.Breadcrumb = Breadcrumb;
