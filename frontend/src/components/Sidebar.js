import React from 'react';
import { Users, Mic, MicOff, Volume2, VolumeX, Settings } from 'lucide-react';

const Sidebar = ({ 
  users = [], 
  currentUser, 
  isConnected, 
  joinVoiceCall, 
  leaveVoiceCall, 
  isInVoice,
  isMuted,
  toggleMute,
  volume,
  setVolume 
}) => {
  return (
    <div className="w-80 bg-gray-800 flex flex-col h-full">
      {/* Server Header */}
      <div className="p-4 border-b border-gray-700">
        <h2 className="text-xl font-semibold text-white">Голосовой чат</h2>
        <p className="text-gray-400 text-sm">Общайтесь с друзьями</p>
      </div>

      {/* Voice Channel */}
      <div className="p-4 border-b border-gray-700">
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <Volume2 className="w-5 h-5 text-gray-400" />
            <span className="text-gray-300 font-medium">Голосовой канал</span>
          </div>
          <span className="text-gray-500 text-sm">{users.length}/4</span>
        </div>

        {/* Voice Controls */}
        {isConnected && (
          <div className="space-y-3">
            {!isInVoice ? (
              <button
                onClick={joinVoiceCall}
                className="w-full bg-green-600 hover:bg-green-700 text-white py-2 px-4 rounded-lg font-medium transition-colors"
              >
                Присоединиться к разговору
              </button>
            ) : (
              <button
                onClick={leaveVoiceCall}
                className="w-full bg-red-600 hover:bg-red-700 text-white py-2 px-4 rounded-lg font-medium transition-colors"
              >
                Покинуть разговор
              </button>
            )}

            {isInVoice && (
              <div className="space-y-2">
                {/* Mute Button */}
                <button
                  onClick={toggleMute}
                  className={`w-full py-2 px-4 rounded-lg font-medium transition-colors ${
                    isMuted 
                      ? 'bg-red-600 hover:bg-red-700 text-white' 
                      : 'bg-gray-600 hover:bg-gray-700 text-white'
                  }`}
                >
                  <div className="flex items-center justify-center gap-2">
                    {isMuted ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                    {isMuted ? 'Включить микрофон' : 'Выключить микрофон'}
                  </div>
                </button>

                {/* Volume Control */}
                <div className="space-y-1">
                  <label className="text-gray-300 text-sm">Громкость: {volume}%</label>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={volume}
                    onChange={(e) => setVolume(parseInt(e.target.value))}
                    className="w-full h-2 bg-gray-700 rounded-lg appearance-none cursor-pointer slider"
                    style={{
                      background: `linear-gradient(to right, #5865F2 0%, #5865F2 ${volume}%, #4F5660 ${volume}%, #4F5660 100%)`
                    }}
                  />
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Users List */}
      <div className="flex-1 p-4">
        <div className="flex items-center gap-2 mb-3">
          <Users className="w-5 h-5 text-gray-400" />
          <span className="text-gray-300 font-medium">Участники — {users.length}</span>
        </div>

        <div className="space-y-2">
          {users.map((user) => (
            <div key={user.id} className="flex items-center gap-3 p-2 rounded-lg hover:bg-gray-700 transition-colors">
              {/* Avatar */}
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white font-semibold ${
                user.is_in_voice ? 'bg-green-600 ring-2 ring-green-400' : 'bg-gray-600'
              }`}>
                {user.username.charAt(0).toUpperCase()}
              </div>

              {/* Username */}
              <div className="flex-1">
                <div className="text-gray-300 font-medium">{user.username}</div>
                {user.is_in_voice && (
                  <div className="text-green-400 text-xs">В голосовом канале</div>
                )}
              </div>

              {/* Voice Status Icon */}
              {user.is_in_voice && (
                <div className="text-green-400">
                  <Mic className="w-4 h-4" />
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* User Panel */}
      <div className="p-4 border-t border-gray-700">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white font-semibold">
            {currentUser?.username?.charAt(0)?.toUpperCase() || 'U'}
          </div>
          <div className="flex-1">
            <div className="text-gray-300 font-medium">{currentUser?.username || 'Пользователь'}</div>
            <div className="text-gray-500 text-xs">
              {isConnected ? 'В сети' : 'Не подключен'}
            </div>
          </div>
          <button className="text-gray-400 hover:text-gray-300 transition-colors">
            <Settings className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default Sidebar;