import { useEffect, useState } from 'react';

function App() {
  const [message, setMessage] = useState('로딩 중...');

  useEffect(() => {
    fetch('http://127.0.0.1:8000/')
      .then((response) => response.json())
      .then((data) => {
        setMessage(data.message);
      })
      .catch((error) => {
        console.error(error);
        setMessage('API 연결 실패');
      });
  }, []);

  return (
    <div>
      <h1>Family Hackathon</h1>
      <p>Backend Response: {message}</p>
    </div>
  );
}

export default App;
