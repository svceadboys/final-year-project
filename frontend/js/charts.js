/**
 * charts.js – Chart.js builder functions for the EcoSort AI dashboard
 * Uses distinct colors per waste class across all charts
 */

// ── Waste class color palette ────────────────────────────────────────────────
const WASTE_COLORS = {
    cardboard: { main: "#f59e0b", bg: "rgba(245,158,11,0.75)" },
    glass: { main: "#3b82f6", bg: "rgba(59,130,246,0.75)" },
    metal: { main: "#94a3b8", bg: "rgba(148,163,184,0.75)" },
    paper: { main: "#10b981", bg: "rgba(16,185,129,0.75)" },
    plastic: { main: "#a855f7", bg: "rgba(168,85,247,0.75)" },
    trash: { main: "#ef4444", bg: "rgba(239,68,68,0.75)" },
};

const WASTE_ORDER = ["cardboard", "glass", "metal", "paper", "plastic", "trash"];

function getWasteColor(type) {
    return WASTE_COLORS[type] || { main: "#64748b", bg: "rgba(100,116,139,0.75)" };
}

// ── Chart.js global defaults ─────────────────────────────────────────────────
Chart.defaults.color = "#8b92a9";
Chart.defaults.font.family = "'Inter', 'Segoe UI', sans-serif";
Chart.defaults.font.size = 12;
Chart.defaults.plugins.legend.display = false;
Chart.defaults.responsive = true;
Chart.defaults.maintainAspectRatio = false;

// ── destroy helper ───────────────────────────────────────────────────────────
const _chartInstances = {};
function destroyChart(canvasId) {
    if (_chartInstances[canvasId]) {
        _chartInstances[canvasId].destroy();
        delete _chartInstances[canvasId];
    }
}

// ═══════════════════════════════════════════════════════════════════════════════
//  PIE / DOUGHNUT – Waste Distribution  (distinct color per class)
// ═══════════════════════════════════════════════════════════════════════════════
function buildWasteDistributionChart(canvasId, distribution) {
    destroyChart(canvasId);
    const labels = Object.keys(distribution);
    const data = Object.values(distribution);
    const bgColors = labels.map(l => getWasteColor(l).bg);
    const borderColors = labels.map(l => getWasteColor(l).main);

    const ctx = document.getElementById(canvasId).getContext("2d");
    _chartInstances[canvasId] = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels,
            datasets: [{
                data,
                backgroundColor: bgColors,
                borderColor: borderColors,
                borderWidth: 2,
                hoverOffset: 8,
            }],
        },
        options: {
            cutout: "62%",
            plugins: {
                legend: {
                    display: true,
                    position: "right",
                    labels: { padding: 14, usePointStyle: true, pointStyle: "circle", font: { size: 12 } },
                },
                tooltip: {
                    callbacks: {
                        label: ctx => ` ${ctx.label}: ${ctx.raw} images (${((ctx.raw / data.reduce((a, b) => a + b, 0)) * 100).toFixed(1)}%)`,
                    },
                },
            },
        },
    });
}

// ═══════════════════════════════════════════════════════════════════════════════
//  HORIZONTAL BAR – Waste type counts  (distinct color per bar)
// ═══════════════════════════════════════════════════════════════════════════════
function buildHorizontalBarChart(canvasId, distribution) {
    destroyChart(canvasId);
    const labels = Object.keys(distribution);
    const data = Object.values(distribution);
    const bgColors = labels.map(l => getWasteColor(l).bg);
    const borderColors = labels.map(l => getWasteColor(l).main);

    const ctx = document.getElementById(canvasId).getContext("2d");
    _chartInstances[canvasId] = new Chart(ctx, {
        type: "bar",
        data: {
            labels,
            datasets: [{
                data,
                backgroundColor: bgColors,
                borderColor: borderColors,
                borderWidth: 1.5,
                borderRadius: 6,
                barThickness: 22,
            }],
        },
        options: {
            indexAxis: "y",
            scales: {
                x: {
                    beginAtZero: true,
                    grid: { color: "rgba(148,163,184,0.08)" },
                    ticks: { stepSize: 1, precision: 0 },
                    title: { display: true, text: "Number of Images", color: "#8b92a9" },
                },
                y: {
                    grid: { display: false },
                },
            },
            plugins: {
                tooltip: {
                    callbacks: { label: ctx => ` ${ctx.raw} images` },
                },
            },
        },
    });
}

