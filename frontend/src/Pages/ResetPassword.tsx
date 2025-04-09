import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Card, Button, TextInput } from 'flowbite-react';
import { FaEnvelope, FaArrowLeft } from 'react-icons/fa';
import bg from '/images/bg.webp';

const ResetPassword: React.FC = () => {
  const [email, setEmail] = useState<string>('');

  const handleResetPassword = () => {
    // Logique de réinitialisation du mot de passe ici
  };

  return (
    <div className="flex justify-center items-center min-h-screen bg-gray-50 bg-cover bg-no-repeat" style={{ backgroundImage: `url(${bg})` }}>
      <div className="w-full max-w-md px-4">
        <Card className="shadow-xl border-0 rounded-xl overflow-hidden">
          <div className="text-center mb-6">
            <h2 className="text-3xl font-bold text-gray-800">Mot de passe oublié</h2>
            <p className="text-gray-500 mt-2">Entrez votre email pour réinitialiser votre mot de passe</p>
          </div>
          
          <div className="space-y-5">
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
            
            <Button 
              onClick={handleResetPassword}
              className="w-full font-semibold py-3 rounded-lg bg-blue-600 hover:bg-blue-700 transition-colors"
            >
              Envoyer les instructions
            </Button>
            
            <Link 
              to="/" 
              className="flex items-center justify-center text-sm text-gray-600 mt-6 hover:text-blue-600 transition-colors"
            >
              <FaArrowLeft className="mr-2" />
              Retour à la connexion
            </Link>
          </div>
          
          <div className="mt-6 pt-4 border-t border-gray-200 text-center text-sm text-gray-500">
            <p>Vous n'avez pas reçu l'email ? Vérifiez votre dossier spam ou</p>
            <button className="text-blue-600 hover:underline font-medium">
              essayez avec une autre adresse
            </button>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default ResetPassword;