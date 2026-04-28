import React, { useEffect } from 'react';
import './index.css';

const App = () => {
  useEffect(() => {
    // We wait a small tick to ensure the DOM is fully painted
    setTimeout(() => {
      if (window.initDashboard) {
        window.initDashboard();
      }
    }, 100);
  }, []);

  return (
    <>
      

  
  <div id="topbar">
    <button id="menu-btn" onClick={() => { toggleSidebar() }} aria-label="Toggle menu">☰</button>
    <span id="topbar-logo">🌍</span>
    <span id="topbar-title">CARBON MONITOR</span>
  </div>

  
  <div id="sidebar-overlay" onClick={() => { closeSidebar() }}></div>

  
  <aside id="sidebar">
    <div className="sb-head">
      <div className="logo-row"><span className="globe">🌍</span>
        <h1>Carbon Monitor</h1>
      </div>
      <p id="sb-meta">— countries</p>
    </div>
    <div className="sb-search">
      <div className="sb-section-lbl" id="sb-mode-lbl">Select Country</div>
      <div className="search-wrap">
        <input type="text" id="country-search" placeholder="Search country…" onInput={(e) => { filterCountries() }} />
        <button className="clear-btn" onClick={() => { clearSearch() }}>✕</button>
      </div>
      <div id="country-list"></div>
    </div>
    <div className="sb-footer">scikit-learn · Plotly.js<br />Synthetic / OWID Dataset<br /><span id="footer-date">—</span>
    </div>
  </aside>

  
  <main id="main">
    <div className="pg-header">
      <div>
        <h2>Global Carbon <span>Emission</span> Dashboard</h2>
        <div style={{'fontSize': '12px', 'color': 'var(--textdim)', 'marginTop': '3px', 'fontFamily': 'var(--mono)'}}>Historical · ML Forecast
          · AI Assistant</div>
      </div>
      <div style={{'display': 'flex', 'alignItems': 'center', 'gap': '10px', 'flexWrap': 'wrap', 'justifyContent': 'flex-end'}}>
        <div className="pg-meta" id="pg-meta">—</div>
        <a className="btn-sm" href="/logout" style={{'textDecoration': 'none'}}>Logout</a>
      </div>
    </div>

    <div className="tabs">
      <button className="tab-btn active" onClick={() => { switchTab('map') }}>🗺️ Map</button>
      <button className="tab-btn" onClick={() => { switchTab('country') }}>📊 Country</button>
      <button className="tab-btn" onClick={() => { switchTab('compare') }}>🆚 Compare</button>
      <button className="tab-btn" onClick={() => { switchTab('global') }}>🌐 Global</button>
      <button className="tab-btn" onClick={() => { switchTab('aqi') }}>🌫️ AQI Index</button>
      <button className="tab-btn" onClick={() => { switchTab('explore') }}>🔍 Explore</button>
      <button className="tab-btn" onClick={() => { switchTab('share') }}>📤 Export &amp; Share</button>
      <button className="tab-btn" onClick={() => { switchTab('chat') }}>🤖 AI Chat</button>
    </div>

    
    <div className="tab-panel active" id="tab-map">
      <div className="kpi-row">
        <div className="kpi">
          <div className="kpi-lbl">Global CO₂</div>
          <div className="kpi-val green" id="kpi-global-total">—</div>
          <div className="kpi-sub">Million Tonnes</div>
        </div>
        <div className="kpi">
          <div className="kpi-lbl">Top Emitter</div>
          <div className="kpi-val" id="kpi-top-emitter" style={{'fontSize': '15px'}}>—</div>
          <div className="kpi-sub" id="kpi-top-emitter-val">—</div>
        </div>
        <div className="kpi">
          <div className="kpi-lbl">Countries</div>
          <div className="kpi-val blue" id="kpi-n-countries">—</div>
          <div className="kpi-sub" id="kpi-year-range">—</div>
        </div>
        <div className="kpi">
          <div className="kpi-lbl">Data Year</div>
          <div className="kpi-val amber" id="kpi-data-year">—</div>
          <div className="kpi-sub">Latest</div>
        </div>
      </div>
      <div className="card" style={{'padding': '14px 18px'}}>
        <div className="year-slider-row">
          <label>YEAR</label>
          <input type="range" id="map-year-slider" min="2003" max="2023" step="5" value="2023"
            onInput={(e) => { onMapYearChange() }} />
          <div className="yr-val" id="map-year-val">2023</div>
        </div>
        <div style={{'display': 'flex', 'gap': '8px', 'flexWrap': 'wrap'}}>
          <button className="model-btn active" id="map-mode-total" onClick={() => { setMapMode('total') }}>Total CO₂</button>
          <button className="model-btn" id="map-mode-percap" onClick={() => { setMapMode('percap') }}>Per Capita</button>
          <button className="model-btn" id="map-mode-aqi" onClick={() => { setMapMode('aqi') }}>AQI Index</button>
        </div>
      </div>
      <div className="card">
        <div className="card-title">CO₂ Emissions by Country</div>
        <div id="chart-map" style={{'height': 'min(440px,55vw)'}}></div>
      </div>
      <div className="grid-2">
        <div className="card" style={{'marginBottom': '0'}}>
          <div className="card-title">Top 10 Emitters</div>
          <div id="top10-list" className="emitter-list"></div>
        </div>
        <div className="card" style={{'marginBottom': '0'}}>
          <div className="card-title">Top 10 Trends</div>
          <div id="chart-top10" style={{'height': 'min(260px,55vw)'}}></div>
        </div>
      </div>
    </div>

    
    <div className="tab-panel" id="tab-country">
      <div
        style={{'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between', 'marginBottom': '16px', 'flexWrap': 'wrap', 'gap': '10px'}}>
        <div>
          <div style={{'fontSize': '18px', 'fontWeight': '600', 'color': 'var(--texthi)'}} id="country-title">Select a country →</div>
          <div style={{'fontSize': '11px', 'color': 'var(--textdim)', 'fontFamily': 'var(--mono)'}} id="country-subtitle">Use the sidebar
          </div>
        </div>
        <div className="model-toggle">
          <button className="model-btn active" id="btn-rf" onClick={() => { setModel('rf') }}>Random Forest</button>
          <button className="model-btn" id="btn-lr" onClick={() => { setModel('lr') }}>Linear Reg.</button>
        </div>
      </div>
      <div id="country-no-data" className="no-data">🌍 Select a country from the sidebar.</div>
      <div id="country-detail" style={{'display': 'none'}}>
        <div className="kpi-row">
          <div className="kpi">
            <div className="kpi-lbl">Latest CO₂</div>
            <div className="kpi-val green" id="ckpi-latest">—</div>
            <div className="kpi-sub">MT</div>
          </div>
          <div className="kpi">
            <div className="kpi-lbl">Forecast End</div>
            <div className="kpi-val" id="ckpi-fc-end">—</div>
            <div className="kpi-sub" id="ckpi-fc-year">—</div>
          </div>
          <div className="kpi">
            <div className="kpi-lbl">Change</div>
            <div className="kpi-val" id="ckpi-change">—</div>
            <div className="kpi-sub">vs current</div>
          </div>
          <div className="kpi">
            <div className="kpi-lbl">Risk</div>
            <div className="kpi-val" id="ckpi-risk">—</div>
            <div className="kpi-sub">R² <span id="ckpi-r2" style={{'fontFamily': 'var(--mono)', 'color': 'var(--accent)'}}>—</span>
            </div>
          </div>
        </div>
        <div className="insight">
          <div style={{'display': 'flex', 'justifyContent': 'space-between', 'alignItems': 'flex-start', 'marginBottom': '8px'}}>
            <div style={{'fontFamily': 'var(--mono)', 'fontSize': '9px', 'letterSpacing': '.2em', 'color': 'var(--textdim)'}}>🧠 AI INSIGHT
            </div>
            <div className="risk-chip" id="risk-chip">—</div>
          </div>
          <div className="ins-head" id="ins-head">—</div>
          <div className="ins-detail" id="ins-detail">—</div>
          <div className="ins-rec" id="ins-rec">—</div>
        </div>
        <div className="card">
          <div className="card-title">Emission History &amp; Forecast</div>
          <div id="chart-country-trend" style={{'height': 'min(340px,60vw)'}}></div>
        </div>
        <div className="grid-3">
          <div className="card" style={{'marginBottom': '0'}}>
            <div className="card-title">Gauge</div>
            <div id="chart-country-gauge" style={{'height': 'min(220px,55vw)'}}></div>
          </div>
          <div className="card" style={{'marginBottom': '0'}}>
            <div className="card-title">Feature Importances</div>
            <div id="chart-country-fi" style={{'height': 'min(220px,55vw)'}}></div>
          </div>
          <div className="card" style={{'marginBottom': '0'}}>
            <div className="card-title">Actual vs Predicted</div>
            <div id="chart-country-scatter" style={{'height': 'min(220px,55vw)'}}></div>
          </div>
        </div>
        <div className="card" style={{'marginTop': '14px'}}>
          <div className="card-title">Forecast Table</div>
          <div style={{'overflowX': 'auto'}}>
            <table style={{'width': '100%', 'borderCollapse': 'collapse', 'fontFamily': 'var(--mono)', 'fontSize': '11px', 'minWidth': '280px'}}>
              <thead>
                <tr>
                  <th
                    style={{'textAlign': 'left', 'padding': '7px 10px', 'color': 'var(--textdim)', 'fontSize': '9px', 'borderBottom': '1px solid var(--border)'}}>
                    YEAR</th>
                  <th
                    style={{'textAlign': 'left', 'padding': '7px 10px', 'color': 'var(--accent)', 'fontSize': '9px', 'borderBottom': '1px solid var(--border)'}}>
                    RF (MT)</th>
                  <th
                    style={{'textAlign': 'left', 'padding': '7px 10px', 'color': 'var(--amber)', 'fontSize': '9px', 'borderBottom': '1px solid var(--border)'}}>
                    LR (MT)</th>
                </tr>
              </thead>
              <tbody id="fc-table-body"></tbody>
            </table>
          </div>
        </div>
      </div>
    </div>

    
    <div className="tab-panel" id="tab-compare">
      <div className="cmp-selector">
        <div className="card-title" style={{'marginBottom': '10px'}}>Select Up to 4 Countries to Compare</div>
        <div className="cmp-chips" id="cmp-chips"><span className="cmp-hint">No countries selected</span></div>
        <div className="cmp-controls">
          <div className="cmp-dd">
            <input type="text" id="cmp-input" placeholder="Type to search and add a country…" onInput={(e) => { filterCmpDd() }}
              onfocus="openCmpDd()" onblur="setTimeout(closeCmpDd,200)" autocomplete="off" />
            <div className="cmp-dd-list" id="cmp-dd-list"></div>
          </div>
          <button className="btn-sm" onClick={() => { clearCompare() }}>Clear All</button>
        </div>
      </div>
      <div id="cmp-placeholder" className="no-data">🆚 Add at least 2 countries to compare.</div>
      <div id="cmp-content" style={{'display': 'none'}}>
        <div className="card">
          <div className="card-title">Emission History &amp; Forecast</div>
          <div id="chart-cmp-trend" style={{'height': 'min(380px,60vw)'}}></div>
        </div>
        <div className="grid-2">
          <div className="card" style={{'marginBottom': '0'}}>
            <div className="card-title">Latest Year (MT)</div>
            <div id="chart-cmp-latest" style={{'height': 'min(280px,55vw)'}}></div>
          </div>
          <div className="card" style={{'marginBottom': '0'}}>
            <div className="card-title">5-Year Forecast</div>
            <div id="chart-cmp-fc" style={{'height': 'min(280px,55vw)'}}></div>
          </div>
        </div>
        <div style={{'height': '14px'}}></div>
        <div className="grid-2">
          <div className="card" style={{'marginBottom': '0'}}>
            <div className="card-title">Radar Comparison</div>
            <div id="chart-cmp-radar" style={{'height': 'min(300px,80vw)'}}></div>
          </div>
          <div className="card" style={{'marginBottom': '0'}}>
            <div className="card-title">Metrics Table</div>
            <div style={{'overflowX': 'auto'}}>
              <table className="cmp-table">
                <thead>
                  <tr>
                    <th>Country</th>
                    <th>Latest</th>
                    <th>Forecast</th>
                    <th>Change</th>
                    <th>R²</th>
                    <th>Risk</th>
                  </tr>
                </thead>
                <tbody id="cmp-tbody"></tbody>
              </table>
            </div>
            <div style={{'marginTop': '16px'}}>
              <div
                style={{'fontFamily': 'var(--mono)', 'fontSize': '9px', 'letterSpacing': '.14em', 'color': 'var(--textdim)', 'marginBottom': '10px', 'textTransform': 'uppercase'}}>
                Projected % Change</div>
              <div id="cmp-pct-bars"></div>
            </div>
          </div>
        </div>
      </div>
    </div>

    
    <div className="tab-panel" id="tab-global">
      <div className="kpi-row">
        <div className="kpi">
          <div className="kpi-lbl">1990 CO₂</div>
          <div className="kpi-val" id="gkpi-1990">—</div>
          <div className="kpi-sub">MT</div>
        </div>
        <div className="kpi">
          <div className="kpi-lbl">Latest CO₂</div>
          <div className="kpi-val green" id="gkpi-latest">—</div>
          <div className="kpi-sub">MT</div>
        </div>
        <div className="kpi">
          <div className="kpi-lbl">Growth</div>
          <div className="kpi-val red" id="gkpi-growth">—</div>
          <div className="kpi-sub">Since 1990</div>
        </div>
        <div className="kpi">
          <div className="kpi-lbl">Countries</div>
          <div className="kpi-val blue" id="gkpi-countries">—</div>
          <div className="kpi-sub">tracked</div>
        </div>
      </div>
      <div className="card">
        <div className="card-title">Global CO₂ Total 1990–Present</div>
        <div id="chart-global-total" style={{'height': 'min(300px,55vw)'}}></div>
      </div>
      <div className="grid-2">
        <div className="card" style={{'marginBottom': '0'}}>
          <div className="card-title">Top 10 — Share of Global</div>
          <div id="chart-top10-pie" style={{'height': 'min(300px,80vw)'}}></div>
        </div>
        <div className="card" style={{'marginBottom': '0'}}>
          <div className="card-title">Top 10 — Annual Trends</div>
          <div id="chart-global-lines" style={{'height': 'min(300px,55vw)'}}></div>
        </div>
      </div>
    </div>

    
    <div className="tab-panel" id="tab-aqi">
      <div className="kpi-row">
        <div className="kpi">
          <div className="kpi-lbl">Avg AQI</div>
          <div className="kpi-val green" id="aqikpi-avg">—</div>
          <div className="kpi-sub">estimated index</div>
        </div>
        <div className="kpi">
          <div className="kpi-lbl">Highest</div>
          <div className="kpi-val red" id="aqikpi-high">—</div>
          <div className="kpi-sub" id="aqikpi-high-name">—</div>
        </div>
        <div className="kpi">
          <div className="kpi-lbl">Improving</div>
          <div className="kpi-val blue" id="aqikpi-cleaner">—</div>
          <div className="kpi-sub">forecast decline</div>
        </div>
        <div className="kpi">
          <div className="kpi-lbl">Selected</div>
          <div className="kpi-val amber" id="aqikpi-selected">—</div>
          <div className="kpi-sub" id="aqikpi-selected-cat">—</div>
        </div>
      </div>
      <div className="grid-2">
        <div className="card">
          <div className="card-title">Country AQI Profile</div>
          <div className="aqi-panel">
            <div className="aqi-ring" id="aqi-ring">
              <div className="aqi-ring-inner">
                <div>
                  <div className="aqi-label">Estimated AQI</div>
                  <div className="aqi-score" id="aqi-score">—</div>
                  <div className="aqi-label" id="aqi-category">—</div>
                </div>
              </div>
            </div>
            <div>
              <div style={{'fontSize': '18px', 'fontWeight': '600', 'color': 'var(--texthi)'}} id="aqi-country">—</div>
              <div style={{'fontSize': '12px', 'color': 'var(--textdim)', 'marginTop': '6px', 'lineHeight': '1.65'}} id="aqi-explain">—</div>
              <div className="aqi-actions">
                <button className="btn-sm" onClick={() => { askAqiAboutCountry() }}>Ask AI</button>
                <button className="btn-sm" onClick={() => { switchTab('country') }}>Open Country</button>
                <button className="btn-sm" onClick={() => { setMapMode('aqi');switchTab('map') }}>Map AQI</button>
              </div>
            </div>
          </div>
        </div>
        <div className="card">
          <div className="card-title">Policy Mixer</div>
          <div className="mixer-row"><span>Energy cut</span><input type="range" id="mix-energy" min="0" max="45" value="18" onInput={(e) => { updateMixer() }} /><strong id="mix-energy-v">18%</strong></div>
          <div className="mixer-row"><span>Clean power</span><input type="range" id="mix-power" min="0" max="45" value="22" onInput={(e) => { updateMixer() }} /><strong id="mix-power-v">22%</strong></div>
          <div className="mixer-row"><span>Transport shift</span><input type="range" id="mix-transport" min="0" max="35" value="12" onInput={(e) => { updateMixer() }} /><strong id="mix-transport-v">12%</strong></div>
          <div style={{'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between', 'gap': '12px', 'marginTop': '18px'}}>
            <div>
              <div style={{'fontFamily': 'var(--mono)', 'fontSize': '9px', 'letterSpacing': '.14em', 'color': 'var(--textdim)', 'textTransform': 'uppercase'}}>Projected AQI</div>
              <div style={{'fontFamily': 'var(--mono)', 'fontSize': '28px', 'color': 'var(--accent)', 'fontWeight': '700'}} id="mix-score">—</div>
            </div>
            <div style={{'flex': '1', 'height': '8px', 'background': 'var(--s3)', 'borderRadius': '4px', 'overflow': 'hidden'}}>
              <div id="mix-bar" style={{'width': '0', 'height': '100%', 'background': 'var(--accent)'}}></div>
            </div>
          </div>
          <div style={{'fontSize': '11px', 'color': 'var(--textdim)', 'lineHeight': '1.6', 'marginTop': '14px'}} id="mix-note">—</div>
        </div>
      </div>
      <div className="grid-2" style={{'marginTop': '14px'}}>
        <div className="card" style={{'marginBottom': '0'}}>
          <div className="card-title">AQI Ranking</div>
          <div id="chart-aqi-rank" style={{'height': 'min(320px,70vw)'}}></div>
        </div>
        <div className="card" style={{'marginBottom': '0'}}>
          <div className="card-title">Air Stress Map</div>
          <div id="chart-aqi-map" style={{'height': 'min(320px,70vw)'}}></div>
        </div>
      </div>
      <div className="card" style={{'marginTop': '14px'}}>
        <div className="card-title">Most Urgent AQI Signals</div>
        <div style={{'overflowX': 'auto'}}>
          <table className="aqi-table"><tbody id="aqi-table-body"></tbody></table>
        </div>
      </div>
    </div>

    
    <div className="tab-panel" id="tab-explore">
      <div className="pg-header" style={{'marginBottom': '14px'}}>
        <div>
          <div style={{'fontSize': '18px', 'fontWeight': '700', 'color': 'var(--texthi)'}}>🔍 Data <span style={{'color': 'var(--accent)'}}>Exploration</span></div>
          <div style={{'fontSize': '11px', 'color': 'var(--textdim)', 'fontFamily': 'var(--mono)', 'marginTop': '2px'}}>Filter · Sort · Analyse all countries at once</div>
        </div>
      </div>

      
      <div className="card" style={{'padding': '16px 18px', 'marginBottom': '14px'}}>
        <div className="card-title" style={{'marginBottom': '12px'}}>Filters &amp; Slicers</div>
        <div className="explore-toolbar">
          <span className="explore-lbl">METRIC</span>
          <select id="exp-metric" onChange={(e) => { renderExplore() }}>
            <option value="co2">CO₂ Emissions (MT)</option>
            <option value="co2_per_capita">CO₂ per Capita (t)</option>
            <option value="energy_pc">Energy per Capita (kWh)</option>
            <option value="gdp_pc">GDP per Capita (USD)</option>
            <option value="population">Population</option>
          </select>
          <span className="explore-lbl">YEAR</span>
          <input type="range" id="exp-year" min="1990" max="2023" step="1" value="2023" onInput={(e) => { document.getElementById('exp-year-val').textContent=this.value;renderExplore() }} style={{'minWidth': '140px'}} />
          <span className="explore-lbl" id="exp-year-val" style={{'color': 'var(--accent)', 'fontSize': '13px', 'fontWeight': '700'}}>2023</span>
          <span className="explore-lbl" style={{'marginLeft': '8px'}}>RISK</span>
          <select id="exp-risk" onChange={(e) => { renderExplore() }}>
            <option value="all">All Risk Levels</option>
            <option value="Critical">Critical</option>
            <option value="High">High</option>
            <option value="Moderate">Moderate</option>
            <option value="Low">Low</option>
          </select>
          <span className="explore-lbl">SORT BY</span>
          <select id="exp-sort" onChange={(e) => { renderExplore() }}>
            <option value="co2_desc">CO₂ High → Low</option>
            <option value="co2_asc">CO₂ Low → High</option>
            <option value="pct_asc">% Change ↑</option>
            <option value="pct_desc">% Change ↓</option>
            <option value="alpha">A → Z</option>
          </select>
          <button className="btn-sm" onClick={() => { resetExploreFilters() }} style={{'marginLeft': '4px'}}>Reset</button>
        </div>
        <div style={{'marginTop': '10px', 'display': 'flex', 'gap': '14px', 'flexWrap': 'wrap'}}>
          <span className="explore-lbl">SHOWING <strong id="exp-count" style={{'color': 'var(--accent)'}}>—</strong> COUNTRIES</span>
          <span className="explore-lbl">TOTAL CO₂ <strong id="exp-total" style={{'color': 'var(--accent)'}}>—</strong> MT (selected year)</span>
        </div>
      </div>

      
      <div className="card">
        <div className="card-title">Scatter: Selected Metric vs CO₂ Forecast Change %</div>
        <div id="chart-explore-scatter" style={{'height': 'min(340px,55vw)'}}></div>
      </div>

      
      <div className="card" style={{'padding': '0', 'overflow': 'hidden'}}>
        <div style={{'padding': '14px 18px', 'borderBottom': '1px solid var(--border)', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'space-between'}}>
          <div className="card-title" style={{'marginBottom': '0'}}>Country Data Table</div>
          <button className="btn-export" onClick={() => { exportTableCSV() }} style={{'fontSize': '9px', 'padding': '6px 14px'}}>⬇ CSV</button>
        </div>
        <div className="data-table-wrap" style={{'maxHeight': '420px', 'overflowY': 'auto', 'border': 'none', 'borderRadius': '0'}}>
          <table className="data-table" id="explore-table">
            <thead>
              <tr>
                <th onClick={() => { expSortBy('rank') }} id="exth-rank">#</th>
                <th onClick={() => { expSortBy('name') }} id="exth-name">Country</th>
                <th onClick={() => { expSortBy('metric') }} id="exth-metric">Metric</th>
                <th onClick={() => { expSortBy('co2') }} id="exth-co2">CO₂ (MT)</th>
                <th onClick={() => { expSortBy('pct') }} id="exth-pct">Forecast Δ%</th>
                <th onClick={() => { expSortBy('r2') }} id="exth-r2">Model R²</th>
                <th onClick={() => { expSortBy('risk') }} id="exth-risk">Risk</th>
              </tr>
            </thead>
            <tbody id="explore-tbody"></tbody>
          </table>
        </div>
      </div>
    </div>

    
    <div className="tab-panel" id="tab-share">
      <div className="pg-header" style={{'marginBottom': '14px'}}>
        <div>
          <div style={{'fontSize': '18px', 'fontWeight': '700', 'color': 'var(--texthi)'}}>📤 Export &amp; <span style={{'color': 'var(--accent)'}}>Share</span></div>
          <div style={{'fontSize': '11px', 'color': 'var(--textdim)', 'fontFamily': 'var(--mono)', 'marginTop': '2px'}}>Download data, charts, and reports</div>
        </div>
      </div>

      <div className="export-grid">
        
        <div className="export-card">
          <div className="export-card-icon">📊</div>
          <div className="export-card-title">All Countries — CSV</div>
          <div className="export-card-desc">Download the full dataset for all countries including historical CO₂, per-capita metrics, forecasts, and risk levels.</div>
          <button className="btn-export" id="btn-export-csv" onClick={() => { exportAllCSV() }}>⬇ Download CSV</button>
        </div>

        
        <div className="export-card">
          <div className="export-card-icon">🗄️</div>
          <div className="export-card-title">Raw Data — JSON</div>
          <div className="export-card-desc">Export the complete structured JSON payload used by this dashboard — perfect for further analysis in Python, R, or Excel Power Query.</div>
          <button className="btn-export" id="btn-export-json" onClick={() => { exportJSON() }}>⬇ Download JSON</button>
        </div>

        
        <div className="export-card">
          <div className="export-card-icon">🌍</div>
          <div className="export-card-title">Selected Country — CSV</div>
          <div className="export-card-desc">Export year-by-year data (CO₂, energy, GDP, population, forecasts) for the currently selected country from the sidebar.</div>
          <button className="btn-export" id="btn-export-country-csv" onClick={() => { exportCountryCSV() }}>⬇ Download Country CSV</button>
        </div>

        
        <div className="export-card">
          <div className="export-card-icon">🗺️</div>
          <div className="export-card-title">Map Chart — PNG</div>
          <div className="export-card-desc">Save the current world emission map as a high-quality PNG image. Switch to a map mode first, then download here.</div>
          <button className="btn-export" id="btn-export-png" onClick={() => { exportMapPNG() }}>📷 Save Map PNG</button>
        </div>

        
        <div className="export-card">
          <div className="export-card-icon">🏆</div>
          <div className="export-card-title">Top 10 Emitters — CSV</div>
          <div className="export-card-desc">Download year-by-year historical CO₂ data for the top 10 emitting countries in a single CSV file.</div>
          <button className="btn-export" onClick={() => { exportTop10CSV() }}>⬇ Download Top 10 CSV</button>
        </div>

        
        <div className="export-card">
          <div className="export-card-icon">📋</div>
          <div className="export-card-title">Forecast Summary — CSV</div>
          <div className="export-card-desc">Export a summary table of 5-year ML forecasts, risk levels, and key metrics for every country in the dataset.</div>
          <button className="btn-export" onClick={() => { exportForecastCSV() }}>⬇ Download Forecast CSV</button>
        </div>
      </div>

      
      <div className="card">
        <div className="card-title">Share Dashboard Link</div>
        <div style={{'fontSize': '12px', 'color': 'var(--textdim)', 'lineHeight': '1.7', 'marginBottom': '14px'}}>Copy a direct link to the dashboard. Authenticated users on the same server can open it to see the live data.</div>
        <div className="share-url-row">
          <input type="text" id="share-url-input" readonly />
          <button className="btn-export" onClick={() => { copyShareLink() }}>📋 Copy Link</button>
        </div>
        <div style={{'marginTop': '16px'}}>
          <div className="card-title" style={{'marginBottom': '10px'}}>Share on Social</div>
          <div style={{'display': 'flex', 'gap': '10px', 'flexWrap': 'wrap'}}>
            <button className="btn-export" onClick={() => { shareTwitter() }}>𝕏 Twitter / X</button>
            <button className="btn-export" onClick={() => { shareLinkedIn() }}>in LinkedIn</button>
            <button className="btn-export" onClick={() => { shareEmail() }}>✉ Email</button>
          </div>
        </div>
      </div>

      
      <div className="card">
        <div className="card-title">Dataset Information</div>
        <table style={{'width': '100%', 'borderCollapse': 'collapse', 'fontSize': '12px'}}>
          <tbody id="dataset-info-body"></tbody>
        </table>
      </div>
    </div>

    
    <div className="tab-panel" id="tab-chat">
      <div className="chat-layout">
        <div className="chat-main">
          <div className="status-bar">
            <div style={{'display': 'flex', 'alignItems': 'center'}}>
              <span className="sdot checking" id="chat-dot"></span>
              <span id="chat-status" style={{'color': 'var(--textdim)'}}>Checking…</span>
            </div>
            <button className="btn-sm" onClick={() => { clearChat() }}>Clear</button>
          </div>
          <div className="chat-messages" id="chat-messages">
            <div className="bubble ai">
              <div className="bubble-lbl">Carbon AI</div>
              👋 Hi! I'm your Carbon Emission AI with data on <strong id="ai-count">—</strong> countries (<strong
                id="ai-range">—</strong>).<br /><br />
              Ask me anything about trends, forecasts, or comparisons!<br /><br />
              <em style={{'fontSize': '11px', 'color': 'var(--textdim)'}}>Run <code
                  style={{'fontFamily': 'var(--mono)', 'background': 'var(--s3)', 'padding': '1px 5px', 'borderRadius': '3px'}}>chatbot_server.py</code>
                to activate.</em>
            </div>
            <div className="typing" id="typing">
              <div className="tdots"><span></span><span></span><span></span></div>
            </div>
          </div>
          <div className="chat-input-row">
            <textarea id="chat-input" placeholder="Ask about emissions, forecasts, comparisons…"
              onkeydown="chatKey(event)"></textarea>
            <button className="btn-send" id="btn-send" onClick={() => { sendMsg() }}>↑</button>
          </div>
        </div>
        <div className="chat-side">
          <div className="card" style={{'marginBottom': '0', 'padding': '14px 16px'}}>
            <div className="card-title">Suggested Questions</div>
            <div className="sugg-grid" id="sugg-grid"></div>
          </div>
          <div className="info-box">
            <p><strong>Enable AI Chat:</strong></p>
            <p>1. Get free API key:<br /><a href="https://aistudio.google.com"
                target="_blank">aistudio.google.com</a></p>
            <p>2. Run:<code className="cmd">python chatbot_server.py</code></p>
            <p>3. Open:<code className="cmd">http://localhost:5500</code></p>
          </div>
        </div>
      </div>
    </div>
  </main>

  

    </>
  );
};

export default App;
