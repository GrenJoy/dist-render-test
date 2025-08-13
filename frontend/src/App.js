import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import axios from 'axios';
import Sidebar from './components/Sidebar';
import Chat from './components/Chat';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'https://voice-connect-22.preview.emergentagent.com';
const API = `${BACKEND_URL}/api`;
const WS_URL = BACKEND_URL ? BACKEND_URL.replace('https://', 'wss://').replace('http://', 'ws://') : 'wss://voice-connect-22.preview.emergentagent.com';

function App() {
  // Room and connection state
  const [roomId, setRoomId] = useState('');
  const [currentRoom, setCurrentRoom] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  
  // User state
  const [currentUser, setCurrentUser] = useState({
    id: localStorage.getItem('userId') || generateUserId(),
    username: localStorage.getItem('username') || ''
  });
  const [users, setUsers] = useState([]);
  
  // Voice state
  const [isInVoice, setIsInVoice] = useState(false);
  const [isMuted, setIsMuted] = useState(false);
  const [volume, setVolume] = useState(80);
  const [audioLevel, setAudioLevel] = useState(0);
  const [remoteAudioLevel, setRemoteAudioLevel] = useState(0);
  
  // Chat state
  const [messages, setMessages] = useState([]);
  const [rooms, setRooms] = useState([]);
  const [showRooms, setShowRooms] = useState(false);
  
  // WebRTC state
  const [peerConnectionState, setPeerConnectionState] = useState('new');
  const [pendingIceCandidates, setPendingIceCandidates] = useState([]);

  // Refs
  const localStreamRef = useRef(null);
  const remoteStreamRef = useRef(null);
  const peerConnectionRef = useRef(null);
  const websocketRef = useRef(null);
  const remoteAudioRef = useRef(null);
  const audioContextRef = useRef(null);

  // WebRTC configuration with STUN servers only
  const rtcConfig = {
    iceServers: [
      // STUN серверы (бесплатные, надежные)
      { urls: 'stun:stun.l.google.com:19302' },
      { urls: 'stun:stun1.l.google.com:19302' },
      { urls: 'stun:stun2.l.google.com:19302' },
      { urls: 'stun:stun3.l.google.com:19302' },
      { urls: 'stun:stun4.l.google.com:19302' }
    ],
    iceCandidatePoolSize: 10,
    iceTransportPolicy: 'all',
    bundlePolicy: 'max-bundle',
    rtcpMuxPolicy: 'require'
  };

  // Generate user ID
  function generateUserId() {
    return Math.random().toString(36).substring(2, 15);
  }

  // Generate random room ID
  const generateRoomId = () => {
    return Math.random().toString(36).substring(2, 8).toUpperCase();
  };

  // Initialize user
  useEffect(() => {
    if (!localStorage.getItem('userId')) {
      localStorage.setItem('userId', currentUser.id);
    }
  }, [currentUser.id]);

  // Load existing rooms
  const loadRooms = async () => {
    try {
      const response = await axios.get(`${API}/rooms`);
      setRooms(response.data);
    } catch (error) {
      console.error('Error loading rooms:', error);
    }
  };

  // Audio level monitoring with noise suppression
  const monitorAudioLevel = (stream, setLevel) => {
    if (!audioContextRef.current) {
      audioContextRef.current = new (window.AudioContext || window.webkitAudioContext)();
    }

    const audioContext = audioContextRef.current;
    const analyser = audioContext.createAnalyser();
    const source = audioContext.createMediaStreamSource(stream);
    
    // Add noise suppression filter
    const filter = audioContext.createBiquadFilter();
    filter.type = 'highpass';
    filter.frequency.setValueAtTime(300, audioContext.currentTime); // Filter out low frequencies
    
    const compressor = audioContext.createDynamicsCompressor();
    compressor.threshold.setValueAtTime(-24, audioContext.currentTime);
    compressor.knee.setValueAtTime(30, audioContext.currentTime);
    compressor.ratio.setValueAtTime(12, audioContext.currentTime);
    compressor.attack.setValueAtTime(0.003, audioContext.currentTime);
    compressor.release.setValueAtTime(0.25, audioContext.currentTime);
    
    analyser.fftSize = 256;
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    // Connect audio nodes
    source.connect(filter);
    filter.connect(compressor);
    compressor.connect(analyser);

    const updateLevel = () => {
      analyser.getByteFrequencyData(dataArray);
      const average = dataArray.reduce((a, b) => a + b) / bufferLength;
      const level = Math.min(100, (average / 255) * 100);
      
      // Only show level if above noise threshold
      setLevel(level > 5 ? level : 0);
      
      if (stream.active) {
        requestAnimationFrame(updateLevel);
      }
    };

    updateLevel();
  };

  // Initialize WebRTC
  const initWebRTC = async () => {
    try {
      if (peerConnectionRef.current) {
        console.log('PeerConnection already exists, reusing');
        return true;
      }

      // Get user media with enhanced audio settings
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
          sampleRate: 48000,
          channelCount: 1
        } 
      });
      
      localStreamRef.current = stream;
      monitorAudioLevel(stream, setAudioLevel);

      // Create peer connection
      const peerConnection = new RTCPeerConnection(rtcConfig);
      peerConnectionRef.current = peerConnection;

      // Add local stream
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

        monitorAudioLevel(remoteStream, setRemoteAudioLevel);
      };

      // Handle ICE candidates
      peerConnection.onicecandidate = (event) => {
        if (event.candidate && websocketRef.current && websocketRef.current.readyState === WebSocket.OPEN) {
          websocketRef.current.send(JSON.stringify({
            type: 'ice-candidate',
            candidate: event.candidate
          }));
        }
      };

      // Handle connection state changes
      peerConnection.onconnectionstatechange = () => {
        setConnectionStatus(peerConnection.connectionState);
        setPeerConnectionState(peerConnection.signalingState);
        
        console.log('WebRTC connection state:', peerConnection.connectionState);
        console.log('WebRTC signaling state:', peerConnection.signalingState);
        
        if (peerConnection.connectionState === 'connected') {
          console.log('WebRTC connected successfully!');
        } else if (peerConnection.connectionState === 'failed') {
          console.error('WebRTC connection failed!');
          resetWebRTC();
        } else if (peerConnection.connectionState === 'disconnected') {
          console.warn('WebRTC disconnected, attempting to reconnect...');
        }
      };

      // Handle ICE connection state changes
      peerConnection.oniceconnectionstatechange = () => {
        console.log('ICE connection state:', peerConnection.iceConnectionState);
        
        if (peerConnection.iceConnectionState === 'failed') {
          console.error('ICE connection failed, trying to restart ICE...');
          peerConnection.restartIce();
        }
      };

      // Handle signaling state changes
      peerConnection.onsignalingstatechange = () => {
        console.log('Signaling state changed:', peerConnection.signalingState);
        setPeerConnectionState(peerConnection.signalingState);
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

    if (!currentUser.username.trim()) {
      const username = prompt('Введите ваше имя:');
      if (!username) return;
      
      const updatedUser = { ...currentUser, username: username.trim() };
      setCurrentUser(updatedUser);
      localStorage.setItem('username', username.trim());
      return;
    }

    // Если уже подключены к другой комнате, сначала отключимся
    if (isConnected) {
      await disconnectFromRoom();
    }

    setConnectionStatus('connecting');

    try {
      // Create room if doesn't exist
      await axios.post(`${API}/rooms`, {
        name: `Room ${roomId}`,
        id: roomId
      });

      // Connect WebSocket with user info
      const ws = new WebSocket(`${WS_URL}/api/ws/${roomId}?user_id=${currentUser.id}&username=${encodeURIComponent(currentUser.username)}`);
      websocketRef.current = ws;

      ws.onopen = () => {
        console.log('WebSocket connected to room:', roomId);
        setIsConnected(true);
        setConnectionStatus('connected');
        ws.send(JSON.stringify({ type: 'join', room_id: roomId }));
      };

      ws.onmessage = async (event) => {
        const message = JSON.parse(event.data);
        console.log('WebSocket message:', message.type);
        
        await handleWebSocketMessage(message, ws);
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        setConnectionStatus('disconnected');
        resetWebRTC();
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setConnectionStatus('error');
      };

    } catch (error) {
      console.error('Error connecting to room:', error);
      alert('Ошибка подключения к комнате');
      setConnectionStatus('disconnected');
    }
  };

  // Handle WebSocket messages
  const handleWebSocketMessage = async (message, ws) => {
    switch (message.type) {
      case 'room_info':
        setCurrentRoom(message.data);
        setUsers(message.data.users || []);
        if (message.messages) {
          setMessages(message.messages);
        }
        break;
        
      case 'user_joined':
        setUsers(prev => {
          const exists = prev.find(u => u.id === message.user.id);
          if (exists) return prev;
          return [...prev, message.user];
        });
        break;
        
      case 'user_left':
        setUsers(prev => prev.filter(u => u.id !== message.user.id));
        break;
        
      case 'user_voice_update':
        setUsers(prev => 
          prev.map(u => 
            u.id === message.user_id 
              ? { ...u, is_in_voice: message.is_in_voice }
              : u
          )
        );
        break;
        
      case 'new_message':
        setMessages(prev => [...prev, message.message]);
        break;
        
      case 'offer':
        console.log('Received offer, current signaling state:', peerConnectionRef.current?.signalingState);
        if (peerConnectionRef.current && peerConnectionRef.current.signalingState === 'stable') {
          try {
            console.log('Setting remote description from offer...');
            await peerConnectionRef.current.setRemoteDescription(message.offer);
            console.log('Remote description set successfully');
            
            // Apply pending ICE candidates
            for (const candidate of pendingIceCandidates) {
              try {
                await peerConnectionRef.current.addIceCandidate(candidate);
                console.log('Added pending ICE candidate:', candidate);
              } catch (error) {
                console.warn('Error adding pending ICE candidate:', error);
              }
            }
            setPendingIceCandidates([]);
            
            console.log('Creating answer...');
            const answer = await peerConnectionRef.current.createAnswer();
            await peerConnectionRef.current.setLocalDescription(answer);
            console.log('Answer created and set locally');
            
            ws.send(JSON.stringify({
              type: 'answer',
              answer: answer
            }));
            console.log('Answer sent to peer');
          } catch (error) {
            console.error('Error handling offer:', error);
            resetWebRTC();
          }
        } else {
          console.warn('Cannot handle offer in current state:', peerConnectionRef.current?.signalingState);
        }
        break;
        
      case 'answer':
        console.log('Received answer, current signaling state:', peerConnectionRef.current?.signalingState);
        if (peerConnectionRef.current && peerConnectionRef.current.signalingState === 'have-local-offer') {
          try {
            console.log('Setting remote description from answer...');
            await peerConnectionRef.current.setRemoteDescription(message.answer);
            console.log('Remote description set from answer successfully');
          } catch (error) {
            console.error('Error handling answer:', error);
            resetWebRTC();
          }
        } else {
          console.warn('Cannot handle answer in current state:', peerConnectionRef.current?.signalingState);
        }
        break;
        
      case 'ice-candidate':
        console.log('Received ICE candidate, remote description exists:', !!peerConnectionRef.current?.remoteDescription);
        if (peerConnectionRef.current && peerConnectionRef.current.remoteDescription) {
          try {
            await peerConnectionRef.current.addIceCandidate(message.candidate);
            console.log('ICE candidate added successfully');
          } catch (error) {
            console.error('Error adding ICE candidate:', error);
          }
        } else {
          console.log('Storing ICE candidate for later, current count:', pendingIceCandidates.length);
          setPendingIceCandidates(prev => [...prev, message.candidate]);
        }
        break;
    }
  };

  // Join voice call
  const joinVoiceCall = async () => {
    console.log('Joining voice call...');
    const webrtcInitialized = await initWebRTC();
    if (!webrtcInitialized) {
      console.error('Failed to initialize WebRTC');
      return;
    }

    setIsInVoice(true);
    
    if (websocketRef.current) {
      websocketRef.current.send(JSON.stringify({ type: 'join_voice' }));
      
      // Create offer if we're the initiator
      const usersInVoice = users.filter(u => u.is_in_voice);
      console.log('Users in voice:', usersInVoice.length);
      
      if (usersInVoice.length === 0) {
        try {
          console.log('Creating offer as initiator...');
          const offer = await peerConnectionRef.current.createOffer();
          await peerConnectionRef.current.setLocalDescription(offer);
          console.log('Offer created and set locally');
          
          websocketRef.current.send(JSON.stringify({
            type: 'offer',
            offer: offer
          }));
          console.log('Offer sent to peer');
        } catch (error) {
          console.error('Error creating offer:', error);
          resetWebRTC();
        }
      } else {
        console.log('Joining as participant, waiting for offer...');
      }
    }
  };

  // Leave voice call
  const leaveVoiceCall = () => {
    setIsInVoice(false);
    
    if (websocketRef.current) {
      websocketRef.current.send(JSON.stringify({ type: 'leave_voice' }));
    }
    
    // Stop local stream
    if (localStreamRef.current) {
      localStreamRef.current.getTracks().forEach(track => track.stop());
      localStreamRef.current = null;
    }
    
    // Close peer connection
    if (peerConnectionRef.current) {
      peerConnectionRef.current.close();
      peerConnectionRef.current = null;
    }
    
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

  // Send message
  const sendMessage = async (messageText) => {
    try {
      await axios.post(`${API}/rooms/${roomId}/messages`, {
        user_id: currentUser.id,
        username: currentUser.username,
        message: messageText
      });
    } catch (error) {
      console.error('Error sending message:', error);
    }
  };

  // Upload file
  const uploadFile = async (file) => {
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('user_id', currentUser.id);
      formData.append('username', currentUser.username);
      
      await axios.post(`${API}/rooms/${roomId}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      });
    } catch (error) {
      console.error('Error uploading file:', error);
      alert('Ошибка при загрузке файла');
    }
  };

  // Disconnect from room
  const disconnectFromRoom = () => {
    console.log('Disconnecting from room...');
    
    if (websocketRef.current) {
      try {
        websocketRef.current.close();
        console.log('WebSocket closed');
      } catch (error) {
        console.warn('Error closing WebSocket:', error);
      }
      websocketRef.current = null;
    }
    
    leaveVoiceCall();
    
    setIsConnected(false);
    setConnectionStatus('disconnected');
    setCurrentRoom(null);
    setUsers([]);
    setMessages([]);
    setPeerConnectionState('new');
    
    console.log('Disconnected from room');
  };

  // Change room
  const changeRoom = async (newRoomId) => {
    console.log('Changing room from', roomId, 'to', newRoomId);
    
    if (isConnected) {
      await disconnectFromRoom();
    }
    
    setRoomId(newRoomId);
    await connectToRoom();
  };

  // Reset WebRTC
  const resetWebRTC = () => {
    console.log('Resetting WebRTC connection...');
    
    if (peerConnectionRef.current) {
      try {
        peerConnectionRef.current.close();
      } catch (error) {
        console.warn('Error closing peer connection:', error);
      }
      peerConnectionRef.current = null;
    }
    
    if (localStreamRef.current) {
      try {
        localStreamRef.current.getTracks().forEach(track => {
          track.stop();
          console.log('Stopped track:', track.kind);
        });
      } catch (error) {
        console.warn('Error stopping tracks:', error);
      }
      localStreamRef.current = null;
    }
    
    if (remoteStreamRef.current) {
      remoteStreamRef.current = null;
    }
    
    setPeerConnectionState('new');
    setPendingIceCandidates([]);
    setConnectionStatus('disconnected');
    setIsInVoice(false);
    
    console.log('WebRTC reset completed');
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnectFromRoom();
    };
  }, []);

  // Update username prompt
  const promptUsername = () => {
    const username = prompt('Введите ваше имя:', currentUser.username);
    if (username && username.trim()) {
      const updatedUser = { ...currentUser, username: username.trim() };
      setCurrentUser(updatedUser);
      localStorage.setItem('username', username.trim());
    }
  };

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {!isConnected ? (
        // Connection Screen
        <div className="min-h-screen flex items-center justify-center p-8">
          <div className="max-w-md w-full space-y-8">
            <div className="text-center">
              <h1 className="text-4xl font-bold text-white mb-2">🎙️ Голосовой чат</h1>
              <p className="text-gray-400">Общайтесь с друзьями из любой точки мира</p>
            </div>

            <div className="bg-gray-800 rounded-lg p-6 space-y-6">
              {/* Username Input */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Ваше имя
                </label>
                <input
                  type="text"
                  value={currentUser.username}
                  onChange={(e) => setCurrentUser(prev => ({ ...prev, username: e.target.value }))}
                  placeholder="Введите ваше имя"
                  className="w-full bg-gray-700 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Room ID Input */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  ID комнаты
                </label>
                <div className="flex gap-2">
                  <input
                    type="text"
                    value={roomId}
                    onChange={(e) => setRoomId(e.target.value.toUpperCase())}
                    placeholder="Введите ID или оставьте пустым"
                    maxLength={6}
                    className="flex-1 bg-gray-700 text-white rounded-lg px-4 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  <button 
                    className="bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg transition-colors"
                    onClick={() => setRoomId(generateRoomId())}
                    title="Случайный ID"
                  >
                    🎲
                  </button>
                </div>
              </div>
              
              <button 
                className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 px-4 rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                onClick={connectToRoom}
                disabled={!currentUser.username.trim() || connectionStatus === 'connecting'}
              >
                {connectionStatus === 'connecting' 
                  ? 'Подключение...' 
                  : roomId 
                    ? `Подключиться к ${roomId}` 
                    : 'Создать новую комнату'
                }
              </button>
              
              <div className="text-center">
                <button 
                  className="text-blue-400 hover:text-blue-300 text-sm transition-colors"
                  onClick={() => {
                    setShowRooms(!showRooms);
                    if (!showRooms) loadRooms();
                  }}
                >
                  {showRooms ? 'Скрыть комнаты' : 'Показать существующие комнаты'}
                </button>
              </div>
              
              {showRooms && (
                <div className="border-t border-gray-700 pt-4">
                  <h4 className="text-white font-medium mb-3">Существующие комнаты:</h4>
                  {rooms.length === 0 ? (
                    <p className="text-gray-400 text-sm">Комнат пока нет. Создайте первую!</p>
                  ) : (
                    <div className="space-y-2">
                      {rooms.map(room => (
                        <div key={room.id} className="flex items-center justify-between bg-gray-700 rounded-lg p-3">
                          <div>
                            <span className="text-white font-medium">{room.id}</span>
                            <div className="text-gray-400 text-xs">👥 {room.active_users} участников</div>
                          </div>
                          <button 
                            className="bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded text-sm transition-colors"
                            onClick={() => {
                              setRoomId(room.id);
                              setShowRooms(false);
                            }}
                          >
                            Войти
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            <div className="text-center text-gray-400 text-sm">
              <p>💡 <strong>Как использовать:</strong></p>
              <p>1. Введите ваше имя и ID комнаты</p>
              <p>2. Поделитесь ID с друзьями</p>
              <p>3. Наслаждайтесь общением!</p>
            </div>
          </div>
        </div>
      ) : (
        // Main Discord-like Interface
        <div className="flex h-screen">
          {/* Sidebar */}
          <Sidebar
            users={users}
            currentUser={currentUser}
            isConnected={isConnected}
            joinVoiceCall={joinVoiceCall}
            leaveVoiceCall={leaveVoiceCall}
            isInVoice={isInVoice}
            isMuted={isMuted}
            toggleMute={toggleMute}
            volume={volume}
            setVolume={updateVolume}
          />

          {/* Main Content */}
          <div className="flex-1 bg-gray-700 flex flex-col">
            {/* Header */}
            <div className="bg-gray-800 border-b border-gray-700 p-4 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="text-lg font-semibold text-white">
                  # {roomId}
                </div>
                <div className="text-gray-400 text-sm">
                  {users.length} участников
                </div>
              </div>
              
              <div className="flex items-center gap-4">
                {/* Audio Level Indicators */}
                {isInVoice && (
                  <div className="flex items-center gap-4 text-sm">
                    <div className="flex items-center gap-2">
                      <span className="text-gray-400">Ваш микрофон:</span>
                      <div className="w-16 h-2 bg-gray-600 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-green-500 transition-all duration-100"
                          style={{ width: `${audioLevel}%` }}
                        />
                      </div>
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <span className="text-gray-400">Входящий:</span>
                      <div className="w-16 h-2 bg-gray-600 rounded-full overflow-hidden">
                        <div 
                          className="h-full bg-blue-500 transition-all duration-100"
                          style={{ width: `${remoteAudioLevel}%` }}
                        />
                      </div>
                    </div>
                  </div>
                )}
                
                <button
                  onClick={disconnectFromRoom}
                  className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
                >
                  Выйти из комнаты
                </button>
              </div>
            </div>

            {/* Content Area */}
            <div className="flex-1 flex items-center justify-center p-8">
              <div className="text-center">
                <h2 className="text-2xl font-semibold text-white mb-2">
                  Добро пожаловать в комнату {roomId}!
                </h2>
                <p className="text-gray-400 mb-6">
                  {isInVoice 
                    ? 'Вы в голосовом канале. Используйте чат справа для текстового общения.'
                    : 'Присоединитесь к голосовому каналу или используйте чат для общения.'
                  }
                </p>
                
                {connectionStatus !== 'connected' && connectionStatus !== 'connecting' && (
                  <div className="text-yellow-400">
                    WebRTC статус: {peerConnectionState}
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Chat */}
          <Chat
            messages={messages}
            onSendMessage={sendMessage}
            onUploadFile={uploadFile}
            currentUser={currentUser}
          />

          {/* Hidden audio element for remote stream */}
          <audio ref={remoteAudioRef} autoPlay playsInline />
        </div>
      )}
    </div>
  );
}

export default App;