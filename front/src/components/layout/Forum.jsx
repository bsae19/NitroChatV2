import { useState, useEffect } from "react";
import Button from "../ui/Button";
import Message from "../chat/Message";

const Forum = ({username}) => {
    const [posts, setPosts] = useState([]);
    const [content, setContent] = useState("");

    useEffect(() => {
      fetch("http://localhost:5000/api/messages/0")
        .then((res) => res.json())
        .then((data) => setPosts(data));
    }, []);
  
    const handleSubmit = (e) => {
      e.preventDefault();
      fetch("http://localhost:5000/api/messages", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: username, message: content }),
      })
        .then((res) => res.json())
        .then((newPost) => setPosts([...posts, newPost]));
      setContent("");
    };
  
    return (
    <div className="flex h-screen overflow-hidden">
      <div className="flex-1">
        <header className="bg-white p-4 border-b border-gray-300">
            <div className="flex items-center">
                <div className="ml-3">
                <h1 className="text-xl font-semibold">Erwan</h1>
                </div>
            </div>
        </header>
        <div className="h-screen overflow-y-auto p-4 pb-36 bg-gray-200">
            {posts.map((message) => (
                <Message 
                key={message.id} 
                message={{
                    ...message,
                    sender: message.user_id === username ? 'me' : username
                }} 
                />
            ))}
        </div>
        <footer className="bg-white border-t border-gray-300 p-4 absolute bottom-0 w-full">
            <form onSubmit={handleSubmit} className="flex items-center">
                <input
                type="text"
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Ecrivez votre message..."
                className="w-full p-2 rounded-md border border-gray-400 focus:outline-none focus:border-blue-500"
                />
                <Button type="submit" className="ml-2 cursor-pointer">Envoyer</Button>
            </form>
        </footer>
      </div>
    </div>
    );
  }

export default Forum;