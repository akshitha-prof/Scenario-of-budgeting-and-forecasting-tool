import { useEffect, useState } from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend } from "recharts";
import { api, fmt, canEdit, useAuth } from "../api.jsx";

const FIELDS = ["category", "department", "region"];

export default function Scenarios() {
  const { role } = useAuth();
  const editable = canEdit(role);
  const [budget, setBudget] = useState(null);
  const [scenarios, setScenarios] = useState([]);
  const [selected, setSelected] = useState(null);
  const [compare, setCompare] = useState(null);
  const [groupBy, setGroupBy] = useState("category");
  const [newName, setNewName] = useState("");
  const [lever, setLever] = useState({ target_field: "category", target_value: "*", adjustment_type: "percent", adjustment_value: -10 });
  const [msg, setMsg] = useState("");

  useEffect(() => {
    api.get("/api/budgets").then(({ data }) => setBudget(data[0] || null));
  }, []);

  function loadScenarios(bid, keep) {
    api.get(`/api/budgets/${bid}/scenarios`).then(({ data }) => {
      setScenarios(data);
      setSelected((cur) => keep ?? cur ?? data[0] ?? null);
    });
  }
  useEffect(() => { if (budget) loadScenarios(budget.id); }, [budget]);

  useEffect(() => {
    if (!selected) { setCompare(null); return; }
    api.get(`/api/scenarios/${selected.id}/compare`, { params: { group_by: groupBy } })
      .then(({ data }) => setCompare(data));
  }, [selected, groupBy]);

  async function createScenario() {
    if (!newName.trim()) return;
    const { data } = await api.post(`/api/budgets/${budget.id}/scenarios`, { name: newName.trim() });
    setNewName("");
    loadScenarios(budget.id, data);
  }

  async function addLever() {
    setMsg("");
    await api.post(`/api/scenarios/${selected.id}/levers`, lever);
    setMsg("Lever applied.");
    // refresh compare + scenario lever list
    const { data } = await api.get(`/api/scenarios/${selected.id}/compare`, { params: { group_by: groupBy } });
    setCompare(data);
    loadScenarios(budget.id, scenarios.find((s) => s.id === selected.id));
    api.get(`/api/budgets/${budget.id}/scenarios`).then(({ data }) =>
      setSelected(data.find((s) => s.id === selected.id) || selected));
  }

  return (
    <>
      <div className="page-head">
        <div>
          <h1>What-if Scenarios</h1>
          <div className="sub">Layer adjustments on the base budget and compare outcomes.</div>
        </div>
        <label className="field">Group by
          <select value={groupBy} onChange={(e) => setGroupBy(e.target.value)}>
            {FIELDS.map((g) => <option key={g} value={g}>{g}</option>)}
          </select>
        </label>
      </div>

      <div className="panel">
        <h3>Scenarios</h3>
        <div className="toolbar">
          {scenarios.map((s) => (
            <button key={s.id}
              className={`btn ${selected?.id === s.id ? "" : "ghost"}`}
              onClick={() => setSelected(s)}>
              {s.name} <span className="chip">{s.levers.length} levers</span>
            </button>
          ))}
          {scenarios.length === 0 && <span className="muted">No scenarios yet.</span>}
        </div>
        {editable && (
          <div className="toolbar">
            <input placeholder="New scenario name" value={newName} onChange={(e) => setNewName(e.target.value)} />
            <button className="btn" onClick={createScenario}>Create scenario</button>
          </div>
        )}
      </div>

      {selected && (
        <>
          {editable && (
            <div className="panel">
              <h3>Add a lever to “{selected.name}”</h3>
              <div className="toolbar">
                <label className="field">Field
                  <select value={lever.target_field}
                    onChange={(e) => setLever({ ...lever, target_field: e.target.value })}>
                    {FIELDS.map((f) => <option key={f}>{f}</option>)}
                  </select>
                </label>
                <label className="field">Value (* = all)
                  <input value={lever.target_value}
                    onChange={(e) => setLever({ ...lever, target_value: e.target.value })} />
                </label>
                <label className="field">Type
                  <select value={lever.adjustment_type}
                    onChange={(e) => setLever({ ...lever, adjustment_type: e.target.value })}>
                    <option value="percent">percent</option>
                    <option value="absolute">absolute</option>
                  </select>
                </label>
                <label className="field">Amount
                  <input type="number" value={lever.adjustment_value}
                    onChange={(e) => setLever({ ...lever, adjustment_value: Number(e.target.value) })} />
                </label>
                <button className="btn" onClick={addLever} style={{ alignSelf: "flex-end" }}>Apply lever</button>
              </div>
              {msg && <span className="muted">{msg}</span>}
              <p className="muted" style={{ marginTop: 8 }}>
                e.g. field <code>category</code>, value <code>Cloud</code>, <code>percent</code> <code>+15</code>
                → raise all cloud spend by 15%.
              </p>
            </div>
          )}

          {compare && (
            <>
              <div className="stat-row">
                <div className="stat"><div className="label">Base total</div><div className="value">${fmt(compare.base_total)}</div></div>
                <div className="stat"><div className="label">Scenario total</div><div className="value">${fmt(compare.scenario_total)}</div></div>
                <div className="stat">
                  <div className="label">Delta</div>
                  <div className={`value ${compare.scenario_total - compare.base_total > 0 ? "neg" : "pos"}`}>
                    ${fmt(Math.abs(compare.scenario_total - compare.base_total))}
                  </div>
                </div>
              </div>

              <div className="panel">
                <h3>Base vs scenario by {groupBy}</h3>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={compare.rows} margin={{ top: 8, right: 8, left: 8, bottom: 0 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#eef1f6" vertical={false} />
                    <XAxis dataKey="dimension" tick={{ fontSize: 12, fill: "#5b6883" }} />
                    <YAxis tickFormatter={(v) => `$${fmt(v / 1000)}k`} tick={{ fontSize: 12, fill: "#5b6883" }} />
                    <Tooltip formatter={(v) => `$${fmt(v)}`} />
                    <Legend />
                    <Bar dataKey="base" name="Base" fill="#9fb3d1" radius={[3, 3, 0, 0]} />
                    <Bar dataKey="scenario" name="Scenario" fill="#1d7a72" radius={[3, 3, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </>
          )}
        </>
      )}
    </>
  );
}
