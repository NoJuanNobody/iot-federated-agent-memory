"""TinCan Mesh OS: Admin-Only Token Treasury & Economy Control Window.

Provides ``#win-admin-treasury`` markup, scoped Aeonik Celadon & Ink CSS
(with high-contrast ``#111111`` Operator Header), and hydration JS wired to:
  - ``GET  /api/admin/treasury``
  - ``POST /api/admin/economy-dials``
  - ``POST /api/admin/cloud-routing``
  - ``POST /api/tokens/mint``
  - ``POST /api/tokens/mint-requests/review``
"""

from __future__ import annotations

ADMIN_TREASURY_TITLEBAR = (
    '<!--TC_TITLEBAR {"id": "win-admin-treasury", '
    '"title": "Token Treasury & Economy Control", '
    '"badge": "ADMIN ONLY"}-->'
)

ADMIN_TREASURY_CSS = r"""
/* tc-admin-treasury-css */
#win-admin-treasury {
  --at-bg: #ecf1e6;
  --at-card: #f4f8f0;
  --at-paper: #ffffff;
  --at-ink: #111111;
  --at-muted: #4a4a4a;
  --at-pos: #107a47;
  --at-danger: #8a1c1c;
  --at-hair: 1px solid #111111;
  --at-font: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
  --at-mono: "JetBrains Mono", ui-monospace, "SF Mono", Menlo, Consolas, monospace;
}
#win-admin-treasury .at-body {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 12px 14px;
  max-height: min(760px, calc(100vh - 110px));
  overflow-y: auto;
  background: var(--at-bg);
  color: var(--at-ink);
  font-family: var(--at-font);
  font-size: 12px;
}
#win-admin-treasury .at-banner {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 10px 12px;
  background: #111111;
  color: #ecf1e6;
  border-radius: 12px;
}
#win-admin-treasury .at-group {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
}
#win-admin-treasury .at-badge {
  display: inline-flex;
  align-items: center;
  padding: 2px 9px;
  border-radius: 9999px;
  font-family: var(--at-mono);
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.05em;
  text-transform: uppercase;
  background: var(--at-pos);
  color: #ffffff;
}
#win-admin-treasury .at-pill {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 5px 12px;
  border-radius: 9999px;
  border: var(--at-hair);
  background: var(--at-paper);
  color: var(--at-ink);
  font-family: var(--at-mono);
  font-size: 10.5px;
  font-weight: 600;
  cursor: pointer;
}
#win-admin-treasury .at-pill--solid { background: #111111; color: #ecf1e6; }
#win-admin-treasury .at-pill--danger { background: var(--at-danger); border-color: #d66b6b; color: #ffffff; }
#win-admin-treasury .at-pill--pos { background: var(--at-pos); border-color: var(--at-pos); color: #ffffff; }
#win-admin-treasury .at-pill--sm { padding: 3px 9px; font-size: 10px; }
#win-admin-treasury .at-pool-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}
#win-admin-treasury .at-card {
  background: var(--at-paper);
  border: var(--at-hair);
  border-radius: 12px;
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
#win-admin-treasury .at-card--celadon { background: var(--at-card); }
#win-admin-treasury .at-label {
  font-size: 9.5px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: var(--at-muted);
}
#win-admin-treasury .at-val {
  font-family: var(--at-mono);
  font-size: 20px;
  font-weight: 700;
  color: var(--at-ink);
}
#win-admin-treasury .at-sub {
  font-size: 10.5px;
  color: var(--at-muted);
}
#win-admin-treasury .at-mid-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.08fr) minmax(0, 1fr);
  gap: 12px;
}
#win-admin-treasury .at-slider {
  width: 100%;
  accent-color: #111111;
  cursor: pointer;
}
#win-admin-treasury .at-input {
  padding: 5px 9px;
  border: var(--at-hair);
  border-radius: 8px;
  background: var(--at-card);
  color: var(--at-ink);
  font-family: var(--at-mono);
  font-size: 11px;
}
#win-admin-treasury .at-table-wrap {
  overflow-x: auto;
  border: var(--at-hair);
  border-radius: 10px;
  background: var(--at-paper);
}
#win-admin-treasury .at-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 11px;
}
#win-admin-treasury .at-table th,
#win-admin-treasury .at-table td {
  padding: 7px 10px;
  border-bottom: 1px solid rgba(17, 17, 17, 0.10);
  text-align: left;
  white-space: nowrap;
}
#win-admin-treasury .at-table th {
  background: var(--at-card);
  color: var(--at-muted);
  font-weight: 700;
  font-size: 10px;
  text-transform: uppercase;
}
#win-admin-treasury .at-mono { font-family: var(--at-mono); font-variant-numeric: tabular-nums; }
#win-admin-treasury .at-pos { color: var(--at-pos); font-weight: 700; }
"""


