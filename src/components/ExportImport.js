import React from 'react';
import localforage from 'localforage';

function ExportImport() {
  const exportData = async () => {
    const drugs = await localforage.getItem('drugs');
    const species = await localforage.getItem('species');
    const history = await localforage.getItem('history');
    const blob = new Blob([
      JSON.stringify({ drugs, species, history }, null, 2)
    ], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'wildlife_data_backup.json';
    a.click();
    URL.revokeObjectURL(url);
  };

  const importData = e => {
    const file = e.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = async evt => {
      try {
        const data = JSON.parse(evt.target.result);
        if (data.drugs) await localforage.setItem('drugs', data.drugs);
        if (data.species) await localforage.setItem('species', data.species);
        if (data.history) await localforage.setItem('history', data.history);
        alert('Data imported! Please reload the app.');
      } catch (err) {
        alert('Import failed: ' + err.message);
      }
    };
    reader.readAsText(file);
  };

  return (
    <div>
      <h2>Export / Import Data</h2>
      <button onClick={exportData}>Export Backup</button>
      <input type="file" accept="application/json" onChange={importData} />
    </div>
  );
}

export default ExportImport;
