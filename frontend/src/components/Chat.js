import React, { useState, useRef, useEffect } from 'react';
import { Send, Image, X, Paperclip } from 'lucide-react';

const Chat = ({ messages = [], onSendMessage, onUploadFile, currentUser }) => {
  const [message, setMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [typingUsers, setTypingUsers] = useState([]);
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSendMessage = (e) => {
    e.preventDefault();
    if (message.trim() && onSendMessage) {
      onSendMessage(message.trim());
      setMessage('');
      setIsTyping(false);
    }
  };

  const handleFileUpload = (e) => {
    const file = e.target.files[0];
    if (file && onUploadFile) {
      onUploadFile(file);
    }
    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('ru-RU', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  const formatDate = (timestamp) => {
    const date = new Date(timestamp);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    if (date.toDateString() === today.toDateString()) {
      return 'Сегодня';
    } else if (date.toDateString() === yesterday.toDateString()) {
      return 'Вчера';
    } else {
      return date.toLocaleDateString('ru-RU', { 
        day: 'numeric', 
        month: 'long' 
      });
    }
  };

  const groupMessagesByDate = (messages) => {
    const groups = {};
    messages.forEach(msg => {
      const date = new Date(msg.timestamp).toDateString();
      if (!groups[date]) {
        groups[date] = [];
      }
      groups[date].push(msg);
    });
    return groups;
  };

  const messageGroups = groupMessagesByDate(messages);

  return (
    <div className="w-80 bg-gray-750 flex flex-col h-full border-l border-gray-700">
      {/* Chat Header */}
      <div className="p-4 border-b border-gray-700">
        <h3 className="text-lg font-semibold text-white">Чат</h3>
        <p className="text-gray-400 text-sm">Общайтесь в текстовом формате</p>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {Object.entries(messageGroups).map(([date, msgs]) => (
          <div key={date}>
            {/* Date Separator */}
            <div className="flex items-center gap-4 my-6">
              <div className="flex-1 h-px bg-gray-600"></div>
              <span className="text-gray-400 text-xs font-medium px-3 py-1 bg-gray-700 rounded-full">
                {formatDate(msgs[0].timestamp)}
              </span>
              <div className="flex-1 h-px bg-gray-600"></div>
            </div>

            {/* Messages */}
            {msgs.map((msg) => (
              <div key={msg.id} className="group hover:bg-gray-800 -mx-4 px-4 py-2 rounded-lg transition-colors">
                <div className="flex items-start gap-3">
                  {/* Avatar */}
                  <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center text-white font-semibold text-sm mt-1">
                    {msg.username.charAt(0).toUpperCase()}
                  </div>

                  <div className="flex-1 min-w-0">
                    {/* Username and Time */}
                    <div className="flex items-baseline gap-2 mb-1">
                      <span className="font-semibold text-white">{msg.username}</span>
                      <span className="text-gray-500 text-xs">{formatTime(msg.timestamp)}</span>
                    </div>

                    {/* Message Content */}
                    {msg.message_type === 'text' ? (
                      <p className="text-gray-300 leading-relaxed break-words">{msg.message}</p>
                    ) : msg.message_type === 'image' ? (
                      <div className="space-y-2">
                        <p className="text-gray-400 text-sm">{msg.message}</p>
                        <div className="relative inline-block">
                          <img 
                            src={`${process.env.REACT_APP_BACKEND_URL}${msg.file_url}`}
                            alt="Uploaded image"
                            className="max-w-xs max-h-64 rounded-lg cursor-pointer hover:opacity-90 transition-opacity"
                            onClick={() => window.open(`${process.env.REACT_APP_BACKEND_URL}${msg.file_url}`, '_blank')}
                          />
                        </div>
                      </div>
                    ) : null}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ))}

        {/* Typing Indicator */}
        {typingUsers.length > 0 && (
          <div className="flex items-center gap-2 text-gray-400 text-sm">
            <div className="flex gap-1">
              <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce"></div>
              <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
              <div className="w-2 h-2 bg-gray-500 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
            </div>
            <span>{typingUsers.join(', ')} печатает...</span>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Message Input */}
      <div className="p-4 border-t border-gray-700">
        <form onSubmit={handleSendMessage} className="space-y-3">
          <div className="flex gap-2">
            {/* File Upload Button */}
            <button
              type="button"
              onClick={() => fileInputRef.current?.click()}
              className="p-2 text-gray-400 hover:text-gray-300 hover:bg-gray-700 rounded-lg transition-colors"
              title="Прикрепить изображение"
            >
              <Image className="w-5 h-5" />
            </button>

            {/* Message Input */}
            <div className="flex-1 relative">
              <input
                type="text"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="Напишите сообщение..."
                className="w-full bg-gray-700 text-white placeholder-gray-400 rounded-lg px-4 py-2 pr-12 focus:outline-none focus:ring-2 focus:ring-blue-500"
                maxLength={2000}
              />
              
              {/* Send Button */}
              <button
                type="submit"
                disabled={!message.trim()}
                className="absolute right-2 top-1/2 transform -translate-y-1/2 p-1 text-gray-400 hover:text-blue-400 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
          </div>

          {/* Character Counter */}
          <div className="text-right">
            <span className={`text-xs ${message.length > 1800 ? 'text-red-400' : 'text-gray-500'}`}>
              {message.length}/2000
            </span>
          </div>
        </form>

        {/* Hidden File Input */}
        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          onChange={handleFileUpload}
          className="hidden"
        />
      </div>
    </div>
  );
};

export default Chat;