def render_admin_treasury_window_html() -> str:
    """Return the complete ``#win-admin-treasury`` Admin Control Panel window."""
    return f"""<div id="win-admin-treasury" class="mesh-window hidden w-[1040px] max-w-full" data-zen-window="true" data-window-id="win-admin-treasury" style="top: 64px; left: 96px; z-index: 28;">
      {ADMIN_TREASURY_TITLEBAR}
      <div class="window-body at-body aeonik-scope" data-at-root="true">
        <div class="at-banner">
          <div class="at-group">
            <strong style="font-size:14px;">Token Treasury &amp; Economy Control</strong>
            <span class="at-badge">ADMIN ONLY · X-ADMIN-KEY</span>
          </div>
          <div class="at-group">
            <button type="button" id="adminKillSwitchBtn" class="at-pill at-pill--danger" onclick="window.TinCanAdminTreasury && window.TinCanAdminTreasury.toggleCloudRouting()">⏸ Pause Cloud Routing</button>
            <button type="button" id="adminExportAuditBtn" class="at-pill" onclick="window.TinCanAdminTreasury && window.TinCanAdminTreasury.exportCsv()">Export Audit CSV</button>
            <button type="button" id="adminRefreshBtn" class="at-pill" onclick="window.TinCanAdminTreasury && window.TinCanAdminTreasury.refresh()">↻ Refresh</button>
          </div>
        </div>

        <div class="at-pool-grid">
          <div class="at-card">
            <span class="at-label">NanoGPT Pool</span>
            <span id="adminPoolNanoVal" class="at-val">$0.00</span>
            <span id="adminPoolNanoSub" class="at-sub">Checking NanoGPT API…</span>
          </div>
          <div class="at-card">
            <span class="at-label">OpenRouter Pool</span>
            <span id="adminPoolOrVal" class="at-val">$0.00</span>
            <span id="adminPoolOrSub" class="at-sub">Checking OpenRouter API…</span>
          </div>
          <div class="at-card">
            <span class="at-label">Hyper3D Rodin</span>
            <span id="adminPoolRodinVal" class="at-val">$0.00</span>
            <span id="adminPoolRodinSub" class="at-sub">0.0 CR · pooled</span>
          </div>
          <div class="at-card">
            <span class="at-label">Net Margin (30D)</span>
            <span id="adminPoolMarginVal" class="at-val">$0.00</span>
            <span id="adminPoolMarginSub" class="at-sub">After Stripe fees · 0 checkouts</span>
          </div>
        </div>

        <div class="at-mid-grid">
          <section class="at-card at-card--celadon" aria-label="Live Economy Dials">
            <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;">
              <strong>Credit Markup &amp; Gross Margin Dial</strong>
              <span id="adminMarkupBadge" class="at-badge">1.25x · 20.0% GROSS MARGIN</span>
            </div>
            <input id="adminMarkupSlider" class="at-slider" type="range" min="1.00" max="2.00" step="0.01" value="1.25" oninput="window.TinCanAdminTreasury && window.TinCanAdminTreasury.previewDials()" />
            <div class="at-group">
              <button type="button" class="at-pill at-pill--sm" onclick="window.TinCanAdminTreasury && window.TinCanAdminTreasury.setMarkupPreset(1.00)">1.00x (0%)</button>
              <button type="button" class="at-pill at-pill--sm" onclick="window.TinCanAdminTreasury && window.TinCanAdminTreasury.setMarkupPreset(1.25)">1.25x (20%)</button>
              <button type="button" class="at-pill at-pill--sm" onclick="window.TinCanAdminTreasury && window.TinCanAdminTreasury.setMarkupPreset(1.30)">1.30x (23%)</button>
              <button type="button" class="at-pill at-pill--sm" onclick="window.TinCanAdminTreasury && window.TinCanAdminTreasury.setMarkupPreset(1.43)">1.43x (30%)</button>
            </div>

            <hr style="border:0;border-top:1px solid rgba(17,17,17,0.14);margin:6px 0;" />

            <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;">
              <strong>Sponsor Video Reward Dial</strong>
              <span id="adminAdRewardBadge" class="at-mono" style="font-size:10.5px;font-weight:700;">25 CR / clip × 5/day = 125 CR</span>
            </div>
            <input id="adminAdRewardSlider" class="at-slider" type="range" min="0" max="1000" step="5" value="25" oninput="window.TinCanAdminTreasury && window.TinCanAdminTreasury.previewDials()" />
            <div style="display:flex;justify-content:space-between;align-items:center;gap:8px;margin-top:4px;">
              <span class="at-sub">Local business CPV transfers to CR · Max daily cap: <strong id="adminDailyCapVal">5</strong> clips</span>
              <button type="button" id="adminApplyDialsBtn" class="at-pill at-pill--solid" onclick="window.TinCanAdminTreasury && window.TinCanAdminTreasury.applyDials()">Apply Live</button>
            </div>
          </section>

          <section class="at-card" aria-label="Mint Requests and Manual Credit Grants">
            <span class="at-label">Manual Credit Grant &amp; Mint Queue</span>
            <div style="display:flex;gap:6px;align-items:center;">
              <input id="adminMintPeerInput" class="at-input" style="flex:1;" type="text" placeholder="peer_id (e.g. tc:maria91)" />
              <input id="adminMintAmtInput" class="at-input" style="width:92px;" type="number" min="1" step="10" value="500" />
              <button type="button" id="adminMintNowBtn" class="at-pill at-pill--solid" onclick="window.TinCanAdminTreasury && window.TinCanAdminTreasury.mintCredits()">Mint Credits</button>
            </div>
            <div id="adminMintQueueList" style="display:flex;flex-direction:column;gap:6px;margin-top:6px;">
              <div class="at-sub">No pending mint requests.</div>
            </div>
            <div id="adminStripeHealthBox" class="at-card at-card--celadon" style="margin-top:auto;padding:8px 10px;">
              <strong style="font-size:11px;">Stripe Webhook · HMAC Verified</strong>
              <span id="adminStripeHealthSub" class="at-sub">0 purchases in last 30 days</span>
            </div>
          </section>
        </div>

        <section class="at-card" aria-label="Global Margin and Upstream Audit Ledger">
          <span class="at-label">Global Margin &amp; Upstream Audit Ledger (All Peers)</span>
          <div class="at-table-wrap">
            <table class="at-table">
              <thead>
                <tr>
                  <th>Time</th>
                  <th>Peer / Role</th>
                  <th>Gateway / Model</th>
                  <th>Tokens</th>
                  <th>Upstream $</th>
                  <th>Billed $</th>
                  <th>Net Margin</th>
                </tr>
              </thead>
              <tbody id="adminAuditLedgerRows">
                <tr><td colspan="7" class="at-sub" style="text-align:center;padding:12px;">No global audit rows yet.</td></tr>
              </tbody>
            </table>
          </div>
        </section>
      </div>
    </div>"""


