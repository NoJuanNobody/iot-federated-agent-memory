"""Plan C: Arena floating vote modal polish, persistent summary badge, and mobile CSS."""

from __future__ import annotations

import json
import re
import shutil
import subprocess

from iot_federated_agent_memory.arena_duel_ui import (
    ARENA_DUEL_RESPONSIVE_CSS,
    ARENA_DUEL_SCRIPT,
    apply_arena_duel,
    render_arena_duel,
)
from iot_federated_agent_memory.mesh_os_ui import MESH_OS_HTML_UI
from iot_federated_agent_memory.window_chrome import legacy_palette_classes


def _extract_js_range(source: str, start_anchor: str, end_anchor: str) -> str:
    i0 = source.index(start_anchor)
    i1 = source.index(end_anchor, i0 + len(start_anchor))
    return source[i0:i1]


def test_custom_prefix_invariant_and_last_vote_badge_placement():
    custom = render_arena_duel("customArena", "Custom")
    custom_ids = set(re.findall(r'\bid="([^"]+)"', custom))

    expected_badge_ids = {
        "customArenaLastVoteBadge",
        "customArenaLastVoteText",
        "customArenaReopenVoteBtn",
    }
    assert expected_badge_ids <= custom_ids
    assert all(eid.startswith("customArena") for eid in custom_ids)

    # Summary bar lives inside BattleBox right above ProStrip and starts hidden.
    badge_idx = custom.index('id="customArenaLastVoteBadge"')
    form_end_idx = custom.index("</form>")
    pro_idx = custom.index('id="customArenaProStrip"')
    assert form_end_idx < badge_idx < pro_idx
    badge_tag = custom[custom.rfind("<div", 0, badge_idx) : custom.find(">", badge_idx) + 1]
    assert "hidden" in badge_tag
    assert 'data-arena-last-vote-badge="customArena"' in badge_tag
    assert 'onclick="arenaDuelReopenVote(\'customArena\')"' in custom
    assert "Re-open Vote Popup" in custom

    # Both rendered Arena views in MESH_OS_HTML_UI carry the badge and Celadon tokens only.
    for prefix in ("arenaWin", "arena"):
        assert f'id="{prefix}LastVoteBadge"' in MESH_OS_HTML_UI
        assert f'id="{prefix}LastVoteText"' in MESH_OS_HTML_UI
        assert f'id="{prefix}ReopenVoteBtn"' in MESH_OS_HTML_UI
        assert MESH_OS_HTML_UI.count(f'id="{prefix}LastVoteBadge"') == 1

    assert legacy_palette_classes(custom) == []
    assert legacy_palette_classes(ARENA_DUEL_RESPONSIVE_CSS) == []
    assert legacy_palette_classes(ARENA_DUEL_SCRIPT) == []


def test_responsive_vote_modal_css_emitted_once_and_idempotent():
    assert MESH_OS_HTML_UI.count('id="arenaDuelResponsiveCss"') == 1
    assert MESH_OS_HTML_UI.count('id="arenaDuelScript"') == 1

    css_match = re.search(
        r'<style id="arenaDuelResponsiveCss">(.*?)</style>',
        MESH_OS_HTML_UI,
        flags=re.DOTALL,
    )
    assert css_match, "arenaDuelResponsiveCss <style> block missing from MESH_OS_HTML_UI"
    css = css_match.group(1)
    assert "@media (max-width: 640px)" in css
    assert "[data-arena-vote-modal]" in css
    for prop in (
        "left: 0.75rem !important;",
        "right: 0.75rem !important;",
        "width: auto !important;",
        "max-width: none !important;",
        "bottom: 4.5rem !important;",
    ):
        assert prop in css

    # Idempotency on standalone HTML pages
    page = "<html><body><!--ARENA_DUEL:customMob--></body></html>"
    once = apply_arena_duel(page)
    assert once.count('id="arenaDuelResponsiveCss"') == 1
    assert once.count('id="arenaDuelScript"') == 1
    assert 'id="customMobLastVoteBadge"' in once

    twice = apply_arena_duel(once)
    assert twice == once

    # Adding another marker onto a page that already has CSS & script never duplicates them.
    with_second = twice.replace("</body>", "<!--ARENA_DUEL:extraMob--></body>")
    applied_second = apply_arena_duel(with_second)
    assert applied_second.count('id="arenaDuelResponsiveCss"') == 1
    assert applied_second.count('id="arenaDuelScript"') == 1
    assert 'id="extraMobLastVoteBadge"' in applied_second


