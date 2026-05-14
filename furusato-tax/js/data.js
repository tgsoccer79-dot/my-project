// js/data.js - Data management layer

const DataManager = (() => {
  const KEYS = {
    SALES: 'fs_sales',
    KPI: 'fs_kpi_targets',
    MAPPING: 'fs_column_mapping',
    HISTORY: 'fs_import_history',
  };

  const DEFAULT_MAPPING = {
    date: '', portal: '', municipality: '', operator: '',
    itemName: '', category: '', amount: '', count: '',
  };

  const MUNICIPALITY_ALIASES = {
    '宮崎市': '宮崎市', '宮崎県宮崎市': '宮崎市', 'Miyazaki': '宮崎市',
    '三木町': '三木町', '香川県三木町': '三木町', 'Miki': '三木町',
  };

  const MUNICIPALITIES = ['宮崎市', '三木町'];

  function normalizeMunicipality(name) {
    if (!name) return '';
    const n = String(name).trim();
    for (const [k, v] of Object.entries(MUNICIPALITY_ALIASES)) {
      if (n.includes(k)) return v;
    }
    return n;
  }

  function parseAmount(v) {
    if (typeof v === 'number') return Math.round(v);
    if (!v) return 0;
    return parseInt(String(v).replace(/[^\d-]/g, ''), 10) || 0;
  }

  function parseCount(v) {
    if (typeof v === 'number') return Math.round(v);
    if (!v) return 1;
    const n = parseInt(String(v).replace(/[^\d]/g, ''), 10);
    return isNaN(n) || n < 1 ? 1 : n;
  }

  function parseDate(v) {
    if (!v) return null;
    const s = String(v).replace(/\//g, '-').replace(/年/g, '-').replace(/月/g, '-').replace(/日/g, '').trim();
    const m = s.match(/(\d{4})-(\d{1,2})-(\d{1,2})/);
    if (!m) return null;
    return `${m[1]}-${m[2].padStart(2, '0')}-${m[3].padStart(2, '0')}`;
  }

  function yearMonth(dateStr) {
    return dateStr ? dateStr.substring(0, 7) : null;
  }

  function fiscalYear(ym) {
    if (!ym) return null;
    const [y, mo] = ym.split('-').map(Number);
    return mo >= 4 ? y : y - 1;
  }

  function currentFiscalYear() {
    const now = new Date();
    const mo = now.getMonth() + 1;
    return mo >= 4 ? now.getFullYear() : now.getFullYear() - 1;
  }

  function load(key) {
    try { return JSON.parse(localStorage.getItem(key)); } catch { return null; }
  }

  function store(key, data) {
    try { localStorage.setItem(key, JSON.stringify(data)); return true; } catch { return false; }
  }

  // ── Sales ─────────────────────────────────────────────────────────────
  function getSales() { return load(KEYS.SALES) || []; }

  function importCSV(rows, mapping) {
    const existing = getSales();
    const added = [];
    for (const row of rows) {
      const dateStr = parseDate(row[mapping.date]);
      if (!dateStr) continue;
      const amount = parseAmount(row[mapping.amount]);
      if (amount <= 0) continue;
      const municipality = normalizeMunicipality(row[mapping.municipality]);
      if (!MUNICIPALITIES.includes(municipality)) continue;
      added.push({
        date: dateStr,
        ym: yearMonth(dateStr),
        portal: (row[mapping.portal] || '不明').trim(),
        municipality,
        operator: (row[mapping.operator] || '不明').trim(),
        itemName: (row[mapping.itemName] || '').trim(),
        category: (row[mapping.category] || '不明').trim(),
        amount,
        count: parseCount(row[mapping.count]),
      });
    }
    store(KEYS.SALES, [...existing, ...added]);
    return added.length;
  }

  function query(f = {}) {
    let d = getSales();
    if (f.municipality) d = d.filter(r => r.municipality === f.municipality);
    if (f.ym)           d = d.filter(r => r.ym === f.ym);
    if (f.year)         d = d.filter(r => r.date.startsWith(String(f.year)));
    if (f.fy !== undefined) d = d.filter(r => fiscalYear(r.ym) === f.fy);
    if (f.portal)       d = d.filter(r => r.portal === f.portal);
    return d;
  }

  function aggregate(data, groupBy) {
    const map = {};
    for (const r of data) {
      const k = r[groupBy] || '不明';
      if (!map[k]) map[k] = { key: k, amount: 0, count: 0 };
      map[k].amount += r.amount;
      map[k].count  += r.count;
    }
    return Object.values(map).sort((a, b) => b.amount - a.amount);
  }

  // Monthly array for calendar year (Jan-Dec)
  function monthlySales(year, municipality) {
    return Array.from({ length: 12 }, (_, i) => {
      const ym = `${year}-${String(i + 1).padStart(2, '0')}`;
      const d  = query({ ym, municipality: municipality || undefined });
      return { ym, amount: d.reduce((s, r) => s + r.amount, 0), count: d.reduce((s, r) => s + r.count, 0) };
    });
  }

  // Monthly array for fiscal year (Apr-Mar = month indices 0-11)
  function fyMonthlySales(fy, municipality) {
    const pairs = [
      [fy, 4],[fy, 5],[fy, 6],[fy, 7],[fy, 8],[fy, 9],
      [fy, 10],[fy, 11],[fy, 12],[fy + 1, 1],[fy + 1, 2],[fy + 1, 3],
    ];
    return pairs.map(([y, mo], i) => {
      const ym = `${y}-${String(mo).padStart(2, '0')}`;
      const d  = query({ ym, municipality: municipality || undefined });
      return { ym, fyMonth: i + 1, label: `${mo}月`, amount: d.reduce((s, r) => s + r.amount, 0), count: d.reduce((s, r) => s + r.count, 0) };
    });
  }

  function getAvailableYears() {
    const s = getSales();
    const y = new Set(s.map(r => r.date.substring(0, 4)));
    return Array.from(y).sort().reverse();
  }

  function getAvailableFYs() {
    const s = getSales();
    const y = new Set(s.map(r => fiscalYear(r.ym)).filter(Boolean));
    return Array.from(y).sort().reverse();
  }

  function getPortals() {
    const s = getSales();
    return Array.from(new Set(s.map(r => r.portal).filter(Boolean))).sort();
  }

  // ── KPI ───────────────────────────────────────────────────────────────
  function getKPI(fy) { return (load(KEYS.KPI) || {})[fy] || {}; }

  function saveKPI(fy, data) {
    const all = load(KEYS.KPI) || {};
    all[fy] = data;
    return store(KEYS.KPI, all);
  }

  // ── Column mapping ────────────────────────────────────────────────────
  function getMapping() { return load(KEYS.MAPPING) || { ...DEFAULT_MAPPING }; }
  function saveMapping(m) { return store(KEYS.MAPPING, m); }

  // ── Import history ────────────────────────────────────────────────────
  function getHistory() { return load(KEYS.HISTORY) || []; }

  function addHistory(rec) {
    const h = getHistory();
    h.unshift({ ...rec, at: new Date().toISOString() });
    if (h.length > 50) h.pop();
    store(KEYS.HISTORY, h);
  }

  // ── Utilities ─────────────────────────────────────────────────────────
  function clearAll() { Object.values(KEYS).forEach(k => localStorage.removeItem(k)); }

  // Auto-detect column mapping from CSV headers
  function autoDetectMapping(headers) {
    const rules = {
      date:         [/日付/, /申込/, /受付/, /date/i, /注文日/],
      portal:       [/ポータル/, /サイト/, /portal/i, /媒体/],
      municipality: [/自治体/, /市町村/, /municipality/i, /地域/],
      operator:     [/事業者/, /提供者/, /operator/i, /生産者/],
      itemName:     [/返礼品/, /商品名/, /item/i, /品名/],
      category:     [/カテゴリ/, /category/i, /分類/],
      amount:       [/金額/, /寄付額/, /amount/i, /価格/],
      count:        [/件数/, /数量/, /count/i, /個数/],
    };
    const m = { ...DEFAULT_MAPPING };
    for (const [field, patterns] of Object.entries(rules)) {
      for (const h of headers) {
        if (patterns.some(p => typeof p === 'string' ? h.includes(p) : p.test(h))) {
          m[field] = h;
          break;
        }
      }
    }
    return m;
  }

  return {
    importCSV, getSales, query, aggregate,
    monthlySales, fyMonthlySales,
    getAvailableYears, getAvailableFYs, getPortals,
    getKPI, saveKPI,
    getMapping, saveMapping,
    getHistory, addHistory,
    clearAll, currentFiscalYear, fiscalYear, yearMonth,
    autoDetectMapping, MUNICIPALITIES,
  };
})();
