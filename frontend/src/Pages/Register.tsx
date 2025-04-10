import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Card, Button, TextInput } from 'flowbite-react';
import { FaUser, FaEnvelope, FaLock, FaGoogle, FaFacebook } from 'react-icons/fa';
import bg from '/images/bg.webp';

const Register: React.FC = () => {
  const [username, setUsername] = useState<string>('');
  const [email, setEmail] = useState<string>('');
  const [password, setPassword] = useState<string>('');

  const handleRegister = () => {
    // Logique d'inscription ici
  };

  return (
    <div className="flex justify-center items-center min-h-screen bg-gray-50 bg-cover bg-no-repeat" style={{ backgroundImage: `url(${bg})` }}>
      <div className="w-full max-w-md px-4">
        <Card className="shadow-xl border-0 rounded-xl overflow-hidden">
          <div className="text-center mb-6">
            <h2 className="text-3xl font-bold text-gray-800">Créer un compte</h2>
            <p className="text-gray-500 mt-2">Rejoignez-nous en quelques étapes simples</p>
          </div>
          
          <div className="space-y-5">
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
                placeholder="Mot de passe"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="rounded-lg"
                icon={FaLock}
              />
              <p className="text-xs text-gray-500 mt-1 ml-1">
                Minimum 8 caractères, avec une majuscule et un chiffre
              </p>
            </div>
            
            <div className="flex items-center">
              <input
                id="terms"
                type="checkbox"
                className="w-4 h-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
              />
              <label htmlFor="terms" className="ml-2 text-sm text-gray-600">
                J'accepte les <a href="#" className="text-blue-600 hover:underline">conditions d'utilisation</a> et la <a href="#" className="text-blue-600 hover:underline">politique de confidentialité</a>
              </label>
            </div>
            
            <Button 
              onClick={handleRegister}
              className="w-full font-semibold py-3 rounded-lg bg-blue-600 hover:bg-blue-700 transition-colors"
            >
              Créer mon compte
            </Button>
            
            
            <div className="text-center text-sm text-gray-600 mt-4">
              <span>Déjà inscrit ? </span>
              <Link to="/auth" className="text-blue-600 font-medium hover:underline">
                Connectez-vous
              </Link>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default Register;