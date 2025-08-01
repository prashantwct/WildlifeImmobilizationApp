import React, { useState, useEffect } from 'react';
import localforage from 'localforage';

function CaseHistory() {
  const [cases, setCases] = useState([]);
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    localforage.getItem('cases').then(data => setCases(data || []));
  }, []);

  return (
    <div>
      <h2>Case History</h2>
      <ul>
        {cases.map(c => (
          <li key={c.id} style={{ marginBottom: 10, display: 'flex', alignItems: 'center', gap: 8 }}>
            <button onClick={() => setSelected(c)} style={{ fontWeight: selected && selected.id === c.id ? 'bold' : 'normal' }}>
              {c.name} ({c.date})
            </button>
            <button onClick={async e => {
              e.stopPropagation();
              const jsPDF = (await import('jspdf')).jsPDF;
              const doc = new jsPDF();
              let y = 10;
              doc.setFontSize(16);
              doc.text(`Case: ${c.name || ''}`, 10, y); y += 8;
              doc.setFontSize(12);
              doc.text(`Case Number: ${c.caseNumber || ''}`, 10, y); y += 7;
              doc.text(`Date: ${c.date || ''}`, 10, y); y += 7;
              doc.text('--- Monitoring ---', 10, y); y += 7;
              doc.text(`Approach: ${c.monitoring.approachTime || '-'}`, 10, y); y += 6;
              doc.text(`Drug Admin: ${c.monitoring.drugAdminTime || '-'}`, 10, y); y += 6;
              doc.text(`Induction: ${c.monitoring.inductionTime || '-'}`, 10, y); y += 6;
              doc.text(`Revival: ${c.monitoring.revivalTime || '-'}`, 10, y); y += 7;
              if ((c.monitoring.intervals||[]).length > 0) {
                doc.text('Respiration & Temperature Events:', 10, y); y += 6;
                c.monitoring.intervals.forEach((iv, i) => {
                  doc.text(`${iv.time}: Resp: ${iv.respiration}, Temp: ${iv.temperature}`, 12, y); y += 6;
                  if (y > 270) { doc.addPage(); y = 10; }
                });
                y += 2;
              }
              if ((c.monitoring.calculations||[]).length > 0) {
                doc.text('Calculations:', 10, y); y += 6;
                c.monitoring.calculations.forEach((calc, i) => {
                  doc.text(`${calc.time ? new Date(calc.time).toLocaleString() : ''}: ${calc.species}, ${calc.weight}kg`, 12, y); y += 6;
                  calc.drugs.forEach(d => {
                    doc.text(`- ${d.drug} (${d.dose} mg/kg, ${d.volume} ml)`, 14, y); y += 6;
                  });
                  doc.text(`Total: ${calc.total} ml`, 14, y); y += 6;
                  if (y > 270) { doc.addPage(); y = 10; }
                });
              }
              doc.save(`case_${c.caseNumber||c.id}.pdf`);
            }}>Export as PDF</button>
          </li>
        ))}
      </ul>
      {selected && (
        <div style={{ border: '1px solid #ccc', padding: 16, borderRadius: 8, marginTop: 16 }}>
          <h3>{selected.name}</h3>
          <div>Date: {selected.date}</div>
          <div><b>Monitoring</b></div>
          <div>Drug Admin: {selected.monitoring.drugAdminTime || '-'}</div>
          <div>Induction: {selected.monitoring.inductionTime || '-'}</div>
          <div>Revival: {selected.monitoring.revivalTime || '-'}</div>
          <div style={{marginTop:8}}>
            <b>5-min Intervals</b>
            <ul>
              {(selected.monitoring.intervals || []).map((iv, i) => (
                <li key={i}>{iv.time} - Resp: {iv.respiration}, Temp: {iv.temperature}</li>
              ))}
            </ul>
          </div>
          {selected.monitoring.calculations && selected.monitoring.calculations.length > 0 && (
            <div style={{marginTop:8}}>
              <b>Calculations</b>
              <ul>
                {selected.monitoring.calculations.map((calc, i) => (
                  <li key={i}>
                    {calc.time ? new Date(calc.time).toLocaleString() : ''}: {calc.species}, {calc.weight}kg, {calc.drugs.map(d => `${d.drug} (${d.dose} mg/kg, ${d.volume} ml)`).join('; ')}. <b>Total:</b> {calc.total} ml
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default CaseHistory;
