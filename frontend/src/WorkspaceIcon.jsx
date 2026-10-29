const paths = {
 resumen: 'M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h7v7h-7z',
 servicios: 'M4 4h16v16H4z M8 8h8 M8 12h8 M8 16h5',
 organizacion: 'M9 3h6v5H9z M3 16h6v5H3z M15 16h6v5h-6z M12 8v4 M6 16v-4h12v4',
 cmdb: 'M3 4h18v11H3z M8 20h8 M12 15v5 M7 8h.01 M10 8h7 M7 11h.01 M10 11h7',
 desk: 'M4 5h16v14H4z M8 9h8 M8 13h5 M8 17h3',
 faq: 'M8 9a4 4 0 0 1 8 0c0 3-4 2-4 5 M12 18h.01 M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20',
 tablero: 'M4 3v17h17 M8 16v-4 M13 16V8 M18 16V5',
 usuarios: 'M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2 M9 3a4 4 0 1 0 0 8 4 4 0 0 0 0-8 M18 8a3 3 0 0 1 0 6 M22 21v-2a4 4 0 0 0-3-4',
 arrow: 'M5 12h14 M13 6l6 6-6 6',
 logout: 'M9 4H4v16h5 M9 12h12 M16 7l5 5-5 5',
}

export default function WorkspaceIcon({name, ...props}) {
 return <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" {...props}><path d={paths[name] || paths.servicios}/></svg>
}
