import React, { useState, useEffect } from 'react';
import standardDrugs from '../data/standardDrugs';
import localforage from 'localforage';

const defaultDrugs = [
  { id: 1, name: 'Ketamine', concentration: '100mg/ml', notes: 'Commonly used for large mammals.', speciesDoses: [] },
  { id: 2, name: 'Medetomidine', concentration: '10mg/ml', notes: 'Often combined with other drugs.', speciesDoses: [] }
];

function DrugRepository() {
  const [drugs, setDrugs] = useState([]);
  const [species, setSpecies] = useState([]);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({ name: '', concentration: '', notes: '', speciesDoses: [] });
  const [sdForm, setSdForm] = useState({ speciesId: '', dose: '' });
  const [editingSd, setEditingSd] = useState(null);

  useEffect(() => {
    localforage.getItem('drugs').then(data => {
      if (data) setDrugs(data);
      else setDrugs(defaultDrugs);
    });
    localforage.getItem('species').then(data => setSpecies(data || []));
  }, []);

  useEffect(() => {
    localforage.setItem('drugs', drugs);
  }, [drugs]);

  const handleChange = e => setForm({ ...form, [e.target.name]: e.target.value });

  const handleAdd = () => {
    setDrugs([...drugs, { ...form, id: Date.now() }]);
    setForm({ name: '', concentration: '', notes: '', speciesDoses: [] });
  };

  const handleEdit = drug => {
    setEditing(drug.id);
    setForm({ ...drug, speciesDoses: drug.speciesDoses || [] });
  };

  const handleSave = () => {
    setDrugs(drugs.map(d => (d.id === editing ? { ...form, id: editing } : d)));
    setEditing(null);
    setForm({ name: '', concentration: '', notes: '', speciesDoses: [] });
  };

  const handleDelete = id => setDrugs(drugs.filter(d => d.id !== id));

  // Species-dose management
  const handleSdChange = e => setSdForm({ ...sdForm, [e.target.name]: e.target.value });
  const handleSdAdd = () => {
    if (!sdForm.speciesId || !sdForm.dose) return;
    setForm({ ...form, speciesDoses: [...(form.speciesDoses || []), { ...sdForm, id: Date.now() }] });
    setSdForm({ speciesId: '', dose: '' });
  };
  const handleSdEdit = sd => {
    setEditingSd(sd.id);
    setSdForm({ speciesId: sd.speciesId, dose: sd.dose });
  };
  const handleSdSave = () => {
    setForm({
      ...form,
      speciesDoses: form.speciesDoses.map(sd => sd.id === editingSd ? { ...sdForm, id: editingSd } : sd)
    });
    setEditingSd(null);
    setSdForm({ speciesId: '', dose: '' });
  };
  const handleSdDelete = id => setForm({ ...form, speciesDoses: form.speciesDoses.filter(sd => sd.id !== id) });

  return (
    <div>
      <h2>Drug Repository</h2>
      <div>
        <input name="name" placeholder="Name" value={form.name} onChange={handleChange} />
        <input name="concentration" placeholder="Concentration" value={form.concentration} onChange={handleChange} />
        <input name="notes" placeholder="Notes" value={form.notes} onChange={handleChange} />
        {editing ? (
          <button onClick={handleSave}>Save</button>
        ) : (
          <button onClick={handleAdd}>Add</button>
        )}
        {editing && <button onClick={() => setEditing(null)}>Cancel</button>}
      </div>
      {editing && (
        <div style={{ margin: '1em 0', padding: '1em', border: '1px solid #ccc', borderRadius: 6 }}>
          <h4>Species & Doses</h4>
          <div>
            <select name="speciesId" value={sdForm.speciesId} onChange={handleSdChange}>
              <option value="">Select Species</option>
              {species.map(s => <option key={s.id} value={s.id}>{s.name}</option>)}
            </select>
            <input name="dose" placeholder="Dose (mg/kg)" value={sdForm.dose} onChange={handleSdChange} type="number" />
            {editingSd ? (
              <button onClick={handleSdSave}>Save</button>
            ) : (
              <button onClick={handleSdAdd}>Add</button>
            )}
            {editingSd && <button onClick={() => setEditingSd(null)}>Cancel</button>}
          </div>
          <ul>
            {(form.speciesDoses || []).map(sd => (
              <li key={sd.id}>
                {species.find(s => s.id == sd.speciesId)?.name || 'Unknown'}: {sd.dose} mg/kg
                <button onClick={() => handleSdEdit(sd)}>Edit</button>
                <button onClick={() => handleSdDelete(sd.id)}>Delete</button>
              </li>
            ))}
          </ul>
        </div>
      )}
      <ul>
        {drugs.map(drug => (
          <li key={drug.id}>
            <b>{drug.name}</b> ({drug.concentration}) - {drug.notes}
            <button onClick={() => handleEdit(drug)}>Edit</button>
            <button onClick={() => handleDelete(drug.id)}>Delete</button>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default DrugRepository;
