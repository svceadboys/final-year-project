/**
 * api.js – Centralised API client for Smart Waste Management frontend
 */

const BASE_URL = "";

async function apiFetch(path, options = {}) {
  const token = localStorage.getItem("admin_token");
  const headers = { "Accept": "application/json", ...options.headers };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const resp = await fetch(`${BASE_URL}${path}`, {
    ...options,
    headers,
  });

  if (resp.status === 401) {
    if (window.logout) window.logout();
    await new Promise(() => { }); // Freeze execution to prevent flashing errors before redirect completes
  }

  if (!resp.ok) {
    const err = await resp.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${resp.status}`);
  }
  return resp.json();
}

// ── Dashboard ──────────────────────────────────────────────────────────────
const api = {
  getDashboardSummary: () => apiFetch("/api/dashboard/summary"),

  // Bins
  getBins: () => apiFetch("/api/bins/"),
  getBin: (id) => apiFetch(`/api/bins/${id}`),
  createBin: (data) => apiFetch("/api/bins/", { method: "POST", body: JSON.stringify(data), headers: { "Content-Type": "application/json" } }),

  // Classification
  classifyImage: (binId, file) => {
    const form = new FormData();
    form.append("file", file);
    return apiFetch(`/api/classification/predict?bin_id=${binId}`, { method: "POST", body: form });
  },
  classifyBatch: (binId, files) => {
    const form = new FormData();
    for (const f of files) form.append("files", f);
    return apiFetch(`/api/classification/predict/batch?bin_id=${binId}`, { method: "POST", body: form });
  },
  getClassificationHistory: (binId) => apiFetch(`/api/classification/history/${binId}`),

  // Records
  getRecords: (wasteType = null, limit = 100, offset = 0) => {
    const params = new URLSearchParams({ limit, offset });
    if (wasteType) params.set("waste_type", wasteType);
    return apiFetch(`/api/records/?${params}`);
  },
  getRecordStats: () => apiFetch("/api/records/stats"),
  downloadCSV: async () => {
    const token = localStorage.getItem("admin_token");
    const headers = {};
    if (token) headers["Authorization"] = `Bearer ${token}`;

    const resp = await fetch(`${BASE_URL}/api/records/download`, { headers });
    if (!resp.ok) throw new Error("Download failed");

    const blob = await resp.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    // The backend provides the filename in Content-Disposition if we want to parse it, 
    // but a client-side generic name works just as well.
    a.download = `waste_report_${new Date().toISOString().slice(0, 10)}.csv`;
    document.body.appendChild(a);
    a.click();
    a.remove();
    window.URL.revokeObjectURL(url);
  },

  // Forecast
  runForecast: (binId) => apiFetch(`/api/forecast/run/${binId}`, { method: "POST" }),
  getForecast: (binId) => apiFetch(`/api/forecast/${binId}`),

  // Scheduler
  generateSchedule: (truckId, distMatrix, depotBinId = null) =>
    apiFetch("/api/scheduler/generate", {
      method: "POST",
      body: JSON.stringify({ truck_id: truckId, distance_matrix: distMatrix, depot_bin_id: depotBinId }),
      headers: { "Content-Type": "application/json" },
    }),
  getTodaySchedule: (truckId) => apiFetch(`/api/scheduler/today/${truckId}`),

  // Fleet Management
  getFleetStatus: () => apiFetch("/api/fleet/trucks"),
  dispatchFleet: () => apiFetch("/api/fleet/dispatch", { method: "POST" }),
  completeCollection: (truckId) => apiFetch(`/api/fleet/${truckId}/complete`, { method: "POST" }),
};

// ── Toast notifications ────────────────────────────────────────────────────
function showToast(message, type = "success") {
  let toast = document.getElementById("toast");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "toast";
    toast.className = "toast";
    document.body.appendChild(toast);
  }
  toast.className = `toast ${type}`;
  toast.innerHTML = `<span>${type === "success" ? "✓" : "✕"}</span> ${message}`;
  toast.classList.add("show");
  setTimeout(() => toast.classList.remove("show"), 3500);
}

// ── Badge helper ───────────────────────────────────────────────────────────
function wasteBadge(type) {
  const colors = {
    cardboard: { bg: "rgba(234,179,8,0.15)", fg: "#eab308" },
    glass: { bg: "rgba(59,130,246,0.15)", fg: "#3b82f6" },
    metal: { bg: "rgba(107,114,128,0.15)", fg: "#9ca3af" },
    paper: { bg: "rgba(16,185,129,0.15)", fg: "#10b981" },
    plastic: { bg: "rgba(168,85,247,0.15)", fg: "#a855f7" },
    trash: { bg: "rgba(239,68,68,0.15)", fg: "#ef4444" },
    Organic: { bg: "rgba(16,185,129,0.15)", fg: "#10b981" },
    Recyclable: { bg: "rgba(59,130,246,0.15)", fg: "#3b82f6" },
    Hazardous: { bg: "rgba(239,68,68,0.15)", fg: "#ef4444" },
    Other: { bg: "rgba(234,179,8,0.15)", fg: "#eab308" },
  };
  const c = colors[type] || { bg: "rgba(148,163,184,0.15)", fg: "#94a3b8" };
  return `<span class="badge" style="background:${c.bg};color:${c.fg}">${type}</span>`;
}

function fillClass(pct) {
  if (pct >= 80) return "fill-high";
  if (pct >= 50) return "fill-medium";
  return "fill-low";
}

function formatDate(isoString) {
  if (!isoString) return "—";
  const d = new Date(isoString);
  return d.toLocaleDateString("en-GB", { day: "2-digit", month: "2-digit", year: "numeric" }) +
    ", " + d.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

// ── Spinner ─────────────────────────────────────────────────────────────────
function setLoading(el, on) {
  el?.classList.toggle("loading", on);
}
