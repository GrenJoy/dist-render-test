import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import axios from 'axios';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;
const WS_URL = BACKEND_URL.replace('https://', 'wss://').replace('http://', 'ws://');

function App() {
  const [roomId, setRoomId] = useState('');
  const [currentRoom, setCurrentRoom] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [remoteAudioLevel, setRemoteAudioLevel] = useState(0);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [activeUsers, setActiveUsers] = useState(0);
  const [volume, setVolume] = useState(80);

  // WebRTC and WebSocket refs
  const localStreamRef = useRef(null);
  const remoteStreamRef = useRef(null);
  const peerConnectionRef = useRef(null);
  const websocketRef = useRef(null);
  const localAudioRef = useRef(null);
  const remoteAudioRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const remoteAnalyserRef = useRef(null);

  // WebRTC configuration
  const rtcConfig = {
    iceServers: [
      { urls: 'stun:stun.l.google.com:19302' },
      { urls: 'stun:stun1.l.google.com:19302' }
    ]
  };

  // Generate random room ID
  const generateRoomId = () => {
    return Math.random().toString(36).substring(2, 8).toUpperCase();
  };

  // Audio level monitoring
  const monitorAudioLevel = (stream, setLevel) => {
    if (!audioContextRef.current) {
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
    }

    const audioContext = audioContextRef.current;
    const analyser = audioContext.createAnalyser();
    const source = audioContext.createMediaStreamSource(stream);
    
    analyser.fftSize = 256;
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    source.connect(analyser);

    const updateLevel = () => {
      analyser.getByteFrequencyData(dataArray);
      const average = dataArray.reduce((a, b) => a + b) / bufferLength;
      setLevel(Math.min(100, (average / 255) * 100));
      
      if (stream.active) {
        requestAnimationFrame(updateLevel);
      }
    };

    updateLevel();
  };

  // Initialize WebRTC
  const initWebRTC = async () => {
    try {
      // Get user media
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true
        } 
      });
      
      localStreamRef.current = stream;
      
      // Monitor local audio level
      monitorAudioLevel(stream, setAudioLevel);

      // Create peer connection
      const peerConnection = new RTCPeerConnection(rtcConfig);
      peerConnectionRef.current = peerConnection;

      // Add local stream to peer connection
      stream.getTracks().forEach(track => {
        peerConnection.addTrack(track, stream);
      });

      // Handle remote stream
      peerConnection.ontrack = (event) => {
        const [remoteStream] = event.streams;
        remoteStreamRef.current = remoteStream;
        
        if (remoteAudioRef.current) {
          remoteAudioRef.current.srcObject = remoteStream;
          remoteAudioRef.current.volume = volume / 100;
        }

        // Monitor remote audio level
        monitorAudioLevel(remoteStream, setRemoteAudioLevel);
      };

      // Handle ICE candidates
      peerConnection.onicecandidate = (event) => {
        if (event.candidate && websocketRef.current) {
          websocketRef.current.send(JSON.stringify({
            type: 'ice-candidate',
            candidate: event.candidate
          }));
        }
      };

      // Handle connection state changes
      peerConnection.onconnectionstatechange = () => {
        setConnectionStatus(peerConnection.connectionState);
        if (peerConnection.connectionState === 'connected') {
          setIsConnected(true);
        } else if (peerConnection.connectionState === 'disconnected' || 
                   peerConnection.connectionState === 'failed') {
          setIsConnected(false);
        }
      };

      return true;
    } catch (error) {
      console.error('Error initializing WebRTC:', error);
      alert('Не удалось получить доступ к микрофону. Проверьте разрешения.');
      return false;
    }
  };

  // Connect to room
  const connectToRoom = async () => {
    if (!roomId.trim()) {
      setRoomId(generateRoomId());
      return;
    }

    try {
      // Initialize WebRTC first
      const webrtcInitialized = await initWebRTC();
      if (!webrtcInitialized) return;

      // Connect to WebSocket
      const ws = new WebSocket(`${WS_URL}/api/ws/${roomId}`);
      websocketRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected');
        ws.send(JSON.stringify({ type: 'join', room_id: roomId }));
      };

      ws.onmessage = async (event) => {
        const message = JSON.parse(event.data);
        
        switch (message.type) {
          case 'room_info':
            setCurrentRoom(message.data);
            setActiveUsers(message.data.active_users);
            break;
            
          case 'user_joined':
            setActiveUsers(message.total_users);
            // Create and send offer to new user
            if (peerConnectionRef.current) {
              const offer = await peerConnectionRef.current.createOffer();
              await peerConnectionRef.current.setLocalDescription(offer);
              ws.send(JSON.stringify({
                type: 'offer',
                offer: offer
              }));
            }
            break;
            
          case 'user_left':
            setActiveUsers(message.total_users);
            break;
            
          case 'offer':
            if (peerConnectionRef.current) {
              await peerConnectionRef.current.setRemoteDescription(message.offer);
              const answer = await peerConnectionRef.current.createAnswer();
              await peerConnectionRef.current.setLocalDescription(answer);
              ws.send(JSON.stringify({
                type: 'answer',
                answer: answer
              }));
            }
            break;
            
          case 'answer':
            if (peerConnectionRef.current) {
              await peerConnectionRef.current.setRemoteDescription(message.answer);
            }
            break;
            
          case 'ice-candidate':
            if (peerConnectionRef.current) {
              await peerConnectionRef.current.addIceCandidate(message.candidate);
            }
            break;
        }
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        setConnectionStatus('disconnected');
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionStatus('error');
      };

    } catch (error) {
      console.error('Error connecting to room:', error);
      alert('Ошибка подключения к комнате');
    }
  };

  // Disconnect from room
  const disconnectFromRoom = () => {
    // Close WebSocket
    if (websocketRef.current) {
      websocketRef.current.close();
      websocketRef.current = null;
    }

    // Close peer connection
    if (peerConnectionRef.current) {
      peerConnectionRef.current.close();
      peerConnectionRef.current = null;
    }

    // Stop local stream
    if (localStreamRef.current) {
      localStreamRef.current.getTracks().forEach(track => track.stop());
      localStreamRef.current = null;
    }

    // Close audio context
    if (audioContextRef.current) {
      audioContextRef.current.close();
      audioContextRef.current = null;
    }

    // Reset state
    setIsConnected(false);
    setCurrentRoom(null);
    setConnectionStatus('disconnected');
    setActiveUsers(0);
    setAudioLevel(0);
    setRemoteAudioLevel(0);
  };

  // Toggle mute
  const toggleMute = () => {
    if (localStreamRef.current) {
      const audioTrack = localStreamRef.current.getAudioTracks()[0];
      if (audioTrack) {
        audioTrack.enabled = !audioTrack.enabled;
        setIsMuted(!audioTrack.enabled);
      }
    }
  };

  // Update volume
  const updateVolume = (newVolume) => {
    setVolume(newVolume);
    if (remoteAudioRef.current) {
      remoteAudioRef.current.volume = newVolume / 100;
    }
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnectFromRoom();
    };
  }, []);

  return (
    <div className="app">
      <div className="container">
        <div className="header">
          <h1>🎙️ Голосовой чат</h1>
          <p>Общайтесь с друзьями из любой точки мира</p>
        </div>

        <div className="main-content">
          {!isConnected ? (
            <div className="connection-panel">
              <div className="room-input">
                <label>ID комнаты:</label>
                <div className="input-group">
                  <input
                    type="text"
                    value={roomId}
                    onChange={(e) => setRoomId(e.target.value.toUpperCase())}
                    placeholder="Введите ID или оставьте пустым"
                    maxLength={6}
                  />
                  <button 
                    className="generate-btn"
                    onClick={() => setRoomId(generateRoomId())}
                  >
                    🎲
                  </button>
                </div>
              </div>
              
              <button className="connect-btn" onClick={connectToRoom}>
                {roomId ? `Подключиться к ${roomId}` : 'Создать новую комнату'}
              </button>
              
              <div className="instructions">
                <p>💡 <strong>Как использовать:</strong></p>
                <p>1. Введите ID комнаты или создайте новую</p>
                <p>2. Поделитесь ID с другом</p>
                <p>3. Наслаждайтесь общением!</p>
              </div>
            </div>
          ) : (
            <div className="voice-controls">
              <div className="room-info">
                <h3>Комната: {roomId}</h3>
                <div className="status-indicators">
                  <div className={`status-dot ${connectionStatus}`}></div>
                  <span>Статус: {connectionStatus === 'connected' ? 'Подключен' : 'Подключение...'}</span>
                  <span>👥 Участников: {activeUsers}</span>
                </div>
              </div>

              <div className="audio-controls">
                <button 
                  className={`control-btn ${isMuted ? 'muted' : ''}`}
                  onClick={toggleMute}
                >
                  {isMuted ? '🔇' : '🎤'}
                  <span>{isMuted ? 'Включить микрофон' : 'Выключить микрофон'}</span>
                </button>

                <div className="volume-control">
                  <label>🔊 Громкость: {volume}%</label>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={volume}
                    onChange={(e) => updateVolume(parseInt(e.target.value))}
                    className="volume-slider"
                  />
                </div>
              </div>

              <div className="audio-levels">
                <div className="level-indicator">
                  <label>Ваш микрофон:</label>
                  <div className="level-bar">
                    <div 
                      className="level-fill local" 
                      style={{ width: `${audioLevel}%` }}
                    ></div>
                  </div>
                  <span>{Math.round(audioLevel)}%</span>
                </div>

                <div className="level-indicator">
                  <label>Входящий звук:</label>
                  <div className="level-bar">
                    <div 
                      className="level-fill remote" 
                      style={{ width: `${remoteAudioLevel}%` }}
                    ></div>
                  </div>
                  <span>{Math.round(remoteAudioLevel)}%</span>
                </div>
              </div>

              <button className="disconnect-btn" onClick={disconnectFromRoom}>
                Отключиться
              </button>
            </div>
          )}
        </div>

        {/* Hidden audio element for remote stream */}
        <audio ref={remoteAudioRef} autoPlay playsInline />
      </div>
    </div>
  );
}

export default App;