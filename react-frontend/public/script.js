let D = null;

    // State
    let activeCountry = null, activeModel = 'rf', mapMode = 'total', mapYear = D.meta.year_end;
    let compareList = [], chatHistory = [], serverOnline = false, busy = false;
    const PAL = ['#00e5b0', '#4da6ff', '#ff4060', '#ffbe4d', '#a78bfa', '#ff9f40', '#7dca5e', '#f06292', '#4dd0e1', '#ffd54f'];
    const C = { bg: 'rgba(0,0,0,0)', surf: 'rgba(13,17,23,.8)', accent: '#00e5b0', red: '#ff4060', amber: '#ffbe4d', blue: '#4da6ff', text: '#9ab0cc', texthi: '#ddeeff', textdim: '#4a6080', grid: '#1e2d42', font: "'JetBrains Mono',monospace" };
    const BL = { paper_bgcolor: C.bg, plot_bgcolor: C.surf, font: { family: C.font, color: C.text, size: 10 }, margin: { l: 44, r: 14, t: 20, b: 32 }, xaxis: { gridcolor: C.grid, zerolinecolor: C.grid, tickfont: { size: 9 } }, yaxis: { gridcolor: C.grid, zerolinecolor: C.grid, tickfont: { size: 9 } } };
    const cfg = { responsive: true, displayModeBar: false };
    const q = id => document.getElementById(id);
    const fn = (v, d = 1) => v == null ? '—' : Number(v).toFixed(d);
    const fp = v => (v >= 0 ? '+' : '') + fn(v, 1) + '%';

    // ── SIDEBAR MOBILE ────────────────────────────────────────────────
    function toggleSidebar() { const sb = q('sidebar'), ov = q('sidebar-overlay'); sb.classList.toggle('mobile-open'); ov.classList.toggle('open'); }
    function closeSidebar() { q('sidebar').classList.remove('mobile-open'); q('sidebar-overlay').classList.remove('open'); }

    // ── TABS ──────────────────────────────────────────────────────────
    const TABS = ['map', 'country', 'compare', 'global', 'aqi', 'explore', 'share', 'chat'];
    function switchTab(name) {
      document.querySelectorAll('.tab-btn').forEach((b, i) => b.classList.toggle('active', TABS[i] === name));
      document.querySelectorAll('.tab-panel').forEach(p => p.classList.toggle('active', p.id === 'tab-' + name));
      q('sb-mode-lbl').textContent = name === 'compare' ? 'Countries (⊕ to compare)' : name === 'aqi' ? 'Select AQI Country' : 'Select Country';
      if (name === 'global') renderGlobal();
      if (name === 'aqi') renderAqi();
      if (name === 'compare') renderCompare();
      if (name === 'map') renderMap();
      if (name === 'chat') checkServer();
      if (name === 'explore') renderExplore();
      if (name === 'share') initShareTab();
      closeSidebar();
    }

    // ── SIDEBAR LIST ──────────────────────────────────────────────────
    function buildList() {
      const list = q('country-list'); list.innerHTML = '';
      D.countries.forEach(c => {
        const co2 = D.per_country[c]?.co2?.at(-1)?.toFixed(0) || '—';
        const el = document.createElement('div'); el.className = 'country-item'; el.dataset.country = c;
        el.innerHTML = `<span class="c-name">${c}</span><span class="c-co2">${co2}</span><span class="c-plus" onclick="event.stopPropagation();toggleCmp('${c.replace(/'/g, "\\'")}')">⊕</span>`;
        el.addEventListener('click', () => { selectCountry(c); closeSidebar(); });
        list.appendChild(el);
      });
      syncSidebar();
    }
    function filterCountries() { const v = q('country-search').value.toLowerCase(); document.querySelectorAll('.country-item').forEach(el => el.style.display = el.dataset.country.toLowerCase().includes(v) ? '' : 'none'); }
    function clearSearch() { q('country-search').value = ''; filterCountries(); }
    function syncSidebar() {
      document.querySelectorAll('.country-item').forEach(el => {
        const c = el.dataset.country;
        el.classList.toggle('active', c === activeCountry);
        el.classList.toggle('in-compare', compareList.includes(c));
        const p = el.querySelector('.c-plus'); if (p) p.textContent = compareList.includes(c) ? '✓' : '⊕';
      });
    }

    // ── COUNTRY DETAIL ────────────────────────────────────────────────
    function selectCountry(c) { activeCountry = c; syncSidebar(); switchTab('country'); renderCountry(); }
    function setModel(m) { activeModel = m; q('btn-rf').classList.toggle('active', m === 'rf'); q('btn-lr').classList.toggle('active', m === 'lr'); if (activeCountry) renderCountry(); }

    function renderCountry() {
      const cd = D.per_country[activeCountry]; if (!cd) { q('country-no-data').style.display = ''; q('country-detail').style.display = 'none'; return; }
      q('country-no-data').style.display = 'none'; q('country-detail').style.display = 'block';
      const ins = cd.insight, fc = activeModel === 'rf' ? cd.rf_forecast : cd.lr_forecast, r2 = activeModel === 'rf' ? cd.rf_r2 : cd.lr_r2, pct = ins.pct_change;
      q('country-title').textContent = activeCountry;
      q('country-subtitle').textContent = `ISO: ${cd.iso || '—'} · ${cd.years[0]}–${cd.years.at(-1)}`;
      q('ckpi-latest').textContent = fn(cd.co2.at(-1), 1); q('ckpi-fc-end').textContent = fn(fc.at(-1), 1);
      q('ckpi-fc-year').textContent = cd.forecast_years.at(-1);
      q('ckpi-change').textContent = fp(pct); q('ckpi-change').className = 'kpi-val ' + (pct > 0 ? 'red' : 'green');
      q('ckpi-risk').textContent = ins.risk; q('ckpi-risk').style.color = ins.risk_color; q('ckpi-r2').textContent = r2.toFixed(3);
      q('ins-head').innerHTML = ins.headline; q('ins-detail').innerHTML = ins.detail; q('ins-rec').innerHTML = ins.recommendation;
      const ch = q('risk-chip'); ch.textContent = ins.risk.toUpperCase(); ch.style.cssText = `background:${ins.risk_color}18;border:1px solid ${ins.risk_color};color:${ins.risk_color}`;
      renderCTrend(cd); renderCGauge(cd); renderCFI(cd); renderCScatter(cd); renderCTable(cd);
    }

    function renderCTrend(cd) {
      const fc = activeModel === 'rf' ? cd.rf_forecast : cd.lr_forecast, fcCol = activeModel === 'rf' ? C.accent : C.amber, tp = activeModel === 'rf' ? cd.rf_test : cd.lr_test;
      const noise = Math.max(...cd.co2) * 0.06;
      const tr = [{ x: cd.years, y: cd.co2, name: 'Actual', mode: 'lines', line: { color: C.texthi, width: 2 }, hovertemplate: '%{x}: <b>%{y:.1f} MT</b><extra>Actual</extra>' }];
      if (cd.test_years?.length && tp?.length) tr.push({ x: cd.test_years, y: tp, name: 'Test fit', mode: 'lines', line: { color: fcCol, width: 1.4, dash: 'dot' } });
      if (activeModel === 'rf') tr.push({ x: [...cd.forecast_years, ...cd.forecast_years.slice().reverse()], y: [...fc.map(v => v + noise), ...fc.map(v => v - noise).reverse()], fill: 'toself', fillcolor: 'rgba(0,229,176,.07)', line: { color: 'transparent' }, hoverinfo: 'skip', showlegend: false });
      tr.push({ x: cd.forecast_years, y: fc, name: activeModel === 'rf' ? 'RF Forecast' : 'LR Forecast', mode: 'lines+markers', line: { color: fcCol, width: 2.2 }, marker: { size: 6, color: fcCol }, hovertemplate: '%{x}: <b>%{y:.1f} MT</b><extra>Forecast</extra>' });
      Plotly.react('chart-country-trend', tr, { ...BL, yaxis: { ...BL.yaxis, title: 'MT CO₂' }, legend: { bgcolor: 'rgba(0,0,0,0)', font: { size: 9 } }, hovermode: 'x unified', shapes: [{ type: 'line', x0: cd.forecast_years[0], x1: cd.forecast_years[0], y0: 0, y1: 1, yref: 'paper', line: { color: C.red, width: 1, dash: 'dot' } }], annotations: [{ x: cd.forecast_years[0], y: 1, yref: 'paper', xanchor: 'left', showarrow: false, text: ' Forecast →', font: { color: C.red, size: 9, family: C.font } }] }, cfg);
    }
    function renderCGauge(cd) {
      const val = cd.co2.at(-1) || 0, maxV = Math.max(...cd.co2) * 1.2, p = val / maxV, col = p > .75 ? C.red : p > .5 ? C.amber : C.accent;
      Plotly.react('chart-country-gauge', [{ type: 'indicator', mode: 'gauge+number', value: val, number: { suffix: ' MT', font: { size: 20, family: C.font, color: C.texthi } }, gauge: { axis: { range: [0, maxV], tickfont: { size: 8, family: C.font } }, bar: { color: col }, bgcolor: 'rgba(0,0,0,0)', borderwidth: 0, steps: [{ range: [0, maxV * .5], color: 'rgba(0,229,176,.05)' }, { range: [maxV * .5, maxV * .75], color: 'rgba(255,190,77,.05)' }, { range: [maxV * .75, maxV], color: 'rgba(255,64,96,.08)' }] }, title: { text: 'Latest CO₂', font: { family: C.font, color: C.textdim, size: 10 } } }], { ...BL, margin: { l: 14, r: 14, t: 24, b: 8 } }, cfg);
    }
    function renderCFI(cd) {
      const LBL = { year: 'Year Trend', energy_per_capita: 'Energy/Cap', gdp_per_capita: 'GDP/Cap', population: 'Population' };
      const items = Object.entries(cd.feature_importances).sort((a, b) => a[1] - b[1]);
      const mx = Math.max(...items.map(([, v]) => v));
      Plotly.react('chart-country-fi', [{ type: 'bar', orientation: 'h', x: items.map(([, v]) => v), y: items.map(([k]) => LBL[k] || k), marker: { color: items.map(([, v]) => v === mx ? C.accent : '#1e3050') }, text: items.map(([, v]) => v.toFixed(3)), textfont: { family: C.font, color: C.text, size: 9 }, textposition: 'outside' }], { ...BL, margin: { l: 6, r: 44, t: 10, b: 16 }, xaxis: { ...BL.xaxis, visible: false }, yaxis: { ...BL.yaxis, tickfont: { size: 9, family: C.font } } }, cfg);
    }
    function renderCScatter(cd) {
      const act = cd.co2.slice(cd.co2.length - cd.rf_test.length), lo = Math.min(...act, 0.1), hi = Math.max(...act);
      Plotly.react('chart-country-scatter', [{ x: act, y: cd.rf_test, mode: 'markers', name: 'RF', marker: { color: C.accent, size: 5, opacity: .8 } }, { x: act, y: cd.lr_test, mode: 'markers', name: 'LR', marker: { color: C.amber, size: 5, opacity: .7 } }, { x: [lo, hi], y: [lo, hi], mode: 'lines', showlegend: false, line: { color: C.red, dash: 'dash', width: 1 } }], { ...BL, margin: { l: 40, r: 10, t: 10, b: 32 }, xaxis: { ...BL.xaxis, title: 'Actual' }, yaxis: { ...BL.yaxis, title: 'Predicted' }, legend: { bgcolor: 'rgba(0,0,0,0)', font: { size: 9 } } }, cfg);
    }
    function renderCTable(cd) {
      const tb = q('fc-table-body'); tb.innerHTML = '';
      const mx = Math.max(...cd.rf_forecast), mn = Math.min(...cd.rf_forecast);
      cd.forecast_years.forEach((yr, i) => {
        const rv = cd.rf_forecast[i], lv = cd.lr_forecast[i], hi = rv === mx, lo = rv === mn;
        const tr = document.createElement('tr');
        tr.innerHTML = `<td style="padding:7px 10px;border-bottom:1px solid var(--border);color:var(--textdim)">${yr}</td><td style="padding:7px 10px;border-bottom:1px solid var(--border);color:var(--accent);${hi ? 'background:rgba(255,64,96,.08)' : lo ? 'background:rgba(0,229,176,.06)' : ''}">${fn(rv, 2)}</td><td style="padding:7px 10px;border-bottom:1px solid var(--border);color:var(--amber)">${fn(lv, 2)}</td>`;
        tb.appendChild(tr);
      });
    }

    // ── COMPARE ───────────────────────────────────────────────────────
    function toggleCmp(c) { if (compareList.includes(c)) compareList = compareList.filter(x => x !== c); else { if (compareList.length >= 4) { alert('Max 4 countries.'); return; } compareList.push(c); } syncSidebar(); updateChips(); if (q('tab-compare').classList.contains('active')) renderCompare(); }
    function clearCompare() { compareList = []; syncSidebar(); updateChips(); renderCompare(); }
    function updateChips() { const box = q('cmp-chips'); if (!compareList.length) { box.innerHTML = '<span class="cmp-hint">No countries selected</span>'; return; } box.innerHTML = compareList.map((c, i) => `<div class="cmp-chip" style="background:${PAL[i]}18;border-color:${PAL[i]};color:${PAL[i]}"><span>${c}</span><button class="chip-x" style="color:${PAL[i]}" onclick="toggleCmp('${c.replace(/'/g, "\\'")}')">✕</button></div>`).join(''); }
    function filterCmpDd() { renderCmpDdList(q('cmp-input').value.toLowerCase()); }
    function openCmpDd() { renderCmpDdList(q('cmp-input').value.toLowerCase()); q('cmp-dd-list').classList.add('open'); }
    function closeCmpDd() { q('cmp-dd-list').classList.remove('open'); }
    function renderCmpDdList(f) { const list = q('cmp-dd-list'); const m = D.countries.filter(c => c.toLowerCase().includes(f)).slice(0, 14); list.innerHTML = m.map(c => { const inn = compareList.includes(c), co2 = D.per_country[c]?.co2?.at(-1)?.toFixed(0) || '—'; return `<div class="cmp-dd-item${inn ? ' disabled' : ''}" onclick="${inn ? '' : ` addCmp('${c.replace(/'/g, "\\'")}') `}">${inn ? '✓ ' : ''}${c}<span class="ddval">${co2} MT</span></div>`; }).join(''); list.classList.add('open'); }
    function addCmp(c) { if (compareList.length >= 4) { alert('Max 4.'); return; } if (!compareList.includes(c)) compareList.push(c); syncSidebar(); updateChips(); q('cmp-input').value = ''; closeCmpDd(); renderCompare(); }

    function renderCompare() { const ok = compareList.length >= 2; q('cmp-placeholder').style.display = ok ? 'none' : ''; q('cmp-content').style.display = ok ? 'block' : 'none'; if (!ok) return; renderCmpTrend(); renderCmpLatest(); renderCmpFc(); renderCmpRadar(); renderCmpTable(); renderCmpPct(); }
    function renderCmpTrend() { const tr = []; compareList.forEach((c, i) => { const cd = D.per_country[c]; if (!cd) return; tr.push({ x: cd.years, y: cd.co2, name: c, mode: 'lines', line: { color: PAL[i], width: 2 }, hovertemplate: `${c} %{x}: <b>%{y:.1f} MT</b><extra></extra>` }); tr.push({ x: cd.forecast_years, y: cd.rf_forecast, name: `${c} (fc)`, mode: 'lines+markers', line: { color: PAL[i], width: 1.8, dash: 'dash' }, marker: { size: 5, color: PAL[i] }, showlegend: false, hovertemplate: `${c} Fc %{x}: <b>%{y:.1f} MT</b><extra></extra>` }); }); const fy = D.per_country[compareList[0]]?.forecast_years; Plotly.react('chart-cmp-trend', tr, { ...BL, yaxis: { ...BL.yaxis, title: 'MT CO₂' }, legend: { bgcolor: 'rgba(0,0,0,0)', font: { size: 10 }, orientation: 'h', x: 0, y: 1.1 }, hovermode: 'x unified', shapes: fy ? [{ type: 'line', x0: fy[0], x1: fy[0], y0: 0, y1: 1, yref: 'paper', line: { color: 'rgba(255,255,255,.18)', width: 1, dash: 'dot' } }] : [] }, cfg); }
    function renderCmpLatest() { const names = [], vals = [], cols = []; compareList.forEach((c, i) => { const cd = D.per_country[c]; if (!cd) return; names.push(c); vals.push(cd.co2.at(-1) || 0); cols.push(PAL[i]); }); Plotly.react('chart-cmp-latest', [{ type: 'bar', x: names, y: vals, marker: { color: cols }, text: vals.map(v => fn(v, 1) + ' MT'), textfont: { family: C.font, size: 10, color: C.texthi }, textposition: 'outside', hovertemplate: '%{x}: <b>%{y:.1f} MT</b><extra></extra>' }], { ...BL, margin: { l: 44, r: 14, t: 24, b: 54 }, yaxis: { ...BL.yaxis, title: 'MT CO₂' }, xaxis: { ...BL.xaxis, tickangle: -15 } }, cfg); }
    function renderCmpFc() { const fy = D.per_country[compareList[0]]?.forecast_years || []; const tr = compareList.map((c, i) => { const cd = D.per_country[c]; if (!cd) return null; return { type: 'bar', name: c, x: fy.map(String), y: cd.rf_forecast, marker: { color: PAL[i] }, hovertemplate: `${c} %{x}: <b>%{y:.1f} MT</b><extra></extra>` }; }).filter(Boolean); Plotly.react('chart-cmp-fc', tr, { ...BL, barmode: 'group', yaxis: { ...BL.yaxis, title: 'MT CO₂' }, legend: { bgcolor: 'rgba(0,0,0,0)', font: { size: 9 }, orientation: 'h', x: 0, y: 1.1 }, margin: { l: 44, r: 14, t: 24, b: 32 } }, cfg); }
    function renderCmpRadar() { const allCo2 = compareList.map(c => D.per_country[c]?.co2?.at(-1) || 0); const allPct = compareList.map(c => Math.abs(D.per_country[c]?.insight?.pct_change || 0)); const allR2 = compareList.map(c => Math.max(0, D.per_country[c]?.rf_r2 || 0)); const allPcap = compareList.map(c => D.per_country[c]?.co2_per_capita?.at(-1) || 0); const norm = (arr, v) => Math.max(...arr) > 0 ? v / Math.max(...arr) : 0; const theta = ['CO₂ Level', 'Forecast Δ', 'Model R²', 'Per Capita', 'CO₂ Level']; const tr = compareList.map((c, i) => { const r = [norm(allCo2, allCo2[i]), norm(allPct, allPct[i]), norm(allR2, allR2[i]), norm(allPcap, allPcap[i]), norm(allCo2, allCo2[i])]; return { type: 'scatterpolar', r, theta, fill: 'toself', fillcolor: PAL[i] + '22', name: c, line: { color: PAL[i], width: 2 } }; }); Plotly.react('chart-cmp-radar', tr, { ...BL, polar: { bgcolor: C.surf, radialaxis: { visible: true, range: [0, 1], tickfont: { size: 8, family: C.font }, gridcolor: C.grid }, angularaxis: { tickfont: { size: 9, family: C.font }, gridcolor: C.grid } }, margin: { l: 36, r: 36, t: 26, b: 26 }, legend: { bgcolor: 'rgba(0,0,0,0)', font: { size: 9 }, x: 0, y: 1.12, orientation: 'h' } }, cfg); }
    function renderCmpTable() { const tb = q('cmp-tbody'); tb.innerHTML = ''; compareList.forEach((c, i) => { const cd = D.per_country[c]; if (!cd) return; const pct = cd.insight.pct_change, pCol = pct > 0 ? C.red : C.accent, rCol = cd.insight.risk_color; const tr = document.createElement('tr'); tr.innerHTML = `<td><span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:${PAL[i]};margin-right:6px;vertical-align:middle"></span><strong style="color:${PAL[i]}">${c}</strong></td><td class="td-mono">${fn(cd.co2.at(-1), 1)}</td><td class="td-mono">${fn(cd.rf_forecast.at(-1), 1)}</td><td class="td-mono" style="color:${pCol}">${fp(pct)}</td><td class="td-mono">${cd.rf_r2.toFixed(3)}</td><td><span style="background:${rCol}18;border:1px solid ${rCol};color:${rCol};padding:2px 7px;border-radius:12px;font-family:var(--mono);font-size:9px">${cd.insight.risk}</span></td>`; tb.appendChild(tr); }); }
    function renderCmpPct() { const box = q('cmp-pct-bars'); box.innerHTML = ''; const pcts = compareList.map(c => D.per_country[c]?.insight?.pct_change || 0); const mx = Math.max(...pcts.map(Math.abs), 0.1); compareList.forEach((c, i) => { const pct = pcts[i], bW = (Math.abs(pct) / mx * 100).toFixed(1), bC = pct > 0 ? C.red : C.accent; box.innerHTML += `<div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;font-size:11px"><span style="width:80px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;color:${PAL[i]}">${c}</span><div style="flex:1;height:6px;background:var(--s3);border-radius:3px"><div style="width:${bW}%;height:100%;background:${bC};border-radius:3px"></div></div><span style="font-family:var(--mono);font-size:10px;color:${bC};width:44px;text-align:right">${(pct >= 0 ? '+' : '') + pct.toFixed(1)}%</span></div>`; }); }

    // ── AQI INDEX ────────────────────────────────────────────────────
    let aqiDone = false;
    const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
    const latest = (cd, key) => cd?.[key]?.filter(v => v != null).at(-1) || 0;
    function aqiCategory(score) { return score <= 50 ? 'Good' : score <= 100 ? 'Moderate' : score <= 150 ? 'Sensitive' : score <= 200 ? 'Unhealthy' : 'Very Unhealthy'; }
    function aqiColor(score) { return score <= 50 ? '#18b96f' : score <= 100 ? '#b7d936' : score <= 150 ? C.amber : score <= 200 ? '#ff6b35' : '#b91c1c'; }
    function aqiForCountry(country) {
      const cd = D.per_country[country] || {};
      const maxCo2 = Math.max(...D.countries.map(c => latest(D.per_country[c], 'co2')), 1);
      const maxPc = Math.max(...D.countries.map(c => latest(D.per_country[c], 'co2_per_capita')), 1);
      const maxEnergy = Math.max(...D.countries.map(c => latest(D.per_country[c], 'energy_pc')), 1);
      const maxGrowth = Math.max(...D.countries.map(c => Math.max(0, D.per_country[c]?.insight?.pct_change || 0)), 1);
      const total = latest(cd, 'co2') / maxCo2;
      const perCapita = latest(cd, 'co2_per_capita') / maxPc;
      const energy = latest(cd, 'energy_pc') / maxEnergy;
      const growth = Math.max(0, cd.insight?.pct_change || 0) / maxGrowth;
      const score = Math.round(25 + 275 * clamp(total * .28 + perCapita * .34 + energy * .24 + growth * .14, 0, 1));
      return { score, category: aqiCategory(score), color: aqiColor(score), total, perCapita, energy, growth };
    }
    function rankedAqi() { return D.countries.map(c => ({ country: c, ...aqiForCountry(c) })).sort((a, b) => b.score - a.score); }
    function renderAqi() {
      if (!activeCountry && D.countries.length) activeCountry = D.countries[0];
      const rows = rankedAqi(), selected = aqiForCountry(activeCountry), avg = Math.round(rows.reduce((s, r) => s + r.score, 0) / Math.max(rows.length, 1)), improving = D.countries.filter(c => (D.per_country[c]?.insight?.pct_change || 0) < 0).length;
      q('aqikpi-avg').textContent = avg; q('aqikpi-high').textContent = rows[0]?.score || '—'; q('aqikpi-high-name').textContent = rows[0]?.country || '—'; q('aqikpi-cleaner').textContent = improving; q('aqikpi-selected').textContent = selected.score; q('aqikpi-selected-cat').textContent = selected.category;
      q('aqi-country').textContent = activeCountry || '—'; q('aqi-score').textContent = selected.score; q('aqi-category').textContent = selected.category;
      q('aqi-ring').style.background = `conic-gradient(${selected.color} ${selected.score / 300 * 360}deg, var(--s3) 0deg)`;
      q('aqi-explain').innerHTML = `Built as an <strong>estimated AQI-style index</strong> from CO₂ level, CO₂ per person, energy use per person, and forecast growth. It is a comparative dashboard signal, not live pollutant monitoring.`;
      const top = rows.slice(0, 12).reverse();
      Plotly.react('chart-aqi-rank', [{ type: 'bar', orientation: 'h', x: top.map(r => r.score), y: top.map(r => r.country), marker: { color: top.map(r => r.color) }, text: top.map(r => r.category), textposition: 'auto', hovertemplate: '<b>%{y}</b><br>AQI: %{x}<extra></extra>' }], { ...BL, margin: { l: 104, r: 16, t: 12, b: 28 }, xaxis: { ...BL.xaxis, range: [0, 300], title: 'Estimated AQI' } }, cfg);
      Plotly.react('chart-aqi-map', [{ type: 'choropleth', locationmode: 'ISO-3', locations: D.map.iso, z: D.map.country.map(c => aqiForCountry(c).score), text: D.map.country, zmin: 0, zmax: 300, colorscale: [[0, '#18b96f'], [.25, '#b7d936'], [.5, '#ffbe4d'], [.7, '#ff6b35'], [1, '#b91c1c']], colorbar: { title: { text: 'AQI', font: { size: 9, family: C.font, color: C.text } }, tickfont: { size: 9, family: C.font, color: C.text } }, hovertemplate: '<b>%{text}</b><br>Estimated AQI: %{z}<extra></extra>', marker: { line: { color: C.grid, width: .5 } } }], { ...BL, margin: { l: 0, r: 0, t: 4, b: 4 }, geo: { showframe: false, showcoastlines: true, coastlinecolor: C.grid, bgcolor: C.bg, landcolor: '#111c2b', oceancolor: '#060b14', showocean: true, projection: { type: 'natural earth' } } }, cfg);
      q('aqi-table-body').innerHTML = rows.slice(0, 10).map((r, i) => `<tr onclick="selectCountry('${r.country.replace(/'/g, "\\'")}');switchTab('aqi')" style="cursor:pointer"><td style="color:var(--textdim);font-family:var(--mono)">#${i + 1}</td><td><strong style="color:var(--texthi)">${r.country}</strong></td><td style="font-family:var(--mono);color:${r.color}">${r.score}</td><td>${r.category}</td><td style="color:var(--textdim)">CO₂ ${fn(latest(D.per_country[r.country], 'co2'), 0)} MT · ${fn(latest(D.per_country[r.country], 'co2_per_capita'), 2)} t/person</td></tr>`).join('');
      updateMixer();
      aqiDone = true;
    }
    function updateMixer() {
      const base = aqiForCountry(activeCountry || D.countries[0]).score;
      const e = +q('mix-energy').value, p = +q('mix-power').value, t = +q('mix-transport').value;
      q('mix-energy-v').textContent = e + '%'; q('mix-power-v').textContent = p + '%'; q('mix-transport-v').textContent = t + '%';
      const reduction = e * .36 + p * .42 + t * .22, score = Math.max(15, Math.round(base * (1 - reduction / 100)));
      q('mix-score').textContent = score; q('mix-score').style.color = aqiColor(score); q('mix-bar').style.width = `${clamp(score / 300 * 100, 2, 100)}%`; q('mix-bar').style.background = aqiColor(score);
      q('mix-note').textContent = `${activeCountry || D.countries[0]} could move from ${base} (${aqiCategory(base)}) to ${score} (${aqiCategory(score)}) under this scenario.`;
    }
    function askAqiAboutCountry() { useSugg(`Explain the estimated AQI index for ${activeCountry}. What drives it and what policies would improve it?`); }

    // ── MAP ───────────────────────────────────────────────────────────
    function setMapMode(m) { mapMode = m; q('map-mode-total').classList.toggle('active', m === 'total'); q('map-mode-percap').classList.toggle('active', m === 'percap'); q('map-mode-aqi').classList.toggle('active', m === 'aqi'); renderMap(); }
    function onMapYearChange() { mapYear = parseInt(q('map-year-slider').value); q('map-year-val').textContent = mapYear; renderMap(); }
    function getMapYearData() { const av = Object.keys(D.year_map).map(Number).sort((a, b) => a - b); const nr = av.reduce((a, b) => Math.abs(b - mapYear) < Math.abs(a - mapYear) ? b : a); return D.year_map[String(nr)] || D.map; }
    function renderMap() { const yd = mapMode === 'aqi' ? D.map : getMapYearData(), vals = mapMode === 'aqi' ? yd.country.map(c => aqiForCountry(c).score) : mapMode === 'percap' && D.map.co2_per_capita ? D.map.co2_per_capita : yd.co2, title = mapMode === 'aqi' ? 'Estimated AQI' : mapMode === 'percap' ? 'CO₂/Capita' : 'Total CO₂ (MT)', scale = mapMode === 'aqi' ? [[0, '#18b96f'], [.25, '#b7d936'], [.5, '#ffbe4d'], [.7, '#ff6b35'], [1, '#b91c1c']] : [[0, '#0d2f1a'], [.15, '#0a4a2a'], [.35, '#1a7a40'], [.55, '#f5a623'], [.75, '#e8460a'], [1, '#8b0000']]; Plotly.react('chart-map', [{ type: 'choropleth', locationmode: 'ISO-3', locations: yd.iso, z: vals, text: yd.country, colorscale: scale, zmin: mapMode === 'aqi' ? 0 : undefined, zmax: mapMode === 'aqi' ? 300 : undefined, showscale: true, colorbar: { title: { text: title, font: { size: 9, family: C.font, color: C.text } }, tickfont: { size: 9, family: C.font, color: C.text }, bgcolor: C.bg, bordercolor: C.grid, len: .8 }, hovertemplate: '<b>%{text}</b><br>' + title + ': %{z:.1f}<extra></extra>', marker: { line: { color: C.grid, width: .5 } } }], { ...BL, margin: { l: 0, r: 0, t: 4, b: 4 }, geo: { showframe: false, showcoastlines: true, coastlinecolor: C.grid, bgcolor: C.bg, landcolor: '#111c2b', oceancolor: '#060b14', showocean: true, projection: { type: 'natural earth' }, lataxis: { range: [-75, 85] } } }, cfg); }
    function renderTop10List() { const top10 = D.global.top10_countries, vals = top10.map(c => D.global.top10[c]?.co2?.at(-1) || 0), mx = Math.max(...vals); const list = q('top10-list'); list.innerHTML = ''; top10.forEach((c, i) => { const v = vals[i]; const el = document.createElement('div'); el.className = 'emitter-row'; el.innerHTML = `<span class="emitter-rank">${i + 1}</span><span class="emitter-name" onclick="selectCountry('${c}')">${c}</span><div class="emitter-bar-wrap"><div class="emitter-bar" style="width:${(v / mx * 100).toFixed(1)}%;background:${PAL[i]}"></div></div><span class="emitter-val">${fn(v, 0)}</span>`; list.appendChild(el); }); }
    function renderTop10Trend() { const tr = D.global.top10_countries.map((c, i) => ({ x: D.global.top10[c].years, y: D.global.top10[c].co2, name: c, mode: 'lines', line: { color: PAL[i], width: 1.8 }, hovertemplate: `${c} %{x}: <b>%{y:.1f}</b><extra></extra>` })); Plotly.react('chart-top10', tr, { ...BL, yaxis: { ...BL.yaxis, title: 'MT CO₂' }, legend: { bgcolor: 'rgba(0,0,0,0)', font: { size: 8 }, x: 0, y: 1.08, orientation: 'h' }, hovermode: 'x unified' }, cfg); }
    function renderMapKPIs() { q('kpi-global-total').textContent = fn(D.global.total_co2.at(-1), 0); q('kpi-top-emitter').textContent = D.global.top10_countries[0]; q('kpi-top-emitter-val').textContent = fn(D.global.top10[D.global.top10_countries[0]]?.co2?.at(-1), 0) + ' MT'; q('kpi-n-countries').textContent = D.meta.n_countries; q('kpi-year-range').textContent = D.meta.year_start + '–' + D.meta.year_end; q('kpi-data-year').textContent = D.meta.year_end; const av = Object.keys(D.year_map).map(Number).sort((a, b) => a - b); const sl = q('map-year-slider'); sl.min = av[0]; sl.max = av.at(-1); sl.value = av.at(-1); q('map-year-val').textContent = av.at(-1); }

    // ── GLOBAL ────────────────────────────────────────────────────────
    let gDone = false;
    function renderGlobal() { if (gDone) return; gDone = true; const g = D.global, v0 = g.total_co2[0], vn = g.total_co2.at(-1), pct = ((vn - v0) / v0) * 100; q('gkpi-1990').textContent = fn(v0, 0); q('gkpi-latest').textContent = fn(vn, 0); q('gkpi-growth').textContent = (pct >= 0 ? '+' : '') + pct.toFixed(1) + '%'; q('gkpi-countries').textContent = D.meta.n_countries; Plotly.react('chart-global-total', [{ x: g.years, y: g.total_co2, mode: 'lines', line: { color: C.accent, width: 2.5 }, fill: 'tozeroy', fillcolor: 'rgba(0,229,176,.06)', hovertemplate: '%{x}: <b>%{y:.0f} MT</b><extra>Global</extra>' }], { ...BL, yaxis: { ...BL.yaxis, title: 'MT CO₂' }, hovermode: 'x unified', margin: { l: 56, r: 14, t: 16, b: 32 } }, cfg); const top10 = g.top10_countries, lv = top10.map(c => g.top10[c]?.co2?.at(-1) || 0), oth = Math.max(0, vn - lv.reduce((a, b) => a + b, 0)); Plotly.react('chart-top10-pie', [{ type: 'pie', labels: [...top10, 'Rest of World'], values: [...lv, oth], marker: { colors: [...PAL, '#2a3a54'] }, textfont: { family: C.font, size: 9 }, hovertemplate: '<b>%{label}</b><br>%{value:.0f} MT · %{percent}<extra></extra>', hole: .38 }], { ...BL, margin: { l: 10, r: 10, t: 10, b: 10 }, legend: { bgcolor: 'rgba(0,0,0,0)', font: { size: 9 }, x: 1, y: .5 } }, cfg); const tr10 = top10.map((c, i) => ({ x: g.top10[c].years, y: g.top10[c].co2, name: c, mode: 'lines', line: { color: PAL[i], width: 1.8 }, hovertemplate: `${c} %{x}: <b>%{y:.1f}</b><extra></extra>` })); Plotly.react('chart-global-lines', tr10, { ...BL, yaxis: { ...BL.yaxis, title: 'MT CO₂' }, legend: { bgcolor: 'rgba(0,0,0,0)', font: { size: 8 }, x: 0, y: 1.08, orientation: 'h' }, hovermode: 'x unified' }, cfg); }

    // ── CHAT ──────────────────────────────────────────────────────────
    const CHAT_URL = 'http://localhost:5000';
    const SUGGESTIONS = ['🌍 Which country emits the most CO₂?', '🌫️ Which countries have the highest estimated AQI?', '📈 Compare China vs India vs USA', '📉 Countries reducing emissions?', '🔢 Current global total CO₂?', '🚀 Fastest growing emitter?', '🇩🇪 What drives Germany\\'s emissions?', '🌿 Net zero — which countries are closest?'];
    function buildSugg() { const grid = q('sugg-grid'); grid.innerHTML = ''; SUGGESTIONS.forEach(s => { const btn = document.createElement('button'); btn.className = 'sugg-btn'; btn.type = 'button'; btn.textContent = s; btn.addEventListener('click', () => useSugg(s)); grid.appendChild(btn); }); }
    function useSugg(t) { switchTab('chat'); const inp = q('chat-input'); inp.value = t; inp.focus(); if (serverOnline) sendMsg(); }
    function chatKey(e) { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMsg(); } }
    async function checkServer() { const dot = q('chat-dot'), txt = q('chat-status'), btn = q('btn-send'); dot.className = 'sdot checking'; txt.textContent = 'Checking…'; try { const r = await fetch(CHAT_URL + '/ping', { signal: AbortSignal.timeout(3000) }); const d = await r.json(); if (d.status === 'ok') { dot.className = 'sdot online'; txt.textContent = 'AI Chat — Online ✓'; txt.style.color = 'var(--accent)'; btn.disabled = false; serverOnline = true; } } catch (e) { dot.className = 'sdot offline'; txt.textContent = 'Server offline — check Flask backend'; txt.style.color = 'var(--red)'; btn.disabled = true; serverOnline = false; } }
    function dataSummary() { const out = { meta: D.meta, global: { total_1990: D.global.total_co2[0], total_latest: D.global.total_co2.at(-1), top10: D.global.top10_countries }, countries: {} }; D.countries.forEach(c => { const cd = D.per_country[c]; if (!cd) return; out.countries[c] = { iso: cd.iso, latest_co2: cd.co2.at(-1), estimated_aqi: aqiForCountry(c).score, aqi_category: aqiForCountry(c).category, forecast_end: cd.rf_forecast.at(-1), pct_change: cd.insight?.pct_change, risk: cd.insight?.risk, rf_r2: cd.rf_r2, top_driver: cd.insight?.top_factor }; }); return JSON.stringify(out); }
    function systemPrompt() { return `You are an expert climate data analyst for a Carbon Emission Dashboard.\nYou have CO₂ data for ${D.meta.n_countries} countries (${D.meta.year_start}–${D.meta.year_end}) with ${D.meta.forecast_years}-year ML forecasts and an estimated AQI-style index derived from CO₂, CO₂ per capita, energy per capita, and forecast growth.\n\nDATA:\n${dataSummary()}\n\nRules: Use exact numbers from data. Be concise. Use **bold** for key names/numbers. Use bullet lists for comparisons. State clearly that AQI values are estimated dashboard signals, not live pollutant readings.`; }
    function addBubble(role, html) { const msgs = q('chat-messages'); const div = document.createElement('div'); div.className = `bubble ${role}`; const lbl = role === 'user' ? 'You' : role === 'ai' ? 'Carbon AI' : ''; if (lbl) div.innerHTML = `<div class="bubble-lbl">${lbl}</div>`; if (role === 'ai') div.innerHTML += md(html); else if (role === 'user') div.innerHTML += esc(html); else div.innerHTML += html; msgs.insertBefore(div, q('typing')); msgs.scrollTop = msgs.scrollHeight; }
    function showTyping() { q('typing').style.display = 'block'; q('chat-messages').scrollTop = q('chat-messages').scrollHeight; }
    function hideTyping() { q('typing').style.display = 'none'; }
    function clearChat() { chatHistory = []; q('chat-messages').querySelectorAll('.bubble:not(:first-child)').forEach(b => b.remove()); hideTyping(); }
    function esc(t) { return t.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
    function md(t) { return esc(t).replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>').replace(/\*(.+?)\*/g, '<em>$1</em>').replace(/`(.+?)`/g, '<code style="font-family:var(--mono);font-size:11px;background:var(--s3);padding:1px 5px;border-radius:3px">$1</code>').replace(/^- (.+)$/gm, '<li>$1</li>').replace(/(<li>[\s\S]*?<\/li>)+/g, '<ul style="margin:6px 0 6px 16px">$&</ul>').replace(/\n\n/g, '<br/><br/>').replace(/\n/g, '<br/>'); }
    async function sendMsg() { if (busy) return; const inp = q('chat-input'), msg = inp.value.trim(); if (!msg) return; if (!serverOnline) { addBubble('err', '⚠️ Server offline. Please ensure the Flask backend is running.'); return; } busy = true; q('btn-send').disabled = true; addBubble('user', msg); inp.value = ''; showTyping(); const messages = [...chatHistory, { role: 'user', content: msg }]; try { const r = await fetch(CHAT_URL + '/chat', { credentials: 'include',  method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ model: 'gemini-2.5-flash', max_tokens: 1024, system: systemPrompt(), messages }) }); const data = await r.json(); if (data.error) throw new Error(data.error); const reply = data.content?.find(b => b.type === 'text')?.text || 'No response.'; chatHistory.push({ role: 'user', content: msg }, { role: 'assistant', content: reply }); if (chatHistory.length > 20) chatHistory = chatHistory.slice(-20); hideTyping(); addBubble('ai', reply); } catch (e) { hideTyping(); addBubble('err', `❌ ${esc(e.message)}`); } finally { busy = false; q('btn-send').disabled = false; inp.focus(); } }

    // ── DATA EXPLORATION ──────────────────────────────────────────────
    let expSortKey = 'co2', expSortDir = 'desc';

    function getMetricVal(cd, metric, yearIdx) {
      const arr = metric === 'co2' ? cd.co2 : metric === 'co2_per_capita' ? cd.co2_per_capita : metric === 'energy_pc' ? cd.energy_pc : metric === 'gdp_pc' ? cd.gdp_pc : cd.population;
      if (!arr || yearIdx >= arr.length) return null;
      return arr[yearIdx];
    }
    function getMetricLabel(metric) {
      return { co2: 'CO₂ (MT)', co2_per_capita: 'CO₂ per Capita (t)', energy_pc: 'Energy per Cap (kWh)', gdp_pc: 'GDP per Cap (USD)', population: 'Population' }[metric] || metric;
    }
    function expSortBy(col) {
      if (expSortKey === col) expSortDir = expSortDir === 'asc' ? 'desc' : 'asc';
      else { expSortKey = col; expSortDir = col === 'name' ? 'asc' : 'desc'; }
      renderExplore();
    }
    function resetExploreFilters() {
      q('exp-metric').value = 'co2'; q('exp-year').value = 2023; q('exp-year-val').textContent = '2023';
      q('exp-risk').value = 'all'; q('exp-sort').value = 'co2_desc'; expSortKey = 'co2'; expSortDir = 'desc';
      renderExplore();
    }
    function renderExplore() {
      const metric = q('exp-metric').value, year = parseInt(q('exp-year').value);
      const riskFilter = q('exp-risk').value, sortMode = q('exp-sort').value;
      q('exth-metric').textContent = getMetricLabel(metric);
      let rows = [];
      D.countries.forEach(c => {
        const cd = D.per_country[c]; if (!cd) return;
        const yearIdx = cd.years.indexOf(year);
        const metricVal = yearIdx >= 0 ? getMetricVal(cd, metric, yearIdx) : null;
        const co2Val = yearIdx >= 0 ? (cd.co2[yearIdx] || null) : null;
        const ins = cd.insight || {}; const risk = ins.risk || 'Unknown';
        if (riskFilter !== 'all' && risk !== riskFilter) return;
        rows.push({ name: c, metric: metricVal, co2: co2Val, pct: ins.pct_change ?? 0, r2: cd.rf_r2 ?? 0, risk, riskColor: ins.risk_color || '#666' });
      });
      if (sortMode === 'co2_desc') rows.sort((a, b) => (b.co2||0)-(a.co2||0));
      else if (sortMode === 'co2_asc') rows.sort((a, b) => (a.co2||0)-(b.co2||0));
      else if (sortMode === 'pct_asc') rows.sort((a, b) => a.pct-b.pct);
      else if (sortMode === 'pct_desc') rows.sort((a, b) => b.pct-a.pct);
      else rows.sort((a, b) => a.name.localeCompare(b.name));
      if (expSortKey && expSortKey !== 'co2') {
        rows.sort((a, b) => {
          let av = (expSortKey === 'metric' ? a.metric : a[expSortKey]) ?? 0;
          let bv = (expSortKey === 'metric' ? b.metric : b[expSortKey]) ?? 0;
          if (typeof av === 'string') return expSortDir === 'asc' ? av.localeCompare(bv) : bv.localeCompare(av);
          return expSortDir === 'asc' ? av - bv : bv - av;
        });
      }
      const totalCO2 = rows.reduce((s, r) => s+(r.co2||0), 0);
      q('exp-count').textContent = rows.length; q('exp-total').textContent = totalCO2.toFixed(0);
      ['rank','name','metric','co2','pct','r2','risk'].forEach(k => { const el = q('exth-'+k); if(el) el.className = expSortKey===k?('sort-'+expSortDir):''; });
      const tbody = q('explore-tbody'); tbody.innerHTML = '';
      rows.forEach((r, i) => {
        const co2Str = r.co2!=null ? r.co2.toLocaleString(undefined,{maximumFractionDigits:1}) : '—';
        const metricStr = r.metric!=null ? (metric==='population'?Math.round(r.metric).toLocaleString():r.metric.toLocaleString(undefined,{maximumFractionDigits:2})) : '—';
        const pctStr = r.pct!=null ? (r.pct>=0?'+':'')+r.pct.toFixed(1)+'%' : '—';
        const pctColor = r.pct>10?'var(--red)':r.pct>0?'var(--amber)':'var(--accent)';
        const tr = document.createElement('tr');
        tr.innerHTML = `<td class="td-num">${i+1}</td><td style="cursor:pointer;color:var(--texthi)" onclick="selectCountry('${r.name.replace(/'/g,"\\'")}')"><strong>${r.name}</strong></td><td class="td-num">${metricStr}</td><td class="td-num">${co2Str}</td><td class="td-num" style="color:${pctColor}">${pctStr}</td><td class="td-num">${r.r2.toFixed(3)}</td><td><span class="risk-pill" style="background:${r.riskColor}22;color:${r.riskColor};border:1px solid ${r.riskColor}55">${r.risk}</span></td>`;
        tbody.appendChild(tr);
      });
      Plotly.react('chart-explore-scatter', [{
        type:'scatter',mode:'markers',x:rows.map(r=>r.metric),y:rows.map(r=>r.pct),text:rows.map(r=>r.name),
        hovertemplate:'<b>%{text}</b><br>'+getMetricLabel(metric)+': %{x}<br>Forecast Δ: %{y:.1f}%<extra></extra>',
        marker:{color:rows.map(r=>r.riskColor),size:rows.map(r=>Math.max(8,Math.min(28,Math.sqrt(Math.abs(r.co2||10))*0.8))),opacity:0.85}
      }], {...BL, margin:{l:54,r:14,t:20,b:50},
        xaxis:{...BL.xaxis,title:{text:getMetricLabel(metric),font:{size:9,color:C.textdim}}},
        yaxis:{...BL.yaxis,title:{text:'Forecast Δ%',font:{size:9,color:C.textdim}},zeroline:true,zerolinecolor:C.grid},
        shapes:[{type:'line',x0:0,x1:1,xref:'paper',y0:0,y1:0,line:{color:C.accent,width:1,dash:'dot'}}]}, cfg);
    }
    function exportTableCSV() {
      const metric = q('exp-metric').value, year = parseInt(q('exp-year').value);
      let csv = 'Country,ISO,'+getMetricLabel(metric)+',CO2_MT,Forecast_pct,RF_R2,Risk\n';
      D.countries.forEach(c => {
        const cd = D.per_country[c]; if(!cd) return;
        const yi = cd.years.indexOf(year);
        const mv = yi>=0?getMetricVal(cd,metric,yi):''; const cv = yi>=0&&cd.co2[yi]!=null?cd.co2[yi]:'';
        const ins = cd.insight||{};
        csv += `${c},${cd.iso||''},${mv!=null?mv:''},${cv},${ins.pct_change??''},${cd.rf_r2??''},${ins.risk||''}\n`;
      });
      downloadBlob(csv, `explore_${metric}_${year}.csv`, 'text/csv');
    }

    // ── EXPORT & SHARE ────────────────────────────────────────────────
    function downloadBlob(content, filename, type) {
      const blob = new Blob([content],{type}), url = URL.createObjectURL(blob);
      const a = document.createElement('a'); a.href=url; a.download=filename;
      document.body.appendChild(a); a.click();
      setTimeout(()=>{document.body.removeChild(a);URL.revokeObjectURL(url);},100);
    }
    function exportAllCSV() {
      let csv = 'Country,ISO,Year,Energy_per_cap,GDP_per_cap,Population,CO2_MT,CO2_per_cap\n';
      D.countries.forEach(c => {
        const cd = D.per_country[c]; if(!cd) return;
        cd.years.forEach((y,i) => {
          csv += `${c},${cd.iso||''},${y},${cd.energy_pc?.[i]??''},${cd.gdp_pc?.[i]??''},${cd.population?.[i]??''},${cd.co2?.[i]??''},${cd.co2_per_capita?.[i]??''}\n`;
        });
      });
      downloadBlob(csv,'carbon_emission_all_countries.csv','text/csv');
    }
    function exportJSON() { downloadBlob(JSON.stringify(D,null,2),'carbon_dashboard_data.json','application/json'); }
    function exportCountryCSV() {
      const c = activeCountry; if(!c){alert('Select a country from the sidebar first.');return;}
      const cd = D.per_country[c]; if(!cd) return;
      let csv = 'Year,CO2_MT,CO2_per_Capita,Energy_per_Capita,GDP_per_Capita,Population,RF_Forecast,LR_Forecast\n';
      cd.years.forEach((y,i) => { csv += `${y},${cd.co2?.[i]??''},${cd.co2_per_capita?.[i]??''},${cd.energy_pc?.[i]??''},${cd.gdp_pc?.[i]??''},${cd.population?.[i]??''},,\n`; });
      (cd.forecast_years||[]).forEach((fy,fi) => { csv += `${fy},,,,,,${cd.rf_forecast?.[fi]??''},${cd.lr_forecast?.[fi]??''}\n`; });
      downloadBlob(csv,`${c.replace(/ /g,'_')}_data.csv`,'text/csv');
    }
    function exportMapPNG() {
      Plotly.downloadImage(document.getElementById('chart-map'),{format:'png',filename:'carbon_emission_map',width:1200,height:700})
        .catch(()=>alert('View the Map tab first, then try again.'));
    }
    function exportTop10CSV() {
      const top10 = D.global.top10_countries, years = D.global.years;
      let csv = 'Year,'+top10.join(',')+'\n';
      years.forEach((y,yi)=>{ csv += `${y},${top10.map(c=>D.global.top10[c]?.co2?.[yi]??'').join(',')}\n`; });
      downloadBlob(csv,'top10_emitters_history.csv','text/csv');
    }
    function exportForecastCSV() {
      let csv = 'Country,ISO,Latest_CO2_MT,RF_Forecast_End,LR_Forecast_End,Forecast_pct,RF_R2,LR_R2,RF_MAE,LR_MAE,Risk,TopFactor,Insight\n';
      D.countries.forEach(c => {
        const cd = D.per_country[c]; if(!cd) return; const ins = cd.insight||{};
        csv += `${c},${cd.iso||''},${cd.co2?.at(-1)??''},${cd.rf_forecast?.at(-1)??''},${cd.lr_forecast?.at(-1)??''},${ins.pct_change??''},${cd.rf_r2??''},${cd.lr_r2??''},${cd.rf_mae??''},${cd.lr_mae??''},${ins.risk||''},${ins.top_factor||''},"${(ins.headline||'').replace(/"/g,"'")}"\n`;
      });
      downloadBlob(csv,'carbon_forecast_summary.csv','text/csv');
    }
    function initShareTab() {
      const urlInput = q('share-url-input'); if(urlInput) urlInput.value = window.location.href;
      const tbody = q('dataset-info-body'); if(!tbody) return; tbody.innerHTML = '';
      [['Countries',D.meta.n_countries],['Year Range',`${D.meta.year_start} – ${D.meta.year_end}`],
       ['Forecast Horizon',`${D.meta.forecast_years} years`],['Features',D.meta.feature_cols.join(', ')],
       ['Total Data Points',(D.meta.n_countries*(D.meta.year_end-D.meta.year_start+1)).toLocaleString()],
       ['Top Emitter (latest)',D.global.top10_countries[0]||'—'],['Dashboard Version','2.0 — Full Stack']
      ].forEach(([k,v])=>{
        const tr = document.createElement('tr');
        tr.innerHTML = `<td style="padding:8px 10px;border-bottom:1px solid var(--border);color:var(--textdim);font-family:var(--mono);font-size:10px;letter-spacing:.1em;text-transform:uppercase;width:45%">${k}</td><td style="padding:8px 10px;border-bottom:1px solid var(--border);color:var(--texthi);font-size:12px">${v}</td>`;
        tbody.appendChild(tr);
      });
    }
    function showToast(msg) {
      let t = document.getElementById('copy-toast');
      if(!t){t=document.createElement('div');t.id='copy-toast';t.className='copy-toast';document.body.appendChild(t);}
      t.textContent=msg; t.classList.add('show'); setTimeout(()=>t.classList.remove('show'),2200);
    }
    function copyShareLink() {
      const url = window.location.href;
      if(navigator.clipboard) navigator.clipboard.writeText(url).then(()=>showToast('✔ Link copied to clipboard!'));
      else{const inp=q('share-url-input');inp.select();document.execCommand('copy');showToast('✔ Link copied!');}
    }
    function shareTwitter() {
      const t=encodeURIComponent('Check out this Carbon Emission Dashboard with ML forecasts for '+D.meta.n_countries+' countries! #ClimateChange #DataScience');
      window.open(`https://twitter.com/intent/tweet?text=${t}&url=${encodeURIComponent(location.href)}`,'_blank');
    }
    function shareLinkedIn() { window.open(`https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(location.href)}`,'_blank'); }
    function shareEmail() {
      const s=encodeURIComponent('Carbon Emission Dashboard — ML Forecasts for '+D.meta.n_countries+' Countries');
      const b=encodeURIComponent('Hi,\n\nI wanted to share this Carbon Emission Dashboard:\n\n'+location.href);
      location.href=`mailto:?subject=${s}&body=${b}`;
    }

    // ── INIT ──────────────────────────────────────────────────────────
    async function init() {
  try {
    const res = await fetch('http://localhost:5000/api/data', { credentials: 'include' });
    if (res.status === 401 || res.redirected && res.url.includes('login')) {
      window.location.href = 'http://localhost:5000/login';
      return;
    }

    D = await res.json();
  } catch (e) {
    console.error("Failed to load data:", e);
    return;
  }

      q('footer-date').textContent = new Date().toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
      q('sb-meta').textContent = `${D.meta.n_countries} countries · ${D.meta.year_start}–${D.meta.year_end}`;
      q('pg-meta').innerHTML = `${D.meta.n_countries} countries · ${D.meta.year_start}–${D.meta.year_end}<br>Forecast +${D.meta.forecast_years} yrs · RF + LR`;
      q('ai-count').textContent = D.meta.n_countries; q('ai-range').textContent = `${D.meta.year_start}–${D.meta.year_end}`;
      buildList(); updateChips(); renderMapKPIs(); renderMap(); renderTop10List(); renderTop10Trend(); buildSugg();
      if (D.countries.length) { activeCountry = D.countries[0]; syncSidebar(); }
    }
    window.initDashboard = init;
  