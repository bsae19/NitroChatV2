import React, { useState } from 'react';
import { Button, TextInput } from 'flowbite-react';
import { FaPaperPlane, FaPlus, FaHashtag, FaUserFriends, FaCog, FaHome, FaEllipsisV } from 'react-icons/fa';
import { useNavigate } from 'react-router-dom';

const Chat: React.FC = () => {
  const [message, setMessage] = useState<string>('');
  let navigate = useNavigate();

  const handleSendMessage = () => {
    // Logique d'envoi de message ici
    setMessage('');
  };

  const dummyMessages = [
    { id: 1, user: 'Alex', content: 'Bonjour tout le monde !', time: '10:30' },
    { id: 2, user: 'Marie', content: 'Salut Alex, comment ça va aujourd\'hui ?', time: '10:31' },
    { id: 3, user: 'Thomas', content: 'Quelqu\'un a des nouvelles du projet ?', time: '10:35' },
    { id: 4, user: 'Alex', content: 'Oui, j\'ai terminé la partie frontend hier soir.', time: '10:36' },
  ];

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Barre latérale de navigation */}
      <div className="bg-gray-800 w-16 flex flex-col items-center py-4">
        <button className="w-10 h-10 bg-blue-600 rounded-full flex items-center justify-center text-white mb-4 hover:bg-blue-700 transition-colors">
          <FaHome className="text-lg" />
        </button>
        
        <div className="flex flex-col space-y-3">
          <button className="w-10 h-10 bg-gray-700 rounded-full flex items-center justify-center text-gray-200 hover:bg-blue-600 transition-colors">
            <span className="text-xs font-bold">S1</span>
          </button>
          <button className="w-10 h-10 bg-gray-700 rounded-full flex items-center justify-center text-gray-200 hover:bg-blue-600 transition-colors">
            <span className="text-xs font-bold">S2</span>
          </button>
          <button className="w-10 h-10 bg-gray-700 rounded-full flex items-center justify-center text-gray-200 hover:bg-blue-600 transition-colors">
            <FaPlus />
          </button>
        </div>
        
        <div className="mt-auto">
          <button className="w-10 h-10 rounded-full flex items-center justify-center text-gray-400 hover:bg-gray-700 transition-colors"
            onClick={() => navigate("/profile")}>
            <FaCog />
          </button>
        </div>
      </div>
      
      {/* Liste des canaux */}
      <div className="bg-gray-700 w-60 text-gray-200">
        <div className="p-4 border-b border-gray-600">
          <div className="flex justify-between items-center">
            <h2 className="font-bold">Serveur Principal</h2>
            <button className="text-gray-400 hover:text-white">
              <FaEllipsisV />
            </button>
          </div>
        </div>
        
        <div className="p-2">
          <div className="text-sm text-gray-400 font-medium p-2 flex items-center">
            <span>CANAUX DE TEXTE</span>
            <button className="ml-auto text-gray-400 hover:text-white">
              <FaPlus size="12" />
            </button>
          </div>
          
          <ul className="space-y-1">
            <li>
              <button className="w-full flex items-center p-2 rounded hover:bg-gray-600 text-left">
                <FaHashtag className="mr-2 text-gray-400" />
                <span>général</span>
              </button>
            </li>
            <li>
              <button className="w-full flex items-center p-2 rounded bg-gray-600 text-white text-left">
                <FaHashtag className="mr-2 text-gray-400" />
                <span>développement</span>
              </button>
            </li>
            <li>
              <button className="w-full flex items-center p-2 rounded hover:bg-gray-600 text-left">
                <FaHashtag className="mr-2 text-gray-400" />
                <span>ressources</span>
              </button>
            </li>
          </ul>
          
          <div className="text-sm text-gray-400 font-medium p-2 mt-4 flex items-center">
            <span>SALONS VOCAUX</span>
            <button className="ml-auto text-gray-400 hover:text-white">
              <FaPlus size="12" />
            </button>
          </div>
          
          <ul className="space-y-1">
            <li>
              <button className="w-full flex items-center p-2 rounded hover:bg-gray-600 text-left">
                <FaUserFriends className="mr-2 text-gray-400" />
                <span>Réunion</span>
              </button>
            </li>
            <li>
              <button className="w-full flex items-center p-2 rounded hover:bg-gray-600 text-left">
                <FaUserFriends className="mr-2 text-gray-400" />
                <span>Détente</span>
              </button>
            </li>
          </ul>
        </div>
      </div>
      
      {/* Zone principale de chat */}
      <div className="flex-1 flex flex-col bg-white">
        {/* En-tête du canal */}
        <div className="border-b p-4 flex items-center">
          <FaHashtag className="text-gray-500 mr-2" />
          <h2 className="font-bold">développement</h2>
          <span className="ml-2 text-gray-500 text-sm">Canal pour discuter du développement du projet</span>
          
          <div className="ml-auto flex space-x-3">
            <button className="text-gray-500 hover:text-gray-800">
              <FaUserFriends />
            </button>
            <button className="text-gray-500 hover:text-gray-800">
              <FaCog />
            </button>
          </div>
        </div>
        
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {dummyMessages.map((msg) => (
            <div key={msg.id} className="flex">
              <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center mr-3 font-bold text-blue-600">
                {msg.user.charAt(0)}
              </div>
              <div>
                <div className="flex items-baseline">
                  <span className="font-bold">{msg.user}</span>
                  <span className="ml-2 text-xs text-gray-500">{msg.time}</span>
                </div>
                <p className="text-gray-800">{msg.content}</p>
              </div>
            </div>
          ))}
        </div>
        
        {/* Zone de saisie */}
        <div className="p-4 border-t w-full">
          <div className="flex w-full items-center">
            <TextInput
              placeholder="Écrire un message..."
              type="text"
              className="flex-1 rounded-lg border-gray-300 focus:border-blue-500 focus:ring-blue-500 w-full"
              value={message}
              onChange={(e) => setMessage(e.target.value)}
            />
            <Button
              onClick={handleSendMessage}
              className="ml-2 bg-blue-600 hover:bg-blue-700 transition-colors"
            >
              <FaPaperPlane />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Chat;