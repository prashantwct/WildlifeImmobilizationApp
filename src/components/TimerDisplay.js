import React, { useEffect, useState } from 'react';

function TimerDisplay({ startTime }) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    let timer;
    if (startTime) {
      timer = setInterval(() => {
        setElapsed(Math.floor((Date.now() - new Date(startTime).getTime()) / 1000));
      }, 1000);
    } else {
      setElapsed(0);
    }
    return () => clearInterval(timer);
  }, [startTime]);

  if (!startTime) return <span style={{fontWeight:'bold', color:'#388e3c'}}>Timer: --:--</span>;
  const mins = String(Math.floor(elapsed / 60)).padStart(2, '0');
  const secs = String(elapsed % 60).padStart(2, '0');
  return <span style={{fontWeight:'bold', color:'#388e3c'}}>Timer: {mins}:{secs}</span>;
}

export default TimerDisplay;
