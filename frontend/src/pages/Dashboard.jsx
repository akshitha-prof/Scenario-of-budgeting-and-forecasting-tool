import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from "recharts";
import { api, fmt, fmtPct } from "../api.jsx";

const GROUPS = ["department", "category", "region"];

export default function Dashboard() {
  const [budget, setBudget] = useState(null);
  const [rows, setRows] = useState([]);
  const [groupBy, setGroupBy] = useState("department");
  const [error, setError] = useState("");

  useEffect(() => {
    api.get("/api/budgets")
      .then(({ data }) => setBudget(data[0] || null))
      .catch(() => setError("Could not load budgets. Is the API running and seeded?"));
  }, []);

  useEffect(() => {
    if (!budget) return;
    api.get(`/api/budgets/${budget.id}/variance`, { params: { group_by: groupBy } })
      .then(({ data }) => setRows(data))
      .catch(() => setError("Could not load variance."));
  }, [budget, groupBy]);

  const totalPlanned = rows.reduce((s, r) => s + r.planned, 0);
  const totalActual = rows.reduce((s, r) => s + r.actual, 0);
  const totalVar = totalActual - totalPlanned;
  const varPct = totalPlanned ? (totalVar / totalPlanned) * 100 : 0;

  return (
    <>
      <div className="page-head">
        <div>
          <h1>Budget vs Actuals</h1>
          <div className="sub">{budget ? `${budget.name} · FY${budget.fiscal_year}` : "Loading…"}</div>
        </div>
        <label className="field">Group by
          <select value={groupBy} onChange={(e) => setGroupBy(e.target.value)}>
            {GROUPS.map((g) => <option key={g} value={g}>{g}</option>)}
          </select>
        </label>
      </div>

      {error && <div className="panel error">{error}</div>}

      <div className="stat-row">
        <div className="stat"><div className="label">Planned</div><div className="value">${fmt(totalPlanned)}</div></div>
        <div className="stat"><div className="label">Actual</div><div className="value">${fmt(totalActual)}</div></div>
        <div className="stat">
          <div className="label">Variance</div>
          <div className={`value ${totalVar > 0 ? "neg" : "pos"}`}>${fmt(Math.abs(totalVar))}</div>
        </div>
        <div className="stat">
          <div className="label">Variance %</div>
          <div className={`value ${totalVar > 0 ? "neg" : "pos"}`}>{fmtPct(varPct)}</div>
        </div>
      </div>

      <div className="panel">
        <h3>Planned vs actual by {groupBy}</h3>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={rows} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#eef1f6" vertical={false} />
            <XAxis dataKey="dimension" tick={{ fontSize: 12, fill: "#5b6883" }} />
            <YAxis tickFormatter={(v) => `$${fmt(v / 1000)}k`} tick={{ fontSize: 12, fill: "#5b6883" }} />
            <Tooltip formatter={(v) => `$${fmt(v)}`} />
            <Legend />
            <Bar dataKey="planned" name="Planned" fill="#9fb3d1" radius={[3, 3, 0, 0]} />
            <Bar dataKey="actual" name="Actual" fill="#1d7a72" radius={[3, 3, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </div>

      <div className="panel">
        <h3>Detail</h3>
        <table>
          <thead>
            <tr>
              <th>{groupBy}</th>
              <th className="num">Planned</th>
              <th className="num">Actual</th>
              <th className="num">Variance</th>
              <th className="num">Var %</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.dimension}>
                <td>{r.dimension}</td>
                <td className="num">${fmt(r.planned)}</td>
                <td className="num">${fmt(r.actual)}</td>
                <td className={`num ${r.variance > 0 ? "delta-neg" : "delta-pos"}`}>${fmt(r.variance)}</td>
                <td className={`num ${r.variance > 0 ? "delta-neg" : "delta-pos"}`}>{fmtPct(r.variance_pct)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </>
  );
}
