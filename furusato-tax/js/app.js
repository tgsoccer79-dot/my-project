// js/app.js - Main application

const App = (() => {
  // ── Utilities ────────────────────────────────────────────────────────
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];

  function fmt(n) { return '¥' + Number(n).toLocaleString(); }
  function fmtM(n) { return (n / 1_000_000).toFixed(2) + '億'; }

  function toast(msg, type = 'success') {
    const id = 'toast-' + Date.now();
    const color = type === 'success' ? 'text-bg-success' : type === 'error' ? 'text-bg-danger' : 'text-bg-warning';
    const el = document.createElement('div');
    el.innerHTML = `<div id="${id}" class="toast ${color} align-items-center border-0" role="alert">
      <div class="d-flex"><div class="toast-body">${msg}</div>
      <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button></div></div>`;
    $('#toast-container').appendChild(el.firstElementChild);
    const t = new bootstrap.Toast($('#' + id), { delay: 3500 });
    t.show();
    $('#' + id).addEventListener('hidden.bs.toast', () => $('#' + id)?.remove());
  }

  function achieveClass(rate) {
    if (rate >= 100) return 'over';
    if (rate >= 80)  return 'warning';
    return 'under';
  }

  function currentYM() {
    const n = new Date();
    return `${n.getFullYear()}-${String(n.getMonth() + 1).padStart(2, '0')}`;
  }

  function fyMonthLabels() {
    return ['4月','5月','6月','7月','8月','9月','10月','11月','12月','1月','2月','3月'];
  }

  function noDataHtml(msg = 'データがありません') {
    return `<div class="no-data"><div class="no-data-icon"><i class="bi bi-inbox"></i></div><p>${msg}</p>
      <a href="#" class="btn btn-sm btn-primary" data-page="csv-import">CSVを取込む</a></div>`;
  }

  // ── Navigation ────────────────────────────────────────────────────────
  const PAGE_TITLES = {
    'dashboard':       'ダッシュボード',
    'csv-import':      'CSV取込',
    'overall-sales':   '全体売上管理',
    'miyazaki-sales':  '宮崎市 売上管理',
    'miki-sales':      '三木町 売上管理',
    'portal-sales':    'ポータル別売上',
    'kpi-management':  'KPI管理',
    'settings':        '設定',
  };

  function navigate(page) {
    $$('.sidebar-link').forEach(l => l.classList.remove('active'));
    const link = $(`.sidebar-link[data-page="${page}"]`);
    if (link) link.classList.add('active');
    $('#page-title').textContent = PAGE_TITLES[page] || page;
    const container = $('#page-content');
    container.innerHTML = '<div class="text-center py-5"><div class="spinner-border text-primary"></div></div>';
    setTimeout(() => {
      const renderers = {
        'dashboard':      renderDashboard,
        'csv-import':     renderCsvImport,
        'overall-sales':  renderOverallSales,
        'miyazaki-sales': () => renderMunicipalitySales('宮崎市'),
        'miki-sales':     () => renderMunicipalitySales('三木町'),
        'portal-sales':   renderPortalSales,
        'kpi-management': renderKPIManagement,
        'settings':       renderSettings,
      };
      (renderers[page] || (() => { container.innerHTML = '<p class="p-4">ページが見つかりません</p>'; }))();
    }, 50);
  }

  function initNav() {
    document.addEventListener('click', e => {
      const link = e.target.closest('[data-page]');
      if (link) { e.preventDefault(); navigate(link.dataset.page); }
    });
  }

  // ── Dashboard ─────────────────────────────────────────────────────────
  function renderDashboard() {
    const ym  = currentYM();
    const fy  = DataManager.currentFiscalYear();
    const all = DataManager.query({ ym });
    const miy = DataManager.query({ ym, municipality: '宮崎市' });
    const mik = DataManager.query({ ym, municipality: '三木町' });

    const sum = d => d.reduce((s, r) => s + r.amount, 0);
    const cnt = d => d.reduce((s, r) => s + r.count, 0);

    // YoY
    const [y, mo] = ym.split('-');
    const prevYM  = `${Number(y) - 1}-${mo}`;
    const prevAll = DataManager.query({ ym: prevYM });
    const yoy     = prevAll.length && sum(prevAll) > 0 ? ((sum(all) - sum(prevAll)) / sum(prevAll) * 100) : null;

    // KPI
    const kpi  = DataManager.getKPI(fy);
    const kpiM = kpi['宮崎市']?.[ym]?.salesTarget || 0;
    const kpiK = kpi['三木町']?.[ym]?.salesTarget || 0;

    const [yyyy, mm] = ym.split('-');
    const dateLabel = `${yyyy}年${parseInt(mm)}月`;

    const card = (label, value, sub, icon, color) =>
      `<div class="col-sm-6 col-xl-3">
        <div class="stat-card">
          <div class="stat-card-icon" style="background:${color}22;color:${color}">
            <i class="bi bi-${icon}"></i>
          </div>
          <div class="stat-card-label">${label}</div>
          <div class="stat-card-value">${value}</div>
          <div class="stat-card-sub">${sub}</div>
        </div>
      </div>`;

    const kpiBar = (label, actual, target, color) => {
      const rate = target > 0 ? Math.min((actual / target) * 100, 150) : 0;
      const pct  = target > 0 ? ((actual / target) * 100).toFixed(1) : '－';
      return `<div class="kpi-progress-item">
        <div class="kpi-progress-header">
          <span class="kpi-progress-label">${label}</span>
          <span class="kpi-progress-value">${pct}% <small class="text-muted">(${fmt(actual)} / ${fmt(target)})</small></span>
        </div>
        <div class="kpi-progress-bar">
          <div class="kpi-progress-fill" style="width:${Math.min(rate,100)}%;background:${color}"></div>
        </div>
      </div>`;
    };

    const fyMonths = DataManager.fyMonthlySales(fy);
    const fyLabels  = fyMonths.map(m => m.label);
    const fyAmounts = fyMonths.map(m => m.amount);
    const fyMiyAmounts = DataManager.fyMonthlySales(fy, '宮崎市').map(m => m.amount);
    const fyMikAmounts = DataManager.fyMonthlySales(fy, '三木町').map(m => m.amount);

    const hasSales = DataManager.getSales().length > 0;
    const history  = DataManager.getHistory().slice(0, 3);

    $('#page-content').innerHTML = `
      <div class="row g-3 mb-4">
        ${card(dateLabel + ' 全体売上', fmt(sum(all)), cnt(all) + '件', 'currency-yen', '#3b82f6')}
        ${card(dateLabel + ' 宮崎市', fmt(sum(miy)), cnt(miy) + '件', 'building', '#f97316')}
        ${card(dateLabel + ' 三木町', fmt(sum(mik)), cnt(mik) + '件', 'building', '#8b5cf6')}
        ${card('前年同期比', yoy !== null ? (yoy >= 0 ? '+' : '') + yoy.toFixed(1) + '%' : '－',
          yoy !== null ? '対前年' + dateLabel : 'データ不足', yoy !== null && yoy >= 0 ? 'graph-up' : 'graph-down',
          yoy !== null && yoy >= 0 ? '#22c55e' : '#ef4444')}
      </div>

      <div class="row g-4 mb-4">
        <div class="col-lg-8">
          <div class="panel">
            <div class="panel-header">
              <h6 class="panel-title">${fy}年度 月次売上トレンド</h6>
            </div>
            <div class="panel-body">
              ${hasSales ? `<div class="chart-container"><canvas id="dash-trend"></canvas></div>` : noDataHtml()}
            </div>
          </div>
        </div>
        <div class="col-lg-4">
          <div class="panel">
            <div class="panel-header">
              <h6 class="panel-title">${dateLabel} KPI達成状況</h6>
            </div>
            <div class="panel-body">
              ${kpiM > 0 || kpiK > 0
                ? kpiBar('宮崎市', sum(miy), kpiM, '#f97316') + kpiBar('三木町', sum(mik), kpiK, '#8b5cf6')
                : `<p class="text-muted small">目標未設定。<a href="#" data-page="kpi-management">KPI管理</a>で設定してください。</p>`}
            </div>
          </div>
        </div>
      </div>

      <div class="row g-4">
        <div class="col-lg-6">
          <div class="panel">
            <div class="panel-header">
              <h6 class="panel-title">直近のCSVインポート履歴</h6>
            </div>
            <div class="panel-body p-0">
              ${history.length
                ? `<table class="table table-sm mb-0">
                    <thead><tr><th>ファイル名</th><th>件数</th><th>取込日時</th></tr></thead>
                    <tbody>${history.map(h =>
                      `<tr><td>${h.fileName}</td><td>${h.count.toLocaleString()}</td>
                       <td>${new Date(h.at).toLocaleString('ja-JP')}</td></tr>`).join('')}</tbody>
                   </table>`
                : `<p class="text-muted p-3 mb-0 small">インポート履歴がありません</p>`}
            </div>
          </div>
        </div>
        <div class="col-lg-6">
          <div class="panel">
            <div class="panel-header">
              <h6 class="panel-title">宮崎市 事業者別ランキング（今月）</h6>
            </div>
            <div class="panel-body p-0">
              ${renderOperatorTable(miy, 5)}
            </div>
          </div>
        </div>
      </div>`;

    if (hasSales) {
      ChartManager.bar('dash-trend', fyLabels, [
        { label: '宮崎市', data: fyMiyAmounts, backgroundColor: '#f9731680', borderColor: '#f97316', borderWidth: 1 },
        { label: '三木町', data: fyMikAmounts, backgroundColor: '#8b5cf680', borderColor: '#8b5cf6', borderWidth: 1 },
      ], { stacked: true });
    }
  }

  function renderOperatorTable(data, limit = 10) {
    const agg = DataManager.aggregate(data, 'operator').slice(0, limit);
    if (!agg.length) return '<p class="text-muted p-3 mb-0 small">データがありません</p>';
    return `<table class="table table-sm mb-0">
      <thead><tr><th>#</th><th>事業者名</th><th class="text-end">金額</th><th class="text-end">件数</th></tr></thead>
      <tbody>${agg.map((r, i) =>
        `<tr><td class="text-muted">${i + 1}</td><td>${r.key}</td>
         <td class="text-end amount-text">${fmt(r.amount)}</td>
         <td class="text-end">${r.count}</td></tr>`).join('')}</tbody>
    </table>`;
  }

  // ── CSV Import ────────────────────────────────────────────────────────
  let csvRows = [], csvHeaders = [], csvMapping = {};

  function renderCsvImport() {
    const history = DataManager.getHistory();
    $('#page-content').innerHTML = `
      <div class="row g-4">
        <div class="col-lg-7">
          <div class="panel mb-4">
            <div class="panel-header"><h6 class="panel-title">CSVファイルの取込</h6></div>
            <div class="panel-body">
              <div class="drop-zone" id="drop-zone">
                <div class="drop-zone-icon"><i class="bi bi-file-earmark-spreadsheet"></i></div>
                <p class="mb-1 fw-semibold">CSVファイルをドロップ、またはクリックして選択</p>
                <p class="text-muted small mb-0">UTF-8 / Shift-JIS 対応</p>
                <input type="file" id="csv-file-input" accept=".csv" class="d-none">
              </div>
            </div>
          </div>

          <div class="panel mb-4 d-none" id="mapping-panel">
            <div class="panel-header">
              <h6 class="panel-title">列マッピング設定</h6>
              <small class="text-muted">CSVの列名と項目を対応させてください</small>
            </div>
            <div class="panel-body">
              <div class="row g-2" id="mapping-fields"></div>
              <div class="mt-3">
                <button class="btn btn-primary" id="btn-import">
                  <i class="bi bi-cloud-upload me-1"></i>取込実行
                </button>
                <button class="btn btn-outline-secondary ms-2" id="btn-save-mapping">
                  マッピングを保存
                </button>
              </div>
            </div>
          </div>

          <div class="panel d-none" id="preview-panel">
            <div class="panel-header">
              <h6 class="panel-title">プレビュー（先頭5行）</h6>
            </div>
            <div class="panel-body p-0" style="overflow-x:auto">
              <div id="preview-table"></div>
            </div>
          </div>
        </div>

        <div class="col-lg-5">
          <div class="panel">
            <div class="panel-header"><h6 class="panel-title">インポート履歴</h6></div>
            <div class="panel-body p-0">
              ${history.length
                ? `<table class="table table-sm mb-0">
                    <thead><tr><th>ファイル名</th><th>件数</th><th>日時</th></tr></thead>
                    <tbody>${history.map(h =>
                      `<tr><td style="max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${h.fileName}">${h.fileName}</td>
                       <td>${h.count.toLocaleString()}</td>
                       <td style="white-space:nowrap">${new Date(h.at).toLocaleString('ja-JP',{month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit'})}</td></tr>`).join('')}
                    </tbody></table>`
                : '<p class="text-muted p-3 small mb-0">履歴なし</p>'}
            </div>
          </div>
        </div>
      </div>`;

    const dz = $('#drop-zone');
    const fi = $('#csv-file-input');

    dz.addEventListener('click', () => fi.click());
    dz.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('drag-over'); });
    dz.addEventListener('dragleave', () => dz.classList.remove('drag-over'));
    dz.addEventListener('drop', e => { e.preventDefault(); dz.classList.remove('drag-over'); handleFile(e.dataTransfer.files[0]); });
    fi.addEventListener('change', () => handleFile(fi.files[0]));
  }

  function handleFile(file) {
    if (!file) return;
    Papa.parse(file, {
      header: true,
      skipEmptyLines: true,
      complete(res) {
        csvHeaders = res.meta.fields || [];
        csvRows    = res.data;
        const saved = DataManager.getMapping();
        csvMapping  = DataManager.autoDetectMapping(csvHeaders);
        // merge with saved if columns exist
        for (const [k, v] of Object.entries(saved)) {
          if (v && csvHeaders.includes(v)) csvMapping[k] = v;
        }
        showMappingUI(file.name);
      },
      error() { toast('CSVの読み込みに失敗しました。文字コードを確認してください。', 'error'); },
    });
  }

  function showMappingUI(fileName) {
    const FIELD_LABELS = {
      date: '日付 *', portal: 'ポータルサイト *', municipality: '自治体名 *',
      operator: '事業者名', itemName: '返礼品名', category: 'カテゴリ',
      amount: '寄付金額 *', count: '件数',
    };
    const opts = ['', ...csvHeaders].map(h => `<option value="${h}" ${csvMapping[Object.keys(FIELD_LABELS)[0]] === h ? '' : ''}>${h || '(選択なし)'}</option>`).join('');

    const fieldsHtml = Object.entries(FIELD_LABELS).map(([k, label]) =>
      `<div class="col-sm-6">
        <label class="form-label small fw-semibold">${label}</label>
        <select class="form-select form-select-sm" data-field="${k}">
          ${csvHeaders.map(h => `<option value="${h}" ${csvMapping[k] === h ? 'selected' : ''}>${h}</option>`).join('')}
          <option value="" ${!csvMapping[k] ? 'selected' : ''}>(選択なし)</option>
        </select>
      </div>`).join('');

    $('#mapping-fields').innerHTML = fieldsHtml;
    $('#mapping-panel').classList.remove('d-none');

    // Preview
    const previewRows = csvRows.slice(0, 5);
    const previewHtml = `<table class="table table-sm table-bordered mb-0" style="font-size:11px">
      <thead><tr>${csvHeaders.map(h => `<th style="white-space:nowrap">${h}</th>`).join('')}</tr></thead>
      <tbody>${previewRows.map(r =>
        `<tr>${csvHeaders.map(h => `<td style="white-space:nowrap;max-width:120px;overflow:hidden;text-overflow:ellipsis">${r[h] ?? ''}</td>`).join('')}</tr>`
      ).join('')}</tbody></table>`;
    $('#preview-table').innerHTML = previewHtml;
    $('#preview-panel').classList.remove('d-none');

    // Sync mapping from selects
    $$('#mapping-fields select').forEach(sel => {
      sel.addEventListener('change', () => {
        csvMapping[sel.dataset.field] = sel.value;
      });
    });

    $('#btn-import').addEventListener('click', () => {
      const required = ['date', 'municipality', 'amount'];
      const missing  = required.filter(k => !csvMapping[k]);
      if (missing.length) {
        toast('必須項目（日付、自治体名、寄付金額）を設定してください', 'error');
        return;
      }
      const count = DataManager.importCSV(csvRows, csvMapping);
      DataManager.addHistory({ fileName, count });
      toast(`${count.toLocaleString()}件のデータを取込みました`, 'success');
      setTimeout(() => navigate('csv-import'), 500);
    });

    $('#btn-save-mapping').addEventListener('click', () => {
      DataManager.saveMapping(csvMapping);
      toast('マッピングを保存しました', 'success');
    });
  }

  // ── Overall Sales ─────────────────────────────────────────────────────
  function renderOverallSales() {
    const fys  = DataManager.getAvailableFYs();
    const fy   = fys[0] || DataManager.currentFiscalYear();
    const hasSales = DataManager.getSales().length > 0;

    $('#page-content').innerHTML = `
      <div class="filter-bar mb-4">
        <div>
          <label>年度</label>
          <select class="form-select form-select-sm" id="ov-fy" style="width:120px">
            ${fys.map(y => `<option value="${y}" ${y === fy ? 'selected' : ''}>${y}年度</option>`).join('')}
            ${!fys.length ? `<option value="${fy}">${fy}年度</option>` : ''}
          </select>
        </div>
      </div>
      <div class="row g-3 mb-4" id="ov-cards"></div>
      <div class="row g-4 mb-4">
        <div class="col-12">
          <div class="panel">
            <div class="panel-header"><h6 class="panel-title" id="ov-chart-title">月次売上トレンド</h6></div>
            <div class="panel-body">
              ${hasSales ? `<div class="chart-container"><canvas id="ov-trend"></canvas></div>` : noDataHtml()}
            </div>
          </div>
        </div>
      </div>
      <div class="row g-4 mb-4">
        <div class="col-md-6">
          <div class="panel">
            <div class="panel-header"><h6 class="panel-title">ポータル別構成</h6></div>
            <div class="panel-body"><div class="chart-container-sm"><canvas id="ov-portal-pie"></canvas></div></div>
          </div>
        </div>
        <div class="col-md-6">
          <div class="panel">
            <div class="panel-header"><h6 class="panel-title">カテゴリ別構成</h6></div>
            <div class="panel-body"><div class="chart-container-sm"><canvas id="ov-cat-pie"></canvas></div></div>
          </div>
        </div>
      </div>
      <div class="panel">
        <div class="panel-header"><h6 class="panel-title">月次サマリー</h6></div>
        <div class="panel-body p-0" id="ov-table"></div>
      </div>`;

    function refresh(selectedFY) {
      const months = DataManager.fyMonthlySales(selectedFY);
      const miyM   = DataManager.fyMonthlySales(selectedFY, '宮崎市');
      const mikM   = DataManager.fyMonthlySales(selectedFY, '三木町');
      const labels = months.map(m => m.label);

      const totAmt = months.reduce((s, m) => s + m.amount, 0);
      const totCnt = months.reduce((s, m) => s + m.count, 0);
      const miyAmt = miyM.reduce((s, m) => s + m.amount, 0);
      const mikAmt = mikM.reduce((s, m) => s + m.amount, 0);

      // Cards
      const card = (label, val, sub, color) =>
        `<div class="col-sm-6 col-xl-4">
          <div class="stat-card">
            <div class="stat-card-label">${label}</div>
            <div class="stat-card-value" style="color:${color}">${val}</div>
            <div class="stat-card-sub">${sub}</div>
          </div>
        </div>`;
      $('#ov-cards').innerHTML =
        card(selectedFY + '年度 全体', fmt(totAmt), totCnt.toLocaleString() + '件', '#1e293b') +
        card('宮崎市', fmt(miyAmt), totAmt > 0 ? ((miyAmt / totAmt) * 100).toFixed(1) + '%' : '0%', '#f97316') +
        card('三木町', fmt(mikAmt), totAmt > 0 ? ((mikAmt / totAmt) * 100).toFixed(1) + '%' : '0%', '#8b5cf6');

      // Trend chart
      if (hasSales) {
        ChartManager.bar('ov-trend', labels, [
          { label: '宮崎市', data: miyM.map(m => m.amount), backgroundColor: '#f9731680', borderColor: '#f97316', borderWidth: 1 },
          { label: '三木町', data: mikM.map(m => m.amount), backgroundColor: '#8b5cf680', borderColor: '#8b5cf6', borderWidth: 1 },
        ], { stacked: true });

        // Portal pie
        const allData = DataManager.query({ fy: selectedFY });
        const portalAgg = DataManager.aggregate(allData, 'portal');
        if (portalAgg.length) {
          ChartManager.doughnut('ov-portal-pie', portalAgg.map(r => r.key), portalAgg.map(r => r.amount));
        }
        const catAgg = DataManager.aggregate(allData, 'category');
        if (catAgg.length) {
          ChartManager.doughnut('ov-cat-pie', catAgg.map(r => r.key), catAgg.map(r => r.amount));
        }
      }

      // Table
      const rows = months.map((m, i) => {
        const miy = miyM[i].amount, mik = mikM[i].amount, tot = m.amount;
        const [yy, mm] = m.ym.split('-');
        return `<tr>
          <td>${yy}年${parseInt(mm)}月</td>
          <td class="text-end amount-text">${fmt(tot)}</td>
          <td class="text-end">${m.count}</td>
          <td class="text-end amount-text" style="color:#f97316">${fmt(miy)}</td>
          <td class="text-end amount-text" style="color:#8b5cf6">${fmt(mik)}</td>
        </tr>`;
      }).join('');
      $('#ov-table').innerHTML = `<table class="table table-sm mb-0">
        <thead><tr><th>月</th><th class="text-end">全体</th><th class="text-end">件数</th>
        <th class="text-end">宮崎市</th><th class="text-end">三木町</th></tr></thead>
        <tbody>${rows}</tbody>
        <tfoot class="table-light fw-bold"><tr>
          <td>合計</td><td class="text-end">${fmt(totAmt)}</td><td class="text-end">${totCnt}</td>
          <td class="text-end">${fmt(miyAmt)}</td><td class="text-end">${fmt(mikAmt)}</td>
        </tr></tfoot></table>`;
    }

    refresh(fy);
    $('#ov-fy').addEventListener('change', e => refresh(Number(e.target.value)));
  }

  // ── Municipality Sales (Miyazaki / Miki) ─────────────────────────────
  function renderMunicipalitySales(muni) {
    const isMiyazaki = muni === '宮崎市';
    const color      = isMiyazaki ? '#f97316' : '#8b5cf6';
    const fys        = DataManager.getAvailableFYs();
    const fy         = fys[0] || DataManager.currentFiscalYear();
    const hasSales   = DataManager.getSales().length > 0;

    $('#page-content').innerHTML = `
      <div class="filter-bar mb-4">
        <div>
          <label>年度</label>
          <select class="form-select form-select-sm" id="mu-fy" style="width:120px">
            ${fys.map(y => `<option value="${y}" ${y === fy ? 'selected' : ''}>${y}年度</option>`).join('')}
            ${!fys.length ? `<option value="${fy}">${fy}年度</option>` : ''}
          </select>
        </div>
      </div>

      <div class="row g-3 mb-4" id="mu-cards"></div>

      <div class="row g-4 mb-4">
        <div class="col-12">
          <div class="panel">
            <div class="panel-header"><h6 class="panel-title">月次売上トレンド</h6></div>
            <div class="panel-body">
              ${hasSales ? `<div class="chart-container"><canvas id="mu-trend"></canvas></div>` : noDataHtml()}
            </div>
          </div>
        </div>
      </div>

      ${isMiyazaki ? `
      <div class="row g-4 mb-4">
        <div class="col-lg-8">
          <div class="panel">
            <div class="panel-header"><h6 class="panel-title">事業者別売上ランキング</h6></div>
            <div class="panel-body">
              <div class="chart-container"><canvas id="mu-operator-bar"></canvas></div>
            </div>
          </div>
        </div>
        <div class="col-lg-4">
          <div class="panel">
            <div class="panel-header"><h6 class="panel-title">事業者別詳細</h6></div>
            <div class="panel-body p-0" id="mu-operator-table"></div>
          </div>
        </div>
      </div>` : ''}

      <div class="row g-4 mb-4">
        <div class="col-md-6">
          <div class="panel">
            <div class="panel-header"><h6 class="panel-title">ポータル別構成</h6></div>
            <div class="panel-body"><div class="chart-container-sm"><canvas id="mu-portal-pie"></canvas></div></div>
          </div>
        </div>
        <div class="col-md-6">
          <div class="panel">
            <div class="panel-header"><h6 class="panel-title">カテゴリ別構成</h6></div>
            <div class="panel-body"><div class="chart-container-sm"><canvas id="mu-cat-pie"></canvas></div></div>
          </div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-header"><h6 class="panel-title">月次サマリー</h6></div>
        <div class="panel-body p-0" id="mu-table"></div>
      </div>`;

    function refresh(selectedFY) {
      const months = DataManager.fyMonthlySales(selectedFY, muni);
      const totAmt = months.reduce((s, m) => s + m.amount, 0);
      const totCnt = months.reduce((s, m) => s + m.count, 0);
      const avg    = totCnt > 0 ? Math.round(totAmt / totCnt) : 0;

      // KPI
      const kpi    = DataManager.getKPI(selectedFY);
      const muKpi  = kpi[muni] || {};
      const kpiTot = Object.values(muKpi).reduce((s, v) => s + (v.salesTarget || 0), 0);
      const kpiRate = kpiTot > 0 ? ((totAmt / kpiTot) * 100).toFixed(1) : null;

      const card = (label, val, sub, c) =>
        `<div class="col-sm-6 col-xl-3">
          <div class="stat-card">
            <div class="stat-card-label">${label}</div>
            <div class="stat-card-value" style="color:${c}">${val}</div>
            <div class="stat-card-sub">${sub}</div>
          </div>
        </div>`;
      $('#mu-cards').innerHTML =
        card(`${selectedFY}年度 売上合計`, fmt(totAmt), '', color) +
        card('件数合計', totCnt.toLocaleString() + '件', '', '#1e293b') +
        card('客単価（平均）', fmt(avg), '', '#1e293b') +
        card('KPI達成率', kpiRate !== null ? kpiRate + '%' : '目標未設定',
          kpiRate !== null ? fmt(kpiTot) + ' が目標' : '', kpiRate !== null ? (Number(kpiRate) >= 100 ? '#22c55e' : '#ef4444') : '#94a3b8');

      // Trend
      if (hasSales) {
        const labels = months.map(m => m.label);

        // YoY
        const prevMonths = DataManager.fyMonthlySales(selectedFY - 1, muni);
        ChartManager.bar('mu-trend', labels, [
          { label: selectedFY + '年度', data: months.map(m => m.amount), backgroundColor: color + '80', borderColor: color, borderWidth: 1 },
          { label: (selectedFY - 1) + '年度', data: prevMonths.map(m => m.amount), backgroundColor: '#94a3b840', borderColor: '#94a3b8', borderWidth: 1 },
        ]);

        // Operator chart (Miyazaki only)
        if (isMiyazaki) {
          const allMu = DataManager.query({ fy: selectedFY, municipality: muni });
          const opAgg = DataManager.aggregate(allMu, 'operator').slice(0, 10);
          if (opAgg.length) {
            ChartManager.hbar('mu-operator-bar',
              opAgg.map(r => r.key.length > 12 ? r.key.slice(0, 12) + '…' : r.key),
              opAgg.map(r => r.amount),
              color);
          }
          $('#mu-operator-table').innerHTML = renderOperatorTable(allMu, 10);

          // Portal & category pie
          const portalAgg = DataManager.aggregate(allMu, 'portal');
          if (portalAgg.length) ChartManager.doughnut('mu-portal-pie', portalAgg.map(r => r.key), portalAgg.map(r => r.amount));
          const catAgg = DataManager.aggregate(allMu, 'category');
          if (catAgg.length) ChartManager.doughnut('mu-cat-pie', catAgg.map(r => r.key), catAgg.map(r => r.amount));
        } else {
          const allMu = DataManager.query({ fy: selectedFY, municipality: muni });
          const portalAgg = DataManager.aggregate(allMu, 'portal');
          if (portalAgg.length) ChartManager.doughnut('mu-portal-pie', portalAgg.map(r => r.key), portalAgg.map(r => r.amount));
          const catAgg = DataManager.aggregate(allMu, 'category');
          if (catAgg.length) ChartManager.doughnut('mu-cat-pie', catAgg.map(r => r.key), catAgg.map(r => r.amount));
        }
      }

      // Monthly table with YoY
      const prevMonthsData = DataManager.fyMonthlySales(selectedFY - 1, muni);
      const rows = months.map((m, i) => {
        const prev   = prevMonthsData[i]?.amount || 0;
        const yoy    = prev > 0 ? ((m.amount - prev) / prev * 100) : null;
        const yoyStr = yoy !== null ? `<span class="${yoy >= 0 ? 'text-success' : 'text-danger'}">${yoy >= 0 ? '+' : ''}${yoy.toFixed(1)}%</span>` : '－';
        const [yy, mm] = m.ym.split('-');
        return `<tr>
          <td>${yy}年${parseInt(mm)}月</td>
          <td class="text-end amount-text">${fmt(m.amount)}</td>
          <td class="text-end">${m.count}</td>
          <td class="text-end">${m.count > 0 ? fmt(Math.round(m.amount / m.count)) : '－'}</td>
          <td class="text-end">${yoyStr}</td>
        </tr>`;
      }).join('');
      $('#mu-table').innerHTML = `<table class="table table-sm mb-0">
        <thead><tr><th>月</th><th class="text-end">売上金額</th><th class="text-end">件数</th>
        <th class="text-end">客単価</th><th class="text-end">前年比</th></tr></thead>
        <tbody>${rows}</tbody>
        <tfoot class="table-light fw-bold"><tr>
          <td>合計</td><td class="text-end">${fmt(totAmt)}</td><td class="text-end">${totCnt}</td>
          <td class="text-end">${totCnt > 0 ? fmt(avg) : '－'}</td><td class="text-end">－</td>
        </tr></tfoot></table>`;
    }

    refresh(fy);
    $('#mu-fy').addEventListener('change', e => refresh(Number(e.target.value)));
  }

  // ── Portal Sales ──────────────────────────────────────────────────────
  function renderPortalSales() {
    const fys  = DataManager.getAvailableFYs();
    const fy   = fys[0] || DataManager.currentFiscalYear();
    const hasSales = DataManager.getSales().length > 0;

    $('#page-content').innerHTML = `
      <div class="filter-bar mb-4">
        <div>
          <label>年度</label>
          <select class="form-select form-select-sm" id="ps-fy" style="width:120px">
            ${fys.map(y => `<option value="${y}" ${y === fy ? 'selected' : ''}>${y}年度</option>`).join('')}
            ${!fys.length ? `<option value="${fy}">${fy}年度</option>` : ''}
          </select>
        </div>
        <div>
          <label>自治体</label>
          <select class="form-select form-select-sm" id="ps-muni" style="width:140px">
            <option value="">全体</option>
            <option value="宮崎市">宮崎市</option>
            <option value="三木町">三木町</option>
          </select>
        </div>
      </div>

      <div class="row g-4 mb-4">
        <div class="col-lg-5">
          <div class="panel">
            <div class="panel-header"><h6 class="panel-title">ポータル別売上</h6></div>
            <div class="panel-body"><div class="chart-container"><canvas id="ps-pie"></canvas></div></div>
          </div>
        </div>
        <div class="col-lg-7">
          <div class="panel">
            <div class="panel-header"><h6 class="panel-title">ポータル別 月次トレンド</h6></div>
            <div class="panel-body">
              ${hasSales ? `<div class="chart-container"><canvas id="ps-trend"></canvas></div>` : noDataHtml()}
            </div>
          </div>
        </div>
      </div>

      <div class="panel">
        <div class="panel-header"><h6 class="panel-title">ポータル別詳細</h6></div>
        <div class="panel-body p-0" id="ps-table"></div>
      </div>`;

    const PORTAL_COLORS = {
      'さとふる': '#ef4444', 'ふるなび': '#3b82f6', '楽天ふるさと納税': '#f97316',
      'ふるさとチョイス': '#22c55e', 'Yahoo!': '#8b5cf6', 'Amazon': '#14b8a6',
      'JAL': '#f59e0b', 'ANA': '#06b6d4',
    };
    const colorFor = (name, i) => PORTAL_COLORS[name] || ['#3b82f6','#f97316','#22c55e','#8b5cf6','#ec4899','#14b8a6'][i % 6];

    function refresh(selectedFY, selectedMuni) {
      const f = { fy: selectedFY };
      if (selectedMuni) f.municipality = selectedMuni;
      const allData = DataManager.query(f);
      const portals = DataManager.aggregate(allData, 'portal');

      if (!portals.length) {
        $('#ps-pie').closest('.panel-body').innerHTML = noDataHtml();
        if (document.getElementById('ps-trend'))
          $('#ps-trend').closest('.panel-body').innerHTML = noDataHtml();
        $('#ps-table').innerHTML = noDataHtml();
        return;
      }

      // Pie
      ChartManager.doughnut('ps-pie', portals.map(r => r.key), portals.map(r => r.amount));

      // Trend: stacked bar by portal
      const months = DataManager.fyMonthlySales(selectedFY, selectedMuni || undefined);
      const portalNames = portals.map(r => r.key);
      const datasets = portalNames.map((p, i) => {
        const c = colorFor(p, i);
        return {
          label: p,
          data: months.map(m => {
            const d = DataManager.query({ ym: m.ym, ...(selectedMuni ? { municipality: selectedMuni } : {}), portal: p });
            return d.reduce((s, r) => s + r.amount, 0);
          }),
          backgroundColor: c + '99',
          borderColor: c,
          borderWidth: 1,
        };
      });
      if (hasSales) ChartManager.bar('ps-trend', months.map(m => m.label), datasets, { stacked: true });

      // Table
      const totAmt = portals.reduce((s, r) => s + r.amount, 0);
      const totCnt = portals.reduce((s, r) => s + r.count, 0);
      const rows = portals.map(r =>
        `<tr>
          <td><span class="dot" style="background:${colorFor(r.key, 0)};display:inline-block;width:8px;height:8px;border-radius:50%;margin-right:6px"></span>${r.key}</td>
          <td class="text-end amount-text">${fmt(r.amount)}</td>
          <td class="text-end">${r.count.toLocaleString()}</td>
          <td class="text-end">${totAmt > 0 ? ((r.amount / totAmt) * 100).toFixed(1) + '%' : '0%'}</td>
          <td class="text-end">${r.count > 0 ? fmt(Math.round(r.amount / r.count)) : '－'}</td>
        </tr>`).join('');
      $('#ps-table').innerHTML = `<table class="table table-sm mb-0">
        <thead><tr><th>ポータル</th><th class="text-end">売上金額</th><th class="text-end">件数</th>
        <th class="text-end">構成比</th><th class="text-end">客単価</th></tr></thead>
        <tbody>${rows}</tbody>
        <tfoot class="table-light fw-bold"><tr>
          <td>合計</td><td class="text-end">${fmt(totAmt)}</td><td class="text-end">${totCnt}</td>
          <td class="text-end">100%</td><td class="text-end">${totCnt > 0 ? fmt(Math.round(totAmt / totCnt)) : '－'}</td>
        </tr></tfoot></table>`;
    }

    refresh(fy, '');
    $('#ps-fy').addEventListener('change', e => refresh(Number(e.target.value), $('#ps-muni').value));
    $('#ps-muni').addEventListener('change', e => refresh(Number($('#ps-fy').value), e.target.value));
  }

  // ── KPI Management ────────────────────────────────────────────────────
  function renderKPIManagement() {
    const fys = DataManager.getAvailableFYs();
    const fy  = fys[0] || DataManager.currentFiscalYear();
    const MUNIS = DataManager.MUNICIPALITIES;

    $('#page-content').innerHTML = `
      <div class="filter-bar mb-4">
        <div>
          <label>年度</label>
          <select class="form-select form-select-sm" id="kp-fy" style="width:120px">
            ${[...new Set([...fys, DataManager.currentFiscalYear(), DataManager.currentFiscalYear() + 1])].sort().reverse()
              .map(y => `<option value="${y}" ${y === fy ? 'selected' : ''}>${y}年度</option>`).join('')}
          </select>
        </div>
        <div>
          <label>自治体</label>
          <select class="form-select form-select-sm" id="kp-muni" style="width:140px">
            ${MUNIS.map(m => `<option value="${m}">${m}</option>`).join('')}
          </select>
        </div>
        <div class="ms-auto">
          <button class="btn btn-primary btn-sm" id="kp-save">
            <i class="bi bi-save me-1"></i>目標を保存
          </button>
        </div>
      </div>

      <div class="row g-4 mb-4">
        <div class="col-12">
          <div class="panel">
            <div class="panel-header"><h6 class="panel-title">実績 vs 目標</h6></div>
            <div class="panel-body"><div class="chart-container"><canvas id="kp-chart"></canvas></div></div>
          </div>
        </div>
      </div>

      <div class="panel mb-4">
        <div class="panel-header"><h6 class="panel-title">月別目標設定・達成状況</h6></div>
        <div class="panel-body p-0" id="kp-table"></div>
      </div>`;

    function buildKpiData(selectedFY, selectedMuni) {
      const fyData  = DataManager.getKPI(selectedFY);
      const muKpi   = fyData[selectedMuni] || {};
      const months  = DataManager.fyMonthlySales(selectedFY, selectedMuni);
      return months.map(m => ({
        ...m,
        salesTarget: muKpi[m.ym]?.salesTarget || 0,
        countTarget: muKpi[m.ym]?.countTarget || 0,
      }));
    }

    function getCurrentFY() { return Number($('#kp-fy').value); }
    function getCurrentMuni() { return $('#kp-muni').value; }

    function refresh() {
      const selectedFY   = getCurrentFY();
      const selectedMuni = getCurrentMuni();
      const data         = buildKpiData(selectedFY, selectedMuni);
      const color        = selectedMuni === '宮崎市' ? '#f97316' : '#8b5cf6';

      ChartManager.kpi(
        'kp-chart',
        data.map(d => d.label),
        data.map(d => d.amount),
        data.map(d => d.salesTarget),
      );

      const rows = data.map((d, i) => {
        const rate = d.salesTarget > 0 ? ((d.amount / d.salesTarget) * 100).toFixed(1) : null;
        const cls  = rate !== null ? achieveClass(Number(rate)) : '';
        const [yy, mm] = d.ym.split('-');
        return `<tr>
          <td>${yy}年${parseInt(mm)}月</td>
          <td><input type="number" class="form-control form-control-sm kp-target-input" data-ym="${d.ym}" data-type="salesTarget"
            value="${d.salesTarget || ''}" placeholder="0" min="0" step="10000" style="width:140px"></td>
          <td class="text-end amount-text">${fmt(d.amount)}</td>
          <td class="text-end">${d.count}</td>
          <td class="text-end">
            ${rate !== null
              ? `<span class="achievement-badge ${cls}">${rate}%</span>`
              : '<span class="text-muted">－</span>'}
          </td>
        </tr>`;
      }).join('');

      const totAmt  = data.reduce((s, d) => s + d.amount, 0);
      const totTgt  = data.reduce((s, d) => s + d.salesTarget, 0);
      const totRate = totTgt > 0 ? ((totAmt / totTgt) * 100).toFixed(1) : null;

      $('#kp-table').innerHTML = `
        <table class="table table-sm mb-0">
          <thead><tr><th>月</th><th>月次目標（円）</th>
          <th class="text-end">実績</th><th class="text-end">件数</th><th class="text-end">達成率</th></tr></thead>
          <tbody>${rows}</tbody>
          <tfoot class="table-light fw-bold"><tr>
            <td>合計</td><td></td><td class="text-end">${fmt(totAmt)}</td><td class="text-end">－</td>
            <td class="text-end">
              ${totRate !== null
                ? `<span class="achievement-badge ${achieveClass(Number(totRate))}">${totRate}%</span>`
                : '－'}
            </td>
          </tr></tfoot>
        </table>`;
    }

    refresh();
    $('#kp-fy').addEventListener('change', refresh);
    $('#kp-muni').addEventListener('change', refresh);

    document.addEventListener('click', e => {
      if (e.target.id === 'kp-save') {
        const selectedFY   = getCurrentFY();
        const selectedMuni = getCurrentMuni();
        const fyData       = DataManager.getKPI(selectedFY);
        if (!fyData[selectedMuni]) fyData[selectedMuni] = {};

        $$('.kp-target-input').forEach(inp => {
          const ym    = inp.dataset.ym;
          const type  = inp.dataset.type;
          const val   = parseInt(inp.value, 10) || 0;
          if (!fyData[selectedMuni][ym]) fyData[selectedMuni][ym] = {};
          fyData[selectedMuni][ym][type] = val;
        });
        DataManager.saveKPI(selectedFY, fyData);
        toast('目標を保存しました', 'success');
        refresh();
      }
    });
  }

  // ── Settings ──────────────────────────────────────────────────────────
  function renderSettings() {
    const sales  = DataManager.getSales();
    const totalB = JSON.stringify(sales).length;
    const sizeKB = (totalB / 1024).toFixed(1);

    $('#page-content').innerHTML = `
      <div class="row g-4">
        <div class="col-lg-6">
          <div class="panel mb-4">
            <div class="panel-header"><h6 class="panel-title">データ管理</h6></div>
            <div class="panel-body">
              <p class="text-muted small mb-3">
                取込済み件数: <strong>${sales.length.toLocaleString()}件</strong>
                （使用容量: 約 ${sizeKB} KB）
              </p>
              <button class="btn btn-outline-danger btn-sm" id="btn-clear-all">
                <i class="bi bi-trash me-1"></i>全データを削除
              </button>
            </div>
          </div>

          <div class="panel">
            <div class="panel-header"><h6 class="panel-title">自治体名マッピング</h6></div>
            <div class="panel-body">
              <p class="text-muted small mb-2">CSVの自治体名列に含まれる値と、システム内の自治体名を対応させます。</p>
              <table class="table table-sm">
                <thead><tr><th>CSVの値</th><th>システムの自治体</th></tr></thead>
                <tbody>
                  <tr><td>宮崎市 / 宮崎県宮崎市</td><td><span class="badge" style="background:#f97316">宮崎市</span></td></tr>
                  <tr><td>三木町 / 香川県三木町</td><td><span class="badge" style="background:#8b5cf6">三木町</span></td></tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div class="col-lg-6">
          <div class="panel mb-4">
            <div class="panel-header"><h6 class="panel-title">インポート履歴</h6></div>
            <div class="panel-body p-0" style="max-height:400px;overflow-y:auto">
              ${DataManager.getHistory().length
                ? `<table class="table table-sm mb-0">
                    <thead><tr><th>ファイル名</th><th>件数</th><th>日時</th></tr></thead>
                    <tbody>${DataManager.getHistory().map(h =>
                      `<tr><td style="max-width:180px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${h.fileName}</td>
                       <td>${h.count.toLocaleString()}</td>
                       <td style="white-space:nowrap">${new Date(h.at).toLocaleString('ja-JP')}</td></tr>`).join('')}
                    </tbody></table>`
                : '<p class="text-muted p-3 small mb-0">履歴なし</p>'}
            </div>
          </div>
        </div>
      </div>`;

    $('#btn-clear-all')?.addEventListener('click', () => {
      if (confirm('すべてのデータ（売上・KPI目標・インポート履歴）を削除します。この操作は取り消せません。よろしいですか？')) {
        DataManager.clearAll();
        toast('全データを削除しました', 'warning');
        setTimeout(() => renderSettings(), 300);
      }
    });
  }

  // ── Init ──────────────────────────────────────────────────────────────
  function init() {
    initNav();
    navigate('dashboard');

    // Sidebar toggle for mobile
    const toggleBtn = document.getElementById('sidebar-toggle');
    if (toggleBtn) {
      toggleBtn.addEventListener('click', () => {
        document.getElementById('sidebar').classList.toggle('open');
      });
    }
  }

  return { init, navigate };
})();

window.addEventListener('DOMContentLoaded', () => App.init());
