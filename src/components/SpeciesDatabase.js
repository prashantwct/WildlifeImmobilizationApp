import React, { useState, useEffect } from 'react';
import standardSpecies from '../data/standardSpecies';
import localforage from 'localforage';

const defaultSpecies = [
  { id: 1, name: 'African Elephant', notes: 'Loxodonta africana' },
  { id: 2, name: 'Lion', notes: 'Panthera leo' }
];

function SpeciesDatabase() {
  const [species, setSpecies] = useState([]);
  const [editing, setEditing] = useState(null);
  const [form, setForm] = useState({ name: '', notes: '' });

  useEffect(() => {
    localforage.getItem('species').then(data => {
      if (data) setSpecies(data);
      else setSpecies(defaultSpecies);
    });
  }, []);

  useEffect(() => {
    localforage.setItem('species', species);
  }, [species]);

  const handleChange = e => setForm({ ...form, [e.target.name]: e.target.value });

  const handleAdd = () => {
    setSpecies([...species, { ...form, id: Date.now() }]);
    setForm({ name: '', notes: '' });
  };

  const handleEdit = s => {
    setEditing(s.id);
    setForm(s);
  };

  const handleSave = () => {
    setSpecies(species.map(s => (s.id === editing ? { ...form, id: editing } : s)));
    setEditing(null);
    setForm({ name: '', notes: '' });
  };

  const handleDelete = id => setSpecies(species.filter(s => s.id !== id));

  return (
    <div>
      <h2>Species Database</h2>
      <div>
        <input name="name" placeholder="Name" value={form.name} onChange={handleChange} />
        <input name="notes" placeholder="Notes" value={form.notes} onChange={handleChange} />
        {editing ? (
          <button onClick={handleSave}>Save</button>
        ) : (
          <button onClick={handleAdd}>Add</button>
        )}
        {editing && <button onClick={() => setEditing(null)}>Cancel</button>}
      </div>
      <ul>
        {species.map(s => (
          <li key={s.id}>
            <b>{s.name}</b> - {s.notes}
            <button onClick={() => handleEdit(s)}>Edit</button>
            <button onClick={() => handleDelete(s.id)}>Delete</button>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default SpeciesDatabase;