// ═══════════════════════════════════════════════════════════════════════════════
//  BIN FILL LEVELS – Vertical bar (colored by fill level)
// ═══════════════════════════════════════════════════════════════════════════════
function buildBinFillChart(canvasId, bins) {
    destroyChart(canvasId);
    const labels = bins.map(b => b.location.split(" - ")[0]);
    const data = bins.map(b => b.current_fill);
    const bgColors = data.map(v =>
        v >= 80 ? "rgba(239,68,68,0.7)" : v >= 50 ? "rgba(234,179,8,0.7)" : "rgba(16,185,129,0.7)"
    );

    const ctx = document.getElementById(canvasId).getContext("2d");
    _chartInstances[canvasId] = new Chart(ctx, {
        type: "bar",
        data: {
            labels,
            datasets: [{
                data,
                backgroundColor: bgColors,
                borderRadius: 6,
                barThickness: 28,
            }],
        },
        options: {
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100,
                    grid: { color: "rgba(148,163,184,0.08)" },
                    ticks: { callback: v => v + "%" },
                },
                x: { grid: { display: false } },
            },
        },
    });
}

// ═══════════════════════════════════════════════════════════════════════════════
//  FORECAST LINE CHART (ARIMA)
// ═══════════════════════════════════════════════════════════════════════════════
function buildForecastChart(canvasId, histDates, histVals, fcDates, fcVals, upper, lower) {
    destroyChart(canvasId);
    const allLabels = [...histDates, ...fcDates];

    const datasets = [
        {
            label: "Actual",
            data: [...histVals, ...Array(fcDates.length).fill(null)],
            borderColor: "#10b981",
            backgroundColor: "rgba(16,185,129,0.1)",
            borderWidth: 2,
            pointRadius: 2,
            tension: 0.3,
            fill: false,
        },
        {
            label: "Predicted",
            data: [...Array(histDates.length).fill(null), ...fcVals],
            borderColor: "#a855f7",
            borderWidth: 2,
            pointRadius: 3,
            borderDash: [6, 3],
            tension: 0.3,
            fill: false,
        },
    ];

    if (upper && upper.length) {
        datasets.push({
            label: "Upper Bound",
            data: [...Array(histDates.length).fill(null), ...upper],
            borderColor: "transparent",
            backgroundColor: "rgba(168,85,247,0.10)",
            fill: "+1",
            pointRadius: 0,
        });
        datasets.push({
            label: "Lower Bound",
            data: [...Array(histDates.length).fill(null), ...lower],
            borderColor: "transparent",
            backgroundColor: "rgba(168,85,247,0.10)",
            fill: "-1",
            pointRadius: 0,
        });
    }

    const ctx = document.getElementById(canvasId).getContext("2d");
    _chartInstances[canvasId] = new Chart(ctx, {
        type: "line",
        data: { labels: allLabels, datasets },
        options: {
            scales: {
                y: { beginAtZero: true, max: 120, grid: { color: "rgba(148,163,184,0.08)" }, ticks: { callback: v => v + "%" } },
                x: { grid: { display: false } },
            },
            plugins: { legend: { display: false } },
        },
    });
}

// ═══════════════════════════════════════════════════════════════════════════════
//  CATEGORY BAR (stacked / grouped)
// ═══════════════════════════════════════════════════════════════════════════════
function buildCategoryChart(canvasId, labels, datasets) {
    destroyChart(canvasId);
    const ctx = document.getElementById(canvasId).getContext("2d");
    _chartInstances[canvasId] = new Chart(ctx, {
        type: "bar",
        data: { labels, datasets },
        options: {
            scales: {
                y: { beginAtZero: true, stacked: true, grid: { color: "rgba(148,163,184,0.08)" } },
                x: { stacked: true, grid: { display: false } },
            },
            plugins: { legend: { display: true, position: "top", labels: { usePointStyle: true, pointStyle: "circle" } } },
        },
    });
}

// ═══════════════════════════════════════════════════════════════════════════════
//  DAILY TREND LINE
// ═══════════════════════════════════════════════════════════════════════════════
function buildTrendChart(canvasId, labels, data) {
    destroyChart(canvasId);
    const ctx = document.getElementById(canvasId).getContext("2d");
    _chartInstances[canvasId] = new Chart(ctx, {
        type: "line",
        data: {
            labels,
            datasets: [{
                data,
                borderColor: "#10b981",
                backgroundColor: "rgba(16,185,129,0.08)",
                borderWidth: 2,
                pointRadius: 3,
                tension: 0.35,
                fill: true,
            }],
        },
        options: {
            scales: {
                y: { beginAtZero: true, grid: { color: "rgba(148,163,184,0.08)" } },
                x: { grid: { display: false } },
            },
        },
    });
}