def test_all_mesh_os_inline_scripts_pass_node_syntax_check():
    node_bin = shutil.which("node")
    assert node_bin, "node binary required to syntax-check inline scripts"
    scripts = re.findall(
        r"<script\b(?![^>]*\bsrc=)[^>]*>(.*?)</script>",
        MESH_OS_HTML_UI,
        flags=re.DOTALL | re.IGNORECASE,
    )
    assert len(scripts) >= 1
    for idx, body in enumerate(scripts):
        proc = subprocess.run(
            [node_bin, "--check", "-"],
            input=body,
            capture_output=True,
            text=True,
        )
        assert proc.returncode == 0, f"Inline script #{idx} failed node --check:\n{proc.stderr}"


def test_last_vote_badge_full_lifecycle_in_node():
    node_bin = shutil.which("node")
    assert node_bin, "node binary required to test arena_duel_ui vote polish JS"

    duel_js = _extract_js_range(
        ARENA_DUEL_SCRIPT,
        "const VIEWS = __ARENA_VIEWS__;",
        "function boot()",
    ).replace("__ARENA_VIEWS__", '["arenaWin", "arena"]')

    harness = f"""
    function makeEl(id, extra) {{
      const classes = new Set();
      return Object.assign({{
        id,
        value: '',
        textContent: '',
        checked: false,
        disabled: false,
        parentNode: null,
        style: {{}},
        focus() {{}},
        classList: {{
          add(c) {{ classes.add(c); }},
          remove(c) {{ classes.delete(c); }},
          contains(c) {{ return classes.has(c); }},
        }},
      }}, extra || {{}});
    }}
    const elems = {{}};
    for (const p of ['arenaWin', 'arena']) {{
      elems[p + 'PromptInput'] = makeEl(p + 'PromptInput', {{ value: 'Compare local vs cloud' }});
      elems[p + 'RunBtn'] = makeEl(p + 'RunBtn');
      elems[p + 'ModelAInput'] = makeEl(p + 'ModelAInput', {{ value: 'gemini-brain' }});
      elems[p + 'ModelBInput'] = makeEl(p + 'ModelBInput', {{ value: 'claude-brain' }});
      elems[p + 'AgentA'] = makeEl(p + 'AgentA', {{ value: 'brain-a' }});
      elems[p + 'AgentB'] = makeEl(p + 'AgentB', {{ value: 'brain-b' }});
      elems[p + 'UseCtxA'] = makeEl(p + 'UseCtxA', {{ checked: true }});
      elems[p + 'UseCtxB'] = makeEl(p + 'UseCtxB', {{ checked: true }});
      elems[p + 'PreAuthCap'] = makeEl(p + 'PreAuthCap');
      elems[p + 'ResultA'] = makeEl(p + 'ResultA');
      elems[p + 'ResultB'] = makeEl(p + 'ResultB');
      elems[p + 'BillA'] = makeEl(p + 'BillA');
      elems[p + 'BillB'] = makeEl(p + 'BillB');
      elems[p + 'SavingsA'] = makeEl(p + 'SavingsA');
      elems[p + 'SavingsB'] = makeEl(p + 'SavingsB');
      elems[p + 'VoteForm'] = makeEl(p + 'VoteForm');
      elems[p + 'VoteCardA'] = makeEl(p + 'VoteCardA');
      elems[p + 'VoteCardB'] = makeEl(p + 'VoteCardB');
      elems[p + 'VotePickA'] = makeEl(p + 'VotePickA');
      elems[p + 'VotePickB'] = makeEl(p + 'VotePickB');
      elems[p + 'VoteModalPrompt'] = makeEl(p + 'VoteModalPrompt');
      elems[p + 'VoteTagSelect'] = makeEl(p + 'VoteTagSelect', {{ value: 'Faster & cleaner' }});
      elems[p + 'VoteReasonInput'] = makeEl(p + 'VoteReasonInput', {{ value: 'Clear mobile spacing' }});
      elems[p + 'VoteStatus'] = makeEl(p + 'VoteStatus');
      elems[p + 'LastVoteBadge'] = makeEl(p + 'LastVoteBadge');
      elems[p + 'LastVoteText'] = makeEl(p + 'LastVoteText', {{ textContent: 'Duel ready · Cast vote (+150 XP)' }});
      elems[p + 'ReopenVoteBtn'] = makeEl(p + 'ReopenVoteBtn');
      elems[p + 'VoteForm'].classList.add('hidden');
      elems[p + 'LastVoteBadge'].classList.add('hidden');
      elems[p + 'ReopenVoteBtn'].classList.add('hidden');
    }}
    const document = {{
      getElementById: (id) => elems[id] || null,
      addEventListener() {{}},
      body: {{
        appendChild(node) {{ node.parentNode = this; }},
      }},
    }};
    const window = {{}};
    const localStorage = {{ getItem: () => '', setItem() {{}} }};
    const currentRoom = 'main';
    const myPeerId = 'peer-polish';
    let matchCounter = 0;
    let failMatch = false;
    function fetch(url, opts) {{
      const parsed = JSON.parse((opts && opts.body) || '{{}}');
      if (url === '/api/mesh/arena/match') {{
        if (failMatch) {{
          return Promise.resolve({{ ok: false, status: 402, json: async () => ({{ error: 'Low balance' }}) }});
        }}
        matchCounter += 1;
        return Promise.resolve({{ ok: true, status: 200, json: async () => ({{ match: {{ match_id: 'm_polish_' + matchCounter }} }}) }});
      }}
      if (url === '/api/chat') {{
        return Promise.resolve({{ ok: true, status: 200, json: async () => ({{
          id: 'resp-' + parsed.arena_side,
          choices: [{{ message: {{ content: 'Output ' + parsed.arena_side }} }}],
          billing: {{ cost_usd: 0.001, tokens_billed: 64, match_total_cost_usd: 0.002 }},
        }}) }});
      }}
      return Promise.resolve({{ ok: true, status: 200, json: async () => ({{ status: 'voted' }}) }});
    }}
    {duel_js}
    (async () => {{
      const p = 'arenaWin';
      const initialBadgeHidden = elems[p + 'LastVoteBadge'].classList.contains('hidden');
      const initialReopenHidden = elems[p + 'ReopenVoteBtn'].classList.contains('hidden');

      // Dismissing before any run leaves badge hidden; reopen returns false.
      window.arenaDuelCloseVoteModal(p);
      const badgeStillHiddenBeforeRun = elems[p + 'LastVoteBadge'].classList.contains('hidden');
      const reopenBeforeRun = window.arenaDuelReopenVote(p);

      // Run #1 opens popup; badge stays hidden until dismissed or voted.
      await window.arenaDuelRun(p);
      const modalOpenAfterRun1 = !elems[p + 'VoteForm'].classList.contains('hidden');
      const badgeHiddenWhileModalOpen = elems[p + 'LastVoteBadge'].classList.contains('hidden');

      // Dismiss after completed run -> shows dismissed summary + Re-open button.
      window.arenaDuelCloseVoteModal(p);
      const modalClosedAfterDismiss = elems[p + 'VoteForm'].classList.contains('hidden');
      const badgeVisibleAfterDismiss = !elems[p + 'LastVoteBadge'].classList.contains('hidden');
      const reopenVisibleAfterDismiss = !elems[p + 'ReopenVoteBtn'].classList.contains('hidden');
      const dismissedText = elems[p + 'LastVoteText'].textContent;

      // Re-open popup -> popup opens, dismissed badge hides again.
      const reopenReturn = window.arenaDuelReopenVote(p);
      const modalReopened = !elems[p + 'VoteForm'].classList.contains('hidden');
      const badgeHiddenOnReopen = elems[p + 'LastVoteBadge'].classList.contains('hidden');

      // Select Brain A, dismiss again, then re-open -> selection A is preserved.
      window.arenaDuelSelectVoteSide(p, 'A');
      window.arenaDuelCloseVoteModal(p);
      window.arenaDuelReopenVote(p);
      const preservedPickA = elems[p + 'VotePickA'].checked;

      // Switch to Brain B and submit with feedback.
      window.arenaDuelSelectVoteSide(p, 'B');
      await window.arenaDuelSubmitVote(p);
      const modalHiddenAfterSubmit = elems[p + 'VoteForm'].classList.contains('hidden');
      const badgeVisibleAfterSubmit = !elems[p + 'LastVoteBadge'].classList.contains('hidden');
      const reopenHiddenAfterSubmit = elems[p + 'ReopenVoteBtn'].classList.contains('hidden');
      const votedText = elems[p + 'LastVoteText'].textContent;
      const votedBadgeCls = elems[p + 'LastVoteBadge'].className;

      // Calling closeVoteModal after already voting does NOT clobber the recorded vote badge.
      window.arenaDuelCloseVoteModal(p);
      const votedTextPreservedAfterClose = elems[p + 'LastVoteText'].textContent;

      // Starting a fresh run (even if match fails) resets badge to hidden immediately.
      failMatch = true;
      await window.arenaDuelRun(p);
      const badgeResetHiddenOnNewRun = elems[p + 'LastVoteBadge'].classList.contains('hidden');
      const reopenResetHiddenOnNewRun = elems[p + 'ReopenVoteBtn'].classList.contains('hidden');
      const textResetOnNewRun = elems[p + 'LastVoteText'].textContent;

      // Also test second view ('arena') without feedback note.
      failMatch = false;
      elems['arenaVoteTagSelect'].value = '';
      elems['arenaVoteReasonInput'].value = '';
      await window.arenaDuelRun('arena');
      window.arenaDuelSelectVoteSide('arena', 'A');
      await window.arenaDuelSubmitVote('arena');
      const questVotedText = elems['arenaLastVoteText'].textContent;

      console.log(JSON.stringify({{
        initialBadgeHidden,
        initialReopenHidden,
        badgeStillHiddenBeforeRun,
        reopenBeforeRun,
        modalOpenAfterRun1,
        badgeHiddenWhileModalOpen,
        modalClosedAfterDismiss,
        badgeVisibleAfterDismiss,
        reopenVisibleAfterDismiss,
        dismissedText,
        reopenReturn,
        modalReopened,
        badgeHiddenOnReopen,
        preservedPickA,
        modalHiddenAfterSubmit,
        badgeVisibleAfterSubmit,
        reopenHiddenAfterSubmit,
        votedText,
        votedBadgeCls,
        votedTextPreservedAfterClose,
        badgeResetHiddenOnNewRun,
        reopenResetHiddenOnNewRun,
        textResetOnNewRun,
        questVotedText,
      }}));
    }})();
    """
    proc = subprocess.run([node_bin, "-e", harness], capture_output=True, text=True, check=True)
    out = json.loads(proc.stdout)

    assert out["initialBadgeHidden"] is True
    assert out["initialReopenHidden"] is True
    assert out["badgeStillHiddenBeforeRun"] is True
    assert out["reopenBeforeRun"] is False
    assert out["modalOpenAfterRun1"] is True
    assert out["badgeHiddenWhileModalOpen"] is True
    assert out["modalClosedAfterDismiss"] is True
    assert out["badgeVisibleAfterDismiss"] is True
    assert out["reopenVisibleAfterDismiss"] is True
    assert out["dismissedText"] == "Duel ready · Cast vote (+150 XP)"
    assert out["reopenReturn"] is True
    assert out["modalReopened"] is True
    assert out["badgeHiddenOnReopen"] is True
    assert out["preservedPickA"] is True
    assert out["modalHiddenAfterSubmit"] is True
    assert out["badgeVisibleAfterSubmit"] is True
    assert out["reopenHiddenAfterSubmit"] is True
    assert "🏆 Last Vote: Brain B (claude-brain) · +150 XP" in out["votedText"]
    assert "Faster & cleaner — Clear mobile spacing" in out["votedText"]
    assert "#107a47" in out["votedBadgeCls"]
    assert out["votedTextPreservedAfterClose"] == out["votedText"]
    assert out["badgeResetHiddenOnNewRun"] is True
    assert out["reopenResetHiddenOnNewRun"] is True
    assert out["textResetOnNewRun"] == ""
    assert out["questVotedText"] == "🏆 Last Vote: Brain A (gemini-brain) · +150 XP"
