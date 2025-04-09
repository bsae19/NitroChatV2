import React, { useState } from 'react';
import { Card, Button, TextInput } from 'flowbite-react';
import { FaUser, FaEnvelope, FaLock, FaCamera } from 'react-icons/fa';
import bg from '/images/bg.webp';
import avatar from '/images/avatar.png';
import { useNavigate } from 'react-router-dom';

const ProfilePage: React.FC = () => {
  const [username, setUsername] = useState<string>("johndoe");
  const [email, setEmail] = useState<string>("johndoe@example.com");
  const [password, setPassword] = useState<string>("");
  let navigate = useNavigate();
  
  const handleSaveChanges = () => {
    // Logique pour sauvegarder les modifications du profil
  };

  return (
    <div className="flex justify-center items-center min-h-screen bg-gray-50 py-8 bg-cover bg-no-repeat" style={{ backgroundImage: `url(${bg})` }}>
      <div className="w-full max-w-md px-4">
        <Card className="shadow-xl border-0 rounded-xl overflow-hidden">
          {/* En-tête de profil */}
          <div className="text-center mb-6">
            <div className="relative mx-auto w-24 h-24 mb-4">
              <div className="w-24 h-24 rounded-full border-4 border-white bg-gray-200 flex items-center justify-center overflow-hidden shadow-md">
                <img src={avatar} alt="Avatar" className="w-full h-full object-cover" />
              </div>
              <button className="absolute bottom-0 right-0 bg-blue-600 text-white p-2 rounded-full hover:bg-blue-700 transition-colors shadow-md" style={{ width: '32px', height: '32px' }}>
                <FaCamera size={16} />
              </button>
            </div>
            <h2 className="text-2xl font-bold text-gray-800">John Doe</h2>
            <p className="text-sm text-gray-500">Membre depuis Avril 2023</p>
          </div>
          
          <div className="space-y-4">
            <h3 className="text-lg font-semibold mb-2 text-gray-700">
              Informations personnelles
            </h3>
            
            <div className="relative">
              <TextInput
                placeholder="Nom d'utilisateur"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="rounded-lg"
                icon={FaUser}
              />
            </div>
            
            <div className="relative">
              <TextInput
                placeholder="Adresse e-mail"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="rounded-lg"
                icon={FaEnvelope}
              />
            </div>
            
            <div className="relative">
              <TextInput
                placeholder="Nouveau mot de passe"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="rounded-lg"
                icon={FaLock}
              />
              <p className="text-xs text-gray-500 mt-1 ml-1">
                Laissez vide si vous ne souhaitez pas modifier votre mot de passe
              </p>
            </div>
            
            <div className="mt-6 pt-4 border-t border-gray-200">
              <div className="flex justify-end space-x-3">
                <Button
                  color="light"
                  className="border border-gray-300 hover:bg-gray-100 transition-colors"
                  onClick={() => {navigate("/chat")}}>
                  Annuler
                </Button>
                
                <Button
                  onClick={handleSaveChanges}
                  className="bg-blue-600 hover:bg-blue-700 transition-colors"
                >
                  Enregistrer
                </Button>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default ProfilePage;