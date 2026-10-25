const API_BASE = '/api/v1';

export async function fetchHealth() {
  const res = await fetch(`${API_BASE}/health`);
  if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`);
  return res.json();
}

export async function fetchConnections() {
  const res = await fetch(`${API_BASE}/connections`);
  if (!res.ok) throw new Error(`Failed to load connections: ${res.statusText}`);
  return res.json();
}

export async function testConnection(connectorId) {
  const res = await fetch(`${API_BASE}/connections/test`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ connector_id: connectorId }),
  });
  if (!res.ok) throw new Error(`Test failed: ${res.statusText}`);
  return res.json();
}

export async function fetchSchema(connectorId) {
  const res = await fetch(`${API_BASE}/connections/${connectorId}/schema`);
  const data = await res.json();
  if (!res.ok) throw new Error(data.detail || `Failed to load schema: ${res.statusText}`);
  return data;
}

export async function executeQuery(prompt, connectorId) {
  const res = await fetch(`${API_BASE}/query`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt, connector_id: connectorId }),
  });
  const data = await res.json();
  if (!res.ok) {
    throw new Error(data.detail || 'Execution failed.');
  }
  return data;
}
