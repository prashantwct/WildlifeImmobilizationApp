import React, { useState, useEffect } from 'react';
import localforage from 'localforage';

function HistoryLog() {
  const [history, setHistory] = useState([]);
  const [search, setSearch] = useState('');

  useEffect(() => {
    localforage.getItem('history').then(data => setHistory(data || []));
  }, []);

  const filtered = history.filter(h =>
    h.species?.toLowerCase().includes(search.toLowerCase()) ||
    h.drug?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div>
      <h2>Calculation History</h2>
      <input
        placeholder="Search by species or drug"
        value={search}
        onChange={e => setSearch(e.target.value)}
      />
      <ul>
        {filtered.length === 0 && <li>No history found.</li>}
        {filtered.map((h, i) => (
          <li key={i}>
            <b>{h.species}</b>, {h.weight}kg, <b>{h.drug}</b> @ {h.dose}mg/kg → {h.result}ml
            <span style={{ float: 'right', fontSize: '0.8em', color: '#888' }}>
              {new Date(h.time).toLocaleString()}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
}

export default HistoryLog;
