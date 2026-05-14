// js/charts.js - Chart rendering helpers

const ChartManager = (() => {
  const active = {};

  function destroy(id) {
    if (active[id]) { active[id].destroy(); delete active[id]; }
  }

  function make(id, config) {
    destroy(id);
    const el = document.getElementById(id);
    if (!el) return null;
    active[id] = new Chart(el, config);
    return active[id];
  }

  const yen = (v) => '¥' + (v >= 1_000_000
    ? (v / 1_000_000).toFixed(1) + 'M'
    : v.toLocaleString());

  const yenFull = (v) => '¥' + Number(v).toLocaleString();

  const PIE_COLORS = [
    '#3b82f6','#f97316','#22c55e','#8b5cf6',
    '#ec4899','#14b8a6','#f59e0b','#ef4444',
    '#06b6d4','#84cc16','#a78bfa','#fb923c',
  ];

  // Bar chart (monthly sales)
  function bar(id, labels, datasets, { stacked = false } = {}) {
    return make(id, {
      type: 'bar',
      data: { labels, datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'top' },
          tooltip: { callbacks: { label: ctx => `${ctx.dataset.label}: ${yenFull(ctx.raw)}` } },
        },
        scales: {
          x: { stacked },
          y: { stacked, beginAtZero: true, ticks: { callback: yen } },
        },
      },
    });
  }

  // Line chart
  function line(id, labels, datasets) {
    return make(id, {
      type: 'line',
      data: { labels, datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'top' },
          tooltip: { callbacks: { label: ctx => `${ctx.dataset.label}: ${yenFull(ctx.raw)}` } },
        },
        scales: { y: { beginAtZero: true, ticks: { callback: yen } } },
      },
    });
  }

  // KPI chart: bar (actual) + line (target)
  function kpi(id, labels, actual, target) {
    return make(id, {
      type: 'bar',
      data: {
        labels,
        datasets: [
          {
            label: '実績',
            data: actual,
            backgroundColor: '#3b82f680',
            borderColor: '#3b82f6',
            borderWidth: 1,
          },
          {
            label: '目標',
            data: target,
            type: 'line',
            borderColor: '#ef4444',
            borderWidth: 2,
            pointBackgroundColor: '#ef4444',
            fill: false,
            tension: 0.1,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'top' },
          tooltip: { callbacks: { label: ctx => `${ctx.dataset.label}: ${yenFull(ctx.raw)}` } },
        },
        scales: { y: { beginAtZero: true, ticks: { callback: yen } } },
      },
    });
  }

  // Doughnut chart
  function doughnut(id, labels, data) {
    const total = data.reduce((a, b) => a + b, 0);
    return make(id, {
      type: 'doughnut',
      data: {
        labels,
        datasets: [{
          data,
          backgroundColor: PIE_COLORS.slice(0, labels.length),
          borderWidth: 2,
          borderColor: '#fff',
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: 'right', labels: { font: { size: 11 }, boxWidth: 12 } },
          tooltip: {
            callbacks: {
              label: ctx => `${yenFull(ctx.raw)} (${total > 0 ? ((ctx.raw / total) * 100).toFixed(1) : 0}%)`,
            },
          },
        },
      },
    });
  }

  // Horizontal bar (operator ranking)
  function hbar(id, labels, data, color = '#3b82f6') {
    return make(id, {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: '寄付金額',
          data,
          backgroundColor: color + '80',
          borderColor: color,
          borderWidth: 1,
        }],
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: ctx => yenFull(ctx.raw) } },
        },
        scales: { x: { beginAtZero: true, ticks: { callback: yen } } },
      },
    });
  }

  return { bar, line, kpi, doughnut, hbar, destroy };
})();
