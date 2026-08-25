import { useEffect, useState } from "react";
import * as api from "./api";
import PageCanvas from "./components/PageCanvas.jsx";

export default function App() {
  const [docs, setDocs] = useState([]);
  const [doc, setDoc] = useState(null);       // full document detail
  const [pageIndex, setPageIndex] = useState(0);
  const [mode, setMode] = useState("capture"); // capture | ignore | select
  const [zoom, setZoom] = useState(1);
  const [selectedId, setSelectedId] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  // Load the list of documents once, and open the newest if there is one.
  useEffect(() => {
    api.listDocuments().then((list) => {
      setDocs(list);
      if (list.length) openDoc(list[0].id);
    }).catch((e) => setError(String(e)));
  }, []);

  async function openDoc(id) {
    const d = await api.getDocument(id);
    setDoc(d);
    setPageIndex(0);
    setSelectedId(null);
  }

  async function refreshDoc() {
    if (!doc) return;
    const d = await api.getDocument(doc.id);
    setDoc(d);
  }

  async function onUpload(e) {
    const file = e.target.files[0];
    if (!file) return;
    setBusy(true);
    setError("");
    try {
      const d = await api.uploadDocument(file);
      setDocs((prev) => [d, ...prev]);
      setDoc(d);
      setPageIndex(0);
      setSelectedId(null);
    } catch (err) {
      setError(String(err));
    } finally {
      setBusy(false);
      e.target.value = "";
    }
  }

  const pageNumber = pageIndex + 1;
  const pageAnnotations = doc
    ? doc.annotations.filter((a) => a.page === pageNumber)
    : [];

  async function handleCreate(rect) {
    await api.createAnnotation({ document: doc.id, page: pageNumber, ...rect });
    await refreshDoc();
  }

  async function handleDelete(id) {
    await api.deleteAnnotation(id);
    if (selectedId === id) setSelectedId(null);
    await refreshDoc();
  }

  async function handleOcr(id) {
    setBusy(true);
    try {
      await api.ocrAnnotation(id);
      await refreshDoc();
    } catch (err) {
      setError(String(err));
    } finally {
      setBusy(false);
    }
  }

  async function handleOcrAllOnPage() {
    const greens = pageAnnotations.filter((a) => a.kind === "capture");
    setBusy(true);
    try {
      for (const a of greens) {
        await api.ocrAnnotation(a.id);
      }
      await refreshDoc();
    } catch (err) {
      setError(String(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">Drawing Annotator</div>

        <label className="btn file-btn">
          {busy ? "Working..." : "Import PDF"}
          <input type="file" accept="application/pdf" onChange={onUpload} hidden />
        </label>

        {docs.length > 1 && (
          <select
            value={doc ? doc.id : ""}
            onChange={(e) => openDoc(Number(e.target.value))}
          >
            {docs.map((d) => (
              <option key={d.id} value={d.id}>{d.name}</option>
            ))}
          </select>
        )}

        {doc && (
          <>
            <div className="pager">
              <button className="btn" disabled={pageIndex === 0}
                onClick={() => { setPageIndex((i) => i - 1); setSelectedId(null); }}>
                Prev
              </button>
              <span className="page-label">Page {pageNumber} / {doc.num_pages}</span>
              <button className="btn" disabled={pageIndex >= doc.num_pages - 1}
                onClick={() => { setPageIndex((i) => i + 1); setSelectedId(null); }}>
                Next
              </button>
            </div>

            <div className="modes">
              <button className={"btn mode capture" + (mode === "capture" ? " on" : "")}
                onClick={() => setMode("capture")}>Capture (green)</button>
              <button className={"btn mode ignore" + (mode === "ignore" ? " on" : "")}
                onClick={() => setMode("ignore")}>Ignore (red)</button>
              <button className={"btn mode" + (mode === "select" ? " on" : "")}
                onClick={() => setMode("select")}>Select</button>
            </div>

            <div className="zoom">
              <button className="btn" onClick={() => setZoom((z) => Math.max(0.25, z - 0.25))}>-</button>
              <span className="page-label">{Math.round(zoom * 100)}%</span>
              <button className="btn" onClick={() => setZoom((z) => Math.min(4, z + 0.25))}>+</button>
              <button className="btn" onClick={() => setZoom(1)}>Reset</button>
            </div>
          </>
        )}
      </header>

      {error && <div className="error">{error}</div>}

      {!doc && !error && (
        <div className="empty">Import a PDF to begin.</div>
      )}

      {doc && (
        <div className="main">
          <PageCanvas
            imageUrl={doc.pages[pageIndex]}
            annotations={pageAnnotations}
            mode={mode}
            zoom={zoom}
            selectedId={selectedId}
            onCreate={handleCreate}
            onSelect={(id) => setSelectedId(id)}
          />

          <aside className="sidebar">
            <div className="sidebar-head">
              <span>Annotations on page {pageNumber}</span>
              <button className="btn small" disabled={busy}
                onClick={handleOcrAllOnPage}>OCR all green</button>
            </div>

            {pageAnnotations.length === 0 && (
              <div className="hint">Draw a box on the page. Green captures text, red marks content to ignore.</div>
            )}

            <ul className="ann-list">
              {pageAnnotations.map((a) => (
                <li key={a.id}
                    className={"ann" + (a.id === selectedId ? " sel" : "")}
                    onClick={() => setSelectedId(a.id)}>
                  <div className="ann-row">
                    <span className={"dot " + a.kind} />
                    <span className="ann-kind">{a.kind === "capture" ? "Capture" : "Ignore"}</span>
                    <span className="spacer" />
                    {a.kind === "capture" && (
                      <button className="btn small" disabled={busy}
                        onClick={(e) => { e.stopPropagation(); handleOcr(a.id); }}>OCR</button>
                    )}
                    <button className="btn small danger"
                      onClick={(e) => { e.stopPropagation(); handleDelete(a.id); }}>Delete</button>
                  </div>
                  {a.kind === "capture" && (
                    <div className="ann-text">
                      {a.text ? a.text : <span className="muted">no text yet</span>}
                    </div>
                  )}
                </li>
              ))}
            </ul>
          </aside>
        </div>
      )}
    </div>
  );
}
