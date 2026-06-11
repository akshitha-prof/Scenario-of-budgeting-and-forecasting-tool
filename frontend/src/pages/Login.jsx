import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../api.jsx";

export default function Login() {
  const { login } = useAuth();
  const nav = useNavigate();
  const [username, setUsername] = useState("analyst");
  const [password, setPassword] = useState("analyst");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e) {
    e.preventDefault();
    setError("");
    setBusy(true);
    try {
      await login(username, password);
      nav("/");
    } catch {
      setError("Invalid username or password.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="login-wrap">
      <div className="login-card">
        <div className="brand"><span className="dot" /> Scenario</div>
        <p className="muted">Financial planning &amp; what-if modelling.</p>
        <form onSubmit={submit}>
          <label className="field">Username
            <input value={username} onChange={(e) => setUsername(e.target.value)} autoFocus />
          </label>
          <label className="field">Password
            <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          </label>
          {error && <div className="error">{error}</div>}
          <button className="btn" disabled={busy}>{busy ? "Signing in…" : "Sign in"}</button>
        </form>
        <p className="hint">
          Demo logins:<br />
          <code>admin / admin</code> · <code>analyst / analyst</code> (editor) · <code>viewer / viewer</code>
        </p>
      </div>
    </div>
  );
}
