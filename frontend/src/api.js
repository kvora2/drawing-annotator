// Single place that knows where the backend lives.
const BASE = "http://localhost:8000/api";

async function json(res) {
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`${res.status}: ${body}`);
  }
  return res.json();
}

export function listDocuments() {
  return fetch(`${BASE}/documents/`).then(json);
}

export function getDocument(id) {
  return fetch(`${BASE}/documents/${id}/`).then(json);
}

export function uploadDocument(file) {
  const form = new FormData();
  form.append("file", file);
  return fetch(`${BASE}/documents/`, { method: "POST", body: form }).then(json);
}

export function createAnnotation(payload) {
  return fetch(`${BASE}/annotations/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  }).then(json);
}

export function deleteAnnotation(id) {
  return fetch(`${BASE}/annotations/${id}/`, { method: "DELETE" });
}

export function ocrAnnotation(id) {
  return fetch(`${BASE}/annotations/${id}/ocr/`, { method: "POST" }).then(json);
}
