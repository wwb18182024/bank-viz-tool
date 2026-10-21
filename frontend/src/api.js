const BASE = '/api'

async function handle(resp) {
  if (!resp.ok) {
    let detail = resp.statusText
    try {
      const body = await resp.json()
      detail = body.detail || JSON.stringify(body)
    } catch { /* ignore */ }
    throw new Error(detail)
  }
  return resp.json()
}

export const api = {
  health: () => fetch(`${BASE}/health`).then(handle),

  upload: async (file) => {
    const form = new FormData()
    form.append('file', file)
    return fetch(`${BASE}/datasets/upload`, { method: 'POST', body: form }).then(handle)
  },

  metadata: (datasetId) => fetch(`${BASE}/datasets/${datasetId}/metadata`).then(handle),

  remove: (datasetId) => fetch(`${BASE}/datasets/${datasetId}`, { method: 'DELETE' }).then(handle),

  autoPlan: (datasetId) => fetch(`${BASE}/autoviz/${datasetId}/plan`, { method: 'POST' }).then(handle),

  autoExecute: (datasetId, plan) =>
    fetch(`${BASE}/autoviz/${datasetId}/execute`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ charts: plan }),
    }).then(handle),

  manualOptions: (datasetId) => fetch(`${BASE}/manual/${datasetId}/options`).then(handle),

  manualChart: (datasetId, spec) =>
    fetch(`${BASE}/manual/${datasetId}/chart`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(spec),
    }).then(handle),
}
