import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Card, Button, TextInput } from 'flowbite-react';
import { FaEnvelope, FaLock } from 'react-icons/fa';
import bg from '/images/bg.webp';

const Auth = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  let navigate = useNavigate();
  const handleLogin = () => {
    navigate("/chat");
  };

  return (
    <div className="flex justify-center items-center min-h-screen bg-gray-50 bg-cover bg-no-repeat" style={{ backgroundImage: `url(${bg})` }}>
      <div className="w-full max-w-md px-4">
        <Card className="shadow-xl border-0 rounded-xl overflow-hidden">
          <div className="text-center mb-6">
            <h2 className="text-3xl font-bold text-gray-800">Bienvenue</h2>
            <p className="text-gray-500 mt-2">Connectez-vous à votre compte</p>
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
            
            <div className="relative">
              <TextInput
                placeholder="Mot de passe"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="rounded-lg"
                icon={FaLock}
              />
            </div>
            
            <Button 
              onClick={handleLogin}
              className="w-full font-semibold py-3 rounded-lg bg-blue-600 hover:bg-blue-700 transition-colors"
            >
              Se connecter
            </Button>
            
            <div className="flex justify-between text-sm mt-6 text-gray-600">
              <Link to="/reset-password" className="hover:text-blue-600 transition-colors">
                Mot de passe oublié?
              </Link>
              <Link to="/register" className="font-medium hover:text-blue-600 transition-colors">
                Créer un compte
              </Link>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default Auth;