import { useRef, useState } from "react";

// Turn two corner points (each normalized 0..1) into a normalized rect.
function toRect(a, b) {
  return {
    x: Math.min(a.x, b.x),
    y: Math.min(a.y, b.y),
    w: Math.abs(a.x - b.x),
    h: Math.abs(a.y - b.y),
  };
}

const COLORS = {
  capture: { stroke: "#12a150", fill: "rgba(18,161,80,0.15)" },
  ignore: { stroke: "#d0342c", fill: "rgba(208,52,44,0.15)" },
};

export default function PageCanvas({ imageUrl, annotations, mode, zoom, selectedId, onCreate, onSelect }) {
  const svgRef = useRef(null);
  const [nat, setNat] = useState(null); // natural image size in px
  const [draft, setDraft] = useState(null);
  const startRef = useRef(null);

  const drawing = mode !== "select";

  // Normalized pointer position relative to the drawing surface.
  function pointFromEvent(e) {
    const box = svgRef.current.getBoundingClientRect();
    return {
      x: Math.min(1, Math.max(0, (e.clientX - box.left) / box.width)),
      y: Math.min(1, Math.max(0, (e.clientY - box.top) / box.height)),
    };
  }

  function onDown(e) {
    if (!drawing) return;
    startRef.current = pointFromEvent(e);
    setDraft(toRect(startRef.current, startRef.current));
  }
  function onMove(e) {
    if (!drawing || !startRef.current) return;
    setDraft(toRect(startRef.current, pointFromEvent(e)));
  }
  function onUp() {
    if (!drawing || !startRef.current) return;
    const r = draft;
    startRef.current = null;
    setDraft(null);
    // Ignore accidental tiny drags.
    if (r && r.w > 0.005 && r.h > 0.005) {
      onCreate({ kind: mode, ...r });
    }
  }

  const displayW = nat ? nat.w * zoom : undefined;

  return (
    <div className="canvas-scroll">
      <div className="canvas-fit">
      <div className="page-stage" style={{ width: displayW }}>
        <img
          src={imageUrl}
          alt="drawing page"
          draggable={false}
          onLoad={(e) => setNat({ w: e.target.naturalWidth, h: e.target.naturalHeight })}
          style={{ width: displayW }}
        />
        <svg
          ref={svgRef}
          className="overlay"
          viewBox="0 0 100 100"
          preserveAspectRatio="none"
          style={{ cursor: drawing ? "crosshair" : "default" }}
          onMouseDown={onDown}
          onMouseMove={onMove}
          onMouseUp={onUp}
          onMouseLeave={onUp}
        >
          {annotations.map((a) => {
            const c = COLORS[a.kind];
            const isSel = a.id === selectedId;
            return (
              <rect
                key={a.id}
                x={a.x * 100}
                y={a.y * 100}
                width={a.w * 100}
                height={a.h * 100}
                fill={c.fill}
                stroke={c.stroke}
                strokeWidth={isSel ? 2.5 : 1.5}
                strokeDasharray={isSel ? "3 2" : undefined}
                vectorEffect="non-scaling-stroke"
                style={{ cursor: drawing ? "crosshair" : "pointer" }}
                onMouseDown={(e) => {
                  if (!drawing) {
                    e.stopPropagation();
                    onSelect(a.id);
                  }
                }}
              />
            );
          })}
          {draft && (
            <rect
              x={draft.x * 100}
              y={draft.y * 100}
              width={draft.w * 100}
              height={draft.h * 100}
              fill={COLORS[mode].fill}
              stroke={COLORS[mode].stroke}
              strokeWidth={1.5}
              strokeDasharray="4 2"
              vectorEffect="non-scaling-stroke"
            />
          )}
        </svg>
      </div>
      </div>
    </div>
  );
}
