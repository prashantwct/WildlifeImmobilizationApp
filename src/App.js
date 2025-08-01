import React, { useState } from 'react';
import DrugRepository from './components/DrugRepository';
import SpeciesDatabase from './components/SpeciesDatabase';
import DarkModeToggle from './components/DarkModeToggle';
import CaseManagement from './components/CaseManagement';
import CaseHistory from './components/CaseHistory';

function App() {
  const [tab, setTab] = useState('repository');
  return (
    <div className={`app-container`}>
      <header>
        <h1>Wildlife Immobilization App</h1>
        <DarkModeToggle />
      </header>
      <nav>
        <button onClick={() => setTab('repository')}>Drug Repository</button>
        <button onClick={() => setTab('species')}>Species DB</button>
        <button onClick={() => setTab('cases')}>Cases</button>
        <button onClick={() => setTab('casehistory')}>Case History</button>
      </nav>
      <main>
        {tab === 'repository' && <DrugRepository />}
        {tab === 'species' && <SpeciesDatabase />}
        {tab === 'cases' && <CaseManagement />}
        {tab === 'casehistory' && <CaseHistory />}
      </main>
    </div>
  );
}

export default App;
