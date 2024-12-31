import { useState } from 'react';
import Chat from './Chat';
import HLSPlayer from './HLSPlayer';

const App = () => {
  const [username, setUsername] = useState("");
  return (
    <div>      
      <div>
        <label>
          Nombre de usuario: <input value={username} onChange={(e) => setUsername(e.target.value)}></input>
        </label>
      </div>
      <div style={{display: "flex"}}>             
        <div style={{width: "50%"}}>
          <h1>Video</h1>
          <HLSPlayer src="http://localhost:3000/hls/stream1/stream1.m3u8" />
        </div>
        <div style={{width: "50%"}}>
          <Chat username={username}/>
        </div>
      </div>
    </div>
  );
};

export default App;
