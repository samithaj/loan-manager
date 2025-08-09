"use client";
import { useEffect, useState } from "react";

export default function AuthForm() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    setUsername(localStorage.getItem("u") || "");
    setPassword(localStorage.getItem("p") || "");
  }, []);

  return (
    <form
      className="flex flex-col gap-2 max-w-sm"
      onSubmit={(e) => {
        e.preventDefault();
        localStorage.setItem("u", username);
        localStorage.setItem("p", password);
        setSaved(true);
        setTimeout(() => setSaved(false), 1500);
        // Hint other components to re-check auth
        window.dispatchEvent(new Event('auth:updated'));
      }}
    >
      <label className="text-sm">Username</label>
      <input className="border rounded px-2 py-1" value={username} onChange={(e) => setUsername(e.target.value)} />
      <label className="text-sm">Password</label>
      <input className="border rounded px-2 py-1" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
      <button className="mt-2 bg-black text-white rounded px-3 py-1" type="submit">Save</button>
      {saved && <div className="text-xs text-green-600">Saved</div>}
    </form>
  );
}


