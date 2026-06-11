import { Routes, Route, Navigate, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "./api.jsx";
import Login from "./pages/Login.jsx";
import Dashboard from "./pages/Dashboard.jsx";
import Scenarios from "./pages/Scenarios.jsx";

function Shell({ children }) {
  const { role, logout } = useAuth();
  const nav = useNavigate();
  return (
    <div className="shell">
      <aside className="sidebar">
        <div className="brand"><span className="dot" /> Scenario</div>
        <NavLink to="/" end className="nav-link">Budget vs Actuals</NavLink>
        <NavLink to="/scenarios" className="nav-link">What-if Scenarios</NavLink>
        <div className="sidebar-foot">
          Signed in as <strong>{role}</strong>
          <br />
          <button onClick={() => { logout(); nav("/login"); }}>Sign out</button>
        </div>
      </aside>
      <main className="main">{children}</main>
    </div>
  );
}

function Protected({ children }) {
  const { token } = useAuth();
  return token ? <Shell>{children}</Shell> : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/" element={<Protected><Dashboard /></Protected>} />
      <Route path="/scenarios" element={<Protected><Scenarios /></Protected>} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
