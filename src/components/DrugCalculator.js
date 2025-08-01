import React, { useState, useEffect } from 'react';
import localforage from 'localforage';

function DrugCalculator() {
  const [species, setSpecies] = useState([]);
  const [drugs, setDrugs] = useState([]);
  const [form, setForm] = useState({ species: '', weight: '' });
  const [drugRows, setDrugRows] = useState([
    { id: Date.now(), drug: '', dose: '' }
  ]);
  const [results, setResults] = useState([]);

  useEffect(() => {
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
    for (const row of drugRows) {
      const drug = drugs.find(d => d.id == row.drug);
      const dose = parseFloat(row.dose);
      if (!drug || isNaN(dose)) {
        resultRows.push('Select drug and dose.');
        continue;
      }
      let concentration = parseFloat(drug.concentration);
      if (isNaN(concentration)) {
        // try to extract number from string
        const match = /([\d.]+)/.exec(drug.concentration);
        concentration = match ? parseFloat(match[1]) : 1;
      }
      const volume = (weight * dose) / concentration;
      total += volume;
      resultRows.push(`${drug.name}: ${dose} mg/kg | ${volume.toFixed(2)} ml`);
    }
    resultRows.push(`Total volume: ${total.toFixed(2)} ml`);
    setResults(resultRows);
    // Save to history
    localforage.getItem('history').then(hist => {
      const entry = {
        species: sp.name,
        weight: weight,
        drugs: drugRows.map(row => {
          const drug = drugs.find(d => d.id == row.drug);
          return { name: drug?.name || '', dose: row.dose };
        }),
        result: total,
        time: new Date()
      };
      const newHist = hist ? [...hist, entry] : [entry];
      localforage.setItem('history', newHist);
    });
  };

  return (
    <div>
      <h2>Drug Volume Calculator</h2>
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
            <select name="drug" value={row.drug} onChange={e => handleDrugRowChange(row.id, e)}>
              <option value="">Select Drug</option>
              {drugs.map(d => <option key={d.id} value={d.id}>{d.name}</option>)}
            </select>
            <input name="dose" placeholder="Dose (mg/kg)" value={row.dose} onChange={e => handleDrugRowChange(row.id, e)} type="number" />
            <button onClick={() => removeDrugRow(row.id)} disabled={drugRows.length === 1}>Remove</button>
          </div>
        ))}
        <button onClick={addDrugRow}>Add Drug</button>
      </div>
      <button onClick={calculate}>Calculate</button>
      {results.length > 0 && (
        <div className="result">
          {results.map((r, i) => <div key={i}>{r}</div>)}
        </div>
      )}
    </div>
  );
}

export default DrugCalculator;