ADMIN_TREASURY_JS = r"""
    /* tc-admin-treasury-js */
    window.TinCanAdminTreasury = (function () {
      const state = { lastData: null, auditRows: [], paused: false };
      const el = (id) => (typeof document !== 'undefined' ? document.getElementById(id) : null);
      const esc = (v) => String(v == null ? '' : v).replace(/[&<>"']/g, (c) => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
      }[c]));

      function adminHeaders() {
        const headers = { 'Content-Type': 'application/json' };
        try {
          if (typeof localStorage !== 'undefined' && localStorage) {
            const key = localStorage.getItem('tincan_admin_key') || '';
            if (key) headers['X-Admin-Key'] = key;
          }
        } catch (e) {}
        return headers;
      }

      function previewDials() {
        const ms = el('adminMarkupSlider');
        const as = el('adminAdRewardSlider');
        const m = Math.max(1.0, Math.min(2.0, Number(ms ? ms.value : 1.25)));
        const gross = m > 1.0 ? ((m - 1.0) / m) * 100.0 : 0.0;
        const adCr = Math.max(0, Math.round(Number(as ? as.value : 25)));
        const cap = Number((state.lastData && state.lastData.dials && state.lastData.dials.daily_ad_cap) || 5);
        const mb = el('adminMarkupBadge');
        const ab = el('adminAdRewardBadge');
        if (mb) mb.textContent = `${m.toFixed(2)}x · ${gross.toFixed(1)}% GROSS MARGIN`;
        if (ab) ab.textContent = `${adCr} CR / clip × ${cap}/day = ${adCr * cap} CR`;
        return { markup_multiplier: m, ad_reward_credits: adCr };
      }

      function setMarkupPreset(mult) {
        const ms = el('adminMarkupSlider');
        if (ms) ms.value = Number(mult).toFixed(2);
        previewDials();
        return applyDials();
      }

      function currentPeerId() {
        if (typeof myPeerId !== 'undefined' && myPeerId) return myPeerId;
        try {
          if (typeof localStorage !== 'undefined' && localStorage) {
            return localStorage.getItem('tincan_peer_id') || '';
          }
        } catch (e) {}
        return '';
      }

      async function applyDials() {
        if (typeof fetch !== 'function') return null;
        const vals = previewDials();
        vals.peer_id = currentPeerId();
        const resp = await fetch('/api/admin/economy-dials', {
          method: 'POST',
          headers: adminHeaders(),
          body: JSON.stringify(vals),
        });
        const data = await resp.json().catch(() => ({}));
        if (resp.ok) {
          await refresh();
          if (window.TinCanTokenVault && window.TinCanTokenVault.refresh) {
            window.TinCanTokenVault.refresh();
          }
        }
        return data;
      }

      async function toggleCloudRouting() {
        if (typeof fetch !== 'function') return null;
        const resp = await fetch('/api/admin/cloud-routing', {
          method: 'POST',
          headers: adminHeaders(),
          body: JSON.stringify({ paused: !state.paused, peer_id: currentPeerId() }),
        });
        const data = await resp.json().catch(() => ({}));
        if (resp.ok) await refresh();
        return data;
      }

      async function mintCredits() {
        if (typeof fetch !== 'function') return null;
        const pEl = el('adminMintPeerInput');
        const aEl = el('adminMintAmtInput');
        const peer_id = pEl ? String(pEl.value || '').trim() : '';
        const tokens = aEl ? Math.max(1, parseInt(aEl.value || '0', 10)) : 0;
        if (!peer_id || !tokens) return null;
        const resp = await fetch('/api/tokens/mint', {
          method: 'POST',
          headers: adminHeaders(),
          body: JSON.stringify({ peer_id, tokens, amount_usd: Number((tokens / 120.0).toFixed(2)) }),
        });
        const data = await resp.json().catch(() => ({}));
        if (resp.ok) await refresh();
        return data;
      }

      function render(data) {
        if (!data || typeof data !== 'object') return;
        state.lastData = data;
        state.paused = Boolean(data.cloud_routing_paused);
        state.auditRows = Array.isArray(data.audit_ledger) ? data.audit_ledger : [];

        const killBtn = el('adminKillSwitchBtn');
        if (killBtn) {
          killBtn.textContent = state.paused ? '▶ Resume Cloud Routing' : '⏸ Pause Cloud Routing';
          killBtn.className = state.paused ? 'at-pill at-pill--pos' : 'at-pill at-pill--danger';
        }

        const pools = data.pools || {};
        const nano = pools.nanogpt || {};
        const orp = pools.openrouter || {};
        const rodin = pools.rodin || {};
        const st = data.stripe_30d || {};

        const nv = el('adminPoolNanoVal');
        const ns = el('adminPoolNanoSub');
        if (nv) nv.textContent = `$${Number(nano.account_remaining_balance_usd || 0).toFixed(2)}`;
        if (ns) ns.textContent = `${Number(nano.account_remaining_nano || 0).toFixed(2)} NANO · ${Number(nano.session_total_calls || 0)} calls`;

        const ov = el('adminPoolOrVal');
        const os = el('adminPoolOrSub');
        if (ov) ov.textContent = `$${Number(orp.account_remaining_balance_usd || 0).toFixed(2)}`;
        if (os) os.textContent = `$${Number(orp.key_usage_daily_usd || 0).toFixed(2)} today · ${orp.connected ? 'LIVE' : 'STANDBY'}`;

        const rv = el('adminPoolRodinVal');
        const rs = el('adminPoolRodinSub');
        if (rv) rv.textContent = `$${Number(rodin.account_remaining_balance_usd || 0).toFixed(2)}`;
        if (rs) rs.textContent = `${Number(rodin.account_remaining_credits || 0).toFixed(1)} CR · ${Number(rodin.session_total_tasks || 0)} tasks`;

        const mv = el('adminPoolMarginVal');
        const msSub = el('adminPoolMarginSub');
        if (mv) mv.textContent = `$${Number(st.net_after_stripe_usd || 0).toFixed(2)}`;
        if (msSub) msSub.textContent = `${Number(st.purchase_count || 0)} checkouts · $${Number(st.stripe_fees_usd || 0).toFixed(2)} Stripe fees`;

        const dials = data.dials || {};
        const mSlider = el('adminMarkupSlider');
        const aSlider = el('adminAdRewardSlider');
        const capVal = el('adminDailyCapVal');
        if (mSlider && dials.markup_multiplier != null) mSlider.value = Number(dials.markup_multiplier).toFixed(2);
        if (aSlider && dials.ad_reward_credits != null) aSlider.value = String(dials.ad_reward_credits);
        if (capVal && dials.daily_ad_cap != null) capVal.textContent = String(dials.daily_ad_cap);
        previewDials();

        const sh = el('adminStripeHealthSub');
        if (sh) sh.textContent = `${Number(st.purchase_count || 0)} checkouts ($${Number(st.gross_usd || 0).toFixed(2)} gross · ${Number(st.credits_sold || 0).toLocaleString()} CR sold)`;

        const mq = el('adminMintQueueList');
        const reqs = Array.isArray(data.pending_mint_requests) ? data.pending_mint_requests : [];
        if (mq) {
          if (!reqs.length) {
            mq.innerHTML = '<div class="at-sub">No pending mint requests.</div>';
          } else {
            mq.innerHTML = reqs.map((r) => (
              `<div style="display:flex;justify-content:space-between;align-items:center;padding:6px 8px;border:1px solid #b6bfb0;border-radius:8px;background:#f4f8f0;">` +
                `<span><strong>${esc(r.target_peer_id || r.peer_id)}</strong> · +${Number(r.tokens || 0).toLocaleString()} CR</span>` +
                `<span class="at-sub">${esc(r.reason || 'grant')}</span>` +
              `</div>`
            )).join('');
          }
        }

        const tbody = el('adminAuditLedgerRows');
        if (tbody) {
          if (!state.auditRows.length) {
            tbody.innerHTML = '<tr><td colspan="7" class="at-sub" style="text-align:center;padding:12px;">No global audit rows yet.</td></tr>';
          } else {
            const mult = Number(dials.markup_multiplier || 1.25);
            tbody.innerHTML = state.auditRows.map((row) => {
              const billed = Number(row.cost_usd || 0);
              const upstream = mult > 0 ? billed / mult : billed;
              const profit = Math.max(0, billed - upstream);
              const ts = row.timestamp ? new Date(Number(row.timestamp) * 1000).toTimeString().slice(0, 8) : '--:--:--';
              return (
                `<tr>` +
                  `<td class="at-mono">${esc(ts)}</td>` +
                  `<td>${esc(row.peer_id || '')} · <span class="at-sub">${esc(row.role_tier || 'free')}</span></td>` +
                  `<td class="at-mono">${esc(row.model || '')}</td>` +
                  `<td class="at-mono">${Number(row.total_tokens || 0).toLocaleString()}</td>` +
                  `<td class="at-mono">$${upstream.toFixed(4)}</td>` +
                  `<td class="at-mono">$${billed.toFixed(4)}</td>` +
                  `<td class="at-mono at-pos">+$${profit.toFixed(4)}</td>` +
                `</tr>`
              );
            }).join('');
          }
        }
      }

      async function refresh() {
        if (typeof fetch !== 'function') return state.lastData;
        const pid = currentPeerId();
        const q = pid ? `?peer_id=${encodeURIComponent(pid)}` : '';
        const resp = await fetch(`/api/admin/treasury${q}`, { headers: adminHeaders() });
        if (!resp || !resp.ok) return null;
        const data = await resp.json();
        render(data);
        return data;
      }

      function exportCsv() {
        const lines = ['timestamp,peer_id,role_tier,model,total_tokens,cost_usd'];
        (state.auditRows || []).forEach((r) => {
          lines.push([
            Number(r.timestamp || 0),
            `"${String(r.peer_id || '').replace(/"/g, '""')}"`,
            `"${String(r.role_tier || 'free').replace(/"/g, '""')}"`,
            `"${String(r.model || '').replace(/"/g, '""')}"`,
            Number(r.total_tokens || 0),
            Number(r.cost_usd || 0).toFixed(6),
          ].join(','));
        });
        return lines.join('\n') + '\n';
      }

      return { version: 1, refresh, render, previewDials, setMarkupPreset, applyDials, toggleCloudRouting, mintCredits, exportCsv };
    })();
"""


def apply_admin_treasury_ui(html: str) -> str:
    """Inject Admin Treasury CSS, Window HTML, and JS into ``html`` idempotently."""
    if not isinstance(html, str):
        return html
    if "/* tc-admin-treasury-css */" not in html and "</head>" in html:
        idx = html.find("</head>")
        html = f'{html[:idx]}<style id="tcAdminTreasuryCss">{ADMIN_TREASURY_CSS}</style>\n{html[idx:]}'
    if 'id="win-admin-treasury"' not in html and 'id="win-billing"' in html:
        marker = '<div id="win-billing"'
        idx = html.find(marker)
        html = f"{html[:idx]}{render_admin_treasury_window_html()}\n{html[idx:]}"
    if "/* tc-admin-treasury-js */" not in html and "</body>" in html:
        idx = html.rfind("</body>")
        html = f'{html[:idx]}<script id="tcAdminTreasuryJs">{ADMIN_TREASURY_JS}</script>\n{html[idx:]}'
    return html
