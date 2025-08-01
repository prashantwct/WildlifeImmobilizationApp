import React, { useState, useEffect } from 'react';
import localforage from 'localforage';
import TimerDisplay from './TimerDisplay';
import DrugCalculator from './DrugCalculator';

// Calculator for use inside a case, links results to the case
function CaseCalculator({ onAddCalculation }) {
  const [species, setSpecies] = React.useState([]);
  const [drugs, setDrugs] = React.useState([]);
  const [form, setForm] = React.useState({ species: '', weight: '' });
  const [drugRows, setDrugRows] = React.useState([
    { id: Date.now(), drug: '', dose: '' }
  ]);
  const [results, setResults] = React.useState([]);
  const [lastCalc, setLastCalc] = React.useState(null);

  React.useEffect(() => {
    localforage.getItem('species').then(data => setSpecies(data || []));
    localforage.getItem('drugs').then(data => setDrugs(data || []));
  }, []);

  const handleFormChange = e => setForm({ ...form, [e.target.name]: e.target.value });
  const handleDrugRowChange = (id, e) => {
    setDrugRows(drugRows.map(row =>
      row.id === id ? { ...row, [e.target.name]: e.target.value } : row
    ));
  };
  const addDrugRow = () => {
    setDrugRows([...drugRows, { id: Date.now(), drug: '', dose: '' }]);
  };
  const removeDrugRow = id => {
    setDrugRows(drugRows.length > 1 ? drugRows.filter(row => row.id !== id) : drugRows);
  };

  const calculate = () => {
    const sp = species.find(s => s.id == form.species);
    const weight = parseFloat(form.weight);
    if (!sp || isNaN(weight)) {
      setResults(['Please fill species and weight.']);
      return;
    }
    let resultRows = [];
    let total = 0;
    let perDrug = [];
    for (const row of drugRows) {
      const drug = drugs.find(d => d.id == row.drug);
      const dose = parseFloat(row.dose);
      if (!drug || isNaN(dose)) {
        resultRows.push('Select drug and dose.');
        continue;
      }
      let concentration = parseFloat(drug.concentration);
      if (isNaN(concentration)) {
        const match = /([\d.]+)/.exec(drug.concentration);
        concentration = match ? parseFloat(match[1]) : 1;
      }
      const volume = (weight * dose) / concentration;
      total += volume;
      resultRows.push(`${drug.name}: ${dose} mg/kg | ${volume.toFixed(2)} ml`);
      perDrug.push({ drug: drug.name, dose, volume: volume.toFixed(2) });
    }
    resultRows.push(`Total volume: ${total.toFixed(2)} ml`);
    setResults(resultRows);
    const calcObj = {
      species: sp.name,
      weight,
      drugs: perDrug,
      total: total.toFixed(2),
      time: new Date().toISOString()
    };
    setLastCalc(calcObj);
    if (onAddCalculation) onAddCalculation(calcObj);
  };

  return (
    <div>
      <div>
        <select name="species" value={form.species} onChange={handleFormChange}>
          <option value="">Select Species</option>
          {species.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
        </select>
        <input name="weight" placeholder="Weight (kg)" value={form.weight} onChange={handleFormChange} type="number" />
      </div>
      <div>
        {drugRows.map((row, idx) => (
          <div key={row.id} style={{ margin: '0.5em 0', display: 'flex', gap: 8, alignItems: 'center' }}>
            <select name="drug" value={row.drug} onChange={e => handleDrugRowChange(row.id, e)} style={{ padding: '10px', borderRadius: '4px', border: '1px solid #ddd', flex: '1' }}>
              <option value="">Select Drug</option>
              {drugs.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select>
            <input name="dose" placeholder="Dose (mg/kg)" value={row.dose} onChange={e => handleDrugRowChange(row.id, e)} type="number" style={{ padding: '10px', borderRadius: '4px', border: '1px solid #ddd', flex: '1' }} />
            <button onClick={() => removeDrugRow(row.id)} disabled={drugRows.length === 1} style={{ padding: '10px 15px', backgroundColor: '#f44336', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '1rem', fontWeight: 'bold' }}>Remove</button>
          </div>
        ))}
        <button onClick={addDrugRow} style={{ padding: '10px 15px', backgroundColor: '#4CAF50', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '1rem', fontWeight: 'bold' }}>Add Drug</button>
      </div>
      <button onClick={calculate} style={{ padding: '12px 24px', backgroundColor: '#2196F3', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '1rem', fontWeight: 'bold' }}>Calculate</button>
      {results.length > 0 && (
        <div className="result" style={{ padding: '20px', border: '1px solid #ddd', borderRadius: '8px', boxShadow: '0 2px 5px rgba(0,0,0,0.1)', backgroundColor: '#fff' }}>
          {results.map((r, i) => <div key={i}>{r}</div>)}
        </div>
      )}
    </div>
  );
}


function CaseManagement() {
  const [cases, setCases] = useState([]);
  const emptyMonitoring = { drugAdminTime: '', inductionTime: '', revivalTime: '', intervals: [], calculations: [] };
  const [form, setForm] = useState({ name: '', date: '', monitoring: { ...emptyMonitoring } });
  const [editing, setEditing] = useState(null);
  const [intervalForm, setIntervalForm] = useState({ time: '', respiration: '', temperature: '' });

  useEffect(() => {
    localforage.getItem('cases').then(data => setCases(data || []));
  }, []);

  useEffect(() => {
    localforage.setItem('cases', cases);
  }, [cases]);

  const handleChange = e => {
    const { name, value } = e.target;
    setForm({ ...form, [name]: value });
  };
  const handleMonChange = e => {
    const { name, value } = e.target;
    setForm({ ...form, monitoring: { ...form.monitoring, [name]: value } });
  };
  const handleIntervalChange = e => {
    const { name, value } = e.target;
    setIntervalForm({ ...intervalForm, [name]: value });
  };
  const addInterval = () => {
    if (!intervalForm.time) return;
    setForm({
      ...form,
      monitoring: {
        ...form.monitoring,
        intervals: [...(form.monitoring.intervals || []), { ...intervalForm }]
      }
    });
    setIntervalForm({ time: '', respiration: '', temperature: '' });
  };
  const removeInterval = idx => {
    setForm({
      ...form,
      monitoring: {
        ...form.monitoring,
        intervals: form.monitoring.intervals.filter((_, i) => i !== idx)
      }
    });
  };
  const handleAdd = () => {
    // Ensure monitoring.calculations is always present
    setCases([...cases, { ...form, id: Date.now(), monitoring: { ...emptyMonitoring, ...form.monitoring } }]);
    setForm({ name: '', date: '', monitoring: { ...emptyMonitoring } });
  };
  const handleEdit = c => {
    setEditing(c.id);
    setForm(JSON.parse(JSON.stringify(c)));
  };
  const handleSave = () => {
    setCases(cases.map(c => (c.id === editing ? { ...form, id: editing, monitoring: { ...emptyMonitoring, ...form.monitoring } } : c)));
    setEditing(null);
    setForm({ name: '', date: '', monitoring: { ...emptyMonitoring } });
  };
  const handleDelete = id => setCases(cases.filter(c => c.id !== id));
  return (
    <div>
      <h2 style={{color: '#3f51b5', borderBottom: '2px solid #3f51b5', paddingBottom: '8px', marginBottom: '20px'}}>Case Management</h2>
      <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', marginBottom: 15, backgroundColor: '#e8eaf6', padding: '10px', borderRadius: '4px' }}>
        <TimerDisplay startTime={form.monitoring.drugAdminTime} />
      </div>
      <div style={{ border: '1px solid #bbdefb', padding: 20, borderRadius: 8, marginBottom: 20, boxShadow: '0 2px 5px rgba(0,0,0,0.1)', backgroundColor: '#fff' }}>
        <div style={{marginBottom: 30}}>
          <h4 style={{color: '#1976d2', marginBottom: '15px', borderLeft: '4px solid #1976d2', paddingLeft: '10px'}}>Case Calculator</h4>
          <CaseCalculator onAddCalculation={calc => {
            setForm(f => ({
              ...f,
              monitoring: {
                ...f.monitoring,
                calculations: [...(f.monitoring.calculations||[]), calc]
              }
            }));
          }} />
        </div>
        <div style={{display: 'flex', flexWrap: 'wrap', gap: '15px', marginBottom: '20px'}}>
          <input 
            name="caseNumber" 
            placeholder="Case Number" 
            value={form.caseNumber || ''} 
            onChange={handleChange} 
            style={{padding: '10px', borderRadius: '4px', border: '1px solid #ddd', flex: '1'}} 
          />
          <input 
            name="name" 
            placeholder="Case Name" 
            value={form.name} 
            onChange={handleChange} 
            style={{padding: '10px', borderRadius: '4px', border: '1px solid #ddd', flex: '2'}} 
          />
          <input 
            name="date" 
            type="date" 
            value={form.date} 
            onChange={handleChange} 
            style={{padding: '10px', borderRadius: '4px', border: '1px solid #ddd'}} 
          />
        </div>
        <h4 style={{color: '#1976d2', marginBottom: '15px', borderLeft: '4px solid #1976d2', paddingLeft: '10px'}}>Immobilization Monitoring</h4>
        <div style={{ fontSize: '0.95em', color: '#555', marginBottom: 15, backgroundColor: '#e8eaf6', padding: '10px', borderRadius: '4px' }}>
          <div><b>Drug Administration Time</b>: when immobilization drugs are given</div>
          <div><b>Induction Time</b>: when animal first shows signs of sedation/immobilization</div>
          <div><b>Revival Time</b>: when animal is fully awake after reversal</div>
        </div>
        <div style={{display:'flex', flexWrap:'wrap', gap:12, marginBottom:20}}>
  <button 
    style={{padding: '10px 15px', backgroundColor: '#4CAF50', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', margin: '5px', fontWeight: 'bold'}}
    onClick={() => setForm(f => ({...f, monitoring: { ...f.monitoring, drugAdminTime: new Date().toISOString() }}))}
  >
    Drug Administration
  </button>
  <span style={{fontSize: '1rem', padding: '6px', backgroundColor: '#f0f9f0', borderRadius: '4px', minWidth: '80px', display: 'inline-block', textAlign: 'center'}}>  
    {form.monitoring.drugAdminTime ? new Date(form.monitoring.drugAdminTime).toLocaleTimeString('en-IN', {timeZone: 'Asia/Kolkata'}) : '-'}
  </span>
  <button 
    style={{padding: '10px 15px', backgroundColor: '#2196F3', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', margin: '5px', fontWeight: 'bold'}} 
    onClick={() => setForm(f => ({...f, monitoring: { ...f.monitoring, inductionTime: new Date().toISOString() }}))}
  >
    Induction
  </button>
  <span style={{fontSize: '1rem', padding: '6px', backgroundColor: '#e3f2fd', borderRadius: '4px', minWidth: '80px', display: 'inline-block', textAlign: 'center'}}>  
    {form.monitoring.inductionTime ? new Date(form.monitoring.inductionTime).toLocaleTimeString('en-IN', {timeZone: 'Asia/Kolkata'}) : '-'}
  </span>
  <button 
    style={{padding: '10px 15px', backgroundColor: '#9C27B0', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', margin: '5px', fontWeight: 'bold'}}
    onClick={() => setForm(f => ({...f, monitoring: { ...f.monitoring, headDownTime: new Date().toISOString() }}))}
  >
    Head Down
  </button>
  <span style={{fontSize: '1rem', padding: '6px', backgroundColor: '#f3e5f5', borderRadius: '4px', minWidth: '80px', display: 'inline-block', textAlign: 'center'}}>  
    {form.monitoring.headDownTime ? new Date(form.monitoring.headDownTime).toLocaleTimeString('en-IN', {timeZone: 'Asia/Kolkata'}) : '-'}
  </span>
  <button 
    style={{padding: '10px 15px', backgroundColor: '#FF9800', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', margin: '5px', fontWeight: 'bold'}}
    onClick={() => setForm(f => ({...f, monitoring: { ...f.monitoring, approachTime: new Date().toISOString() }}))}
  >
    Approach
  </button>
  <span style={{fontSize: '1rem', padding: '6px', backgroundColor: '#fff3e0', borderRadius: '4px', minWidth: '80px', display: 'inline-block', textAlign: 'center'}}>  
    {form.monitoring.approachTime ? new Date(form.monitoring.approachTime).toLocaleTimeString('en-IN', {timeZone: 'Asia/Kolkata'}) : '-'}
  </span>
  <button 
    style={{padding: '10px 15px', backgroundColor: '#F44336', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', margin: '5px', fontWeight: 'bold'}}
    onClick={() => setForm(f => ({...f, monitoring: { ...f.monitoring, revivalTime: new Date().toISOString() }}))}
  >
    Revival Time
  </button>
  <span style={{fontSize: '1rem', padding: '6px', backgroundColor: '#ffebee', borderRadius: '4px', minWidth: '80px', display: 'inline-block', textAlign: 'center'}}>  
    {form.monitoring.revivalTime ? new Date(form.monitoring.revivalTime).toLocaleTimeString('en-IN', {timeZone: 'Asia/Kolkata'}) : '-'}
  </span>
  <button 
    style={{padding: '10px 15px', backgroundColor: '#00BCD4', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', margin: '5px', fontWeight: 'bold'}}
    onClick={() => setForm(f => ({...f, monitoring: { ...f.monitoring, headUpTime: new Date().toISOString() }}))}
  >
    Head Up
  </button>
  <span style={{fontSize: '1rem', padding: '6px', backgroundColor: '#e0f7fa', borderRadius: '4px', minWidth: '80px', display: 'inline-block', textAlign: 'center'}}>  
    {form.monitoring.headUpTime ? new Date(form.monitoring.headUpTime).toLocaleTimeString('en-IN', {timeZone: 'Asia/Kolkata'}) : '-'}
  </span>
  <button 
    style={{padding: '10px 15px', backgroundColor: '#795548', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', margin: '5px', fontWeight: 'bold'}}
    onClick={() => setForm(f => ({...f, monitoring: { ...f.monitoring, sternalTime: new Date().toISOString() }}))}
  >
    Sternal
  </button>
  <span style={{fontSize: '1rem', padding: '6px', backgroundColor: '#efebe9', borderRadius: '4px', minWidth: '80px', display: 'inline-block', textAlign: 'center'}}>  
    {form.monitoring.sternalTime ? new Date(form.monitoring.sternalTime).toLocaleTimeString('en-IN', {timeZone: 'Asia/Kolkata'}) : '-'}
  </span>
  <button 
    style={{padding: '10px 15px', backgroundColor: '#607D8B', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', margin: '5px', fontWeight: 'bold'}}
    onClick={() => setForm(f => ({...f, monitoring: { ...f.monitoring, standingTime: new Date().toISOString() }}))}
  >
    Standing
  </button>
  <span style={{fontSize: '1rem', padding: '6px', backgroundColor: '#eceff1', borderRadius: '4px', minWidth: '80px', display: 'inline-block', textAlign: 'center'}}>  
    {form.monitoring.standingTime ? new Date(form.monitoring.standingTime).toLocaleTimeString('en-IN', {timeZone: 'Asia/Kolkata'}) : '-'}
  </span>
</div>
        <div style={{display:'flex', gap:15, marginBottom:20, alignItems: 'center'}}>
          <button 
            style={{padding: '10px 15px', backgroundColor: '#3f51b5', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontWeight: 'bold'}}
            onClick={() => {
              const now = new Date().toISOString();
              const respiration = prompt('Enter respiration value:');
              const temperature = prompt('Enter temperature value:');
              if (respiration || temperature) setForm(f => ({
                ...f,
                monitoring: {
                  ...f.monitoring,
                  intervals: [...(f.monitoring.intervals||[]), { time: now, respiration, temperature }]
                }
              }));
            }}
          >Add Interval</button>
          <ul style={{listStyleType: 'none', padding: 0}}>
            {(form.monitoring.intervals || []).map((iv, i) => (
              <li key={i} style={{margin: '8px 0', padding: '10px', backgroundColor: '#f5f5f5', borderRadius: '4px', display: 'flex', justifyContent: 'space-between', alignItems: 'center'}}>
                <span>
                  <strong>{new Date(iv.time).toLocaleTimeString('en-IN', {timeZone: 'Asia/Kolkata'})}</strong> - 
                  <span style={{color: '#2196F3'}}>Resp: {iv.respiration}</span>, 
                  <span style={{color: '#F44336'}}>Temp: {iv.temperature}°C</span>
                </span>
                <button 
                  style={{padding: '5px 10px', backgroundColor: '#f44336', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer'}}
                  onClick={() => removeInterval(i)}
                >Remove</button>
              </li>
            ))}
          </ul>
        </div>
        <button onClick={() => {
          setEditing(null);
          setForm({ name: '', date: '', monitoring: { ...emptyMonitoring } });
        }}>Cancel</button>
        <div style={{marginTop:24}}>
          <button style={{fontSize:'1.1em', padding:'10px 32px', background:'#388e3c', color:'#fff', border:'none', borderRadius:6, cursor:'pointer'}} onClick={editing ? handleSave : handleAdd}>Save</button>
        </div>
      </div>
      
    </div>
  );
}

export default CaseManagement;
