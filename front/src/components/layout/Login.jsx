import { useState } from "react";
import Forum from "./Forum";

export default function Login() {
  const [username, setUsername] = useState("");
  const [submitted, setSubmitted] = useState(false);

  return (
    <>
      {!submitted ? (
        <div className="p-4 max-w-lg mx-auto">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            setSubmitted(true);
          }}
          className="mb-4"
        >
          <input
            className="border p-2 w-full mb-2"
            placeholder="Entrez votre prénom"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
          />
          <button className="bg-indigo-500 text-white p-2 w-full" type="submit">
            Accéder au forum
          </button>
        </form>
        </div>
      ) : (
        <Forum username={username} />
      )}
    </>
  );
}