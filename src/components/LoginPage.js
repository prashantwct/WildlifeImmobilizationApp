import React, { useEffect } from 'react';

const GOOGLE_CLIENT_ID = 'YOUR_GOOGLE_CLIENT_ID.apps.googleusercontent.com'; // <-- Replace with your actual client ID

function LoginPage({ onLogin }) {
  useEffect(() => {
    if (!window.google) {
      const script = document.createElement('script');
      script.src = 'https://accounts.google.com/gsi/client';
      script.async = true;
      script.defer = true;
      script.onload = initializeGoogle;
      document.body.appendChild(script);
    } else {
      initializeGoogle();
    }
    function initializeGoogle() {
      if (window.google && window.google.accounts && window.google.accounts.id) {
        window.google.accounts.id.initialize({
          client_id: GOOGLE_CLIENT_ID,
          callback: handleCredentialResponse
        });
        window.google.accounts.id.renderButton(
          document.getElementById('google-signin-btn'),
          { theme: 'outline', size: 'large', width: 280 }
        );
      }
    }
    function handleCredentialResponse(response) {
      // Save token in localStorage for persistence
      localStorage.setItem('google_token', response.credential);
      onLogin(response.credential);
    }
  }, [onLogin]);

  return (
    <div style={{display:'flex', flexDirection:'column', alignItems:'center', justifyContent:'center', height:'100vh'}}>
      <h2>Login to Wildlife Immobilization App</h2>
      <div id="google-signin-btn" style={{marginTop:32}}></div>
    </div>
  );
}

export default LoginPage;
