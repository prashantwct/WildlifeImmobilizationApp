import React, { useEffect, useState } from 'react';

function DarkModeToggle() {
  const [dark, setDark] = useState(() =>
    window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches
  );

  useEffect(() => {
    document.body.classList.toggle('dark', dark);
  }, [dark]);

  return (
    <button onClick={() => setDark(d => !d)}>
      {dark ? '☾ Dark' : '☀ Light'}
    </button>
  );
}

export default DarkModeToggle;
