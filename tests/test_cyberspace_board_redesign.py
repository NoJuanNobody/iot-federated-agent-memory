"""Unit and Node.js runtime tests for Cyberspace Board Celadon redesign (Plan A)."""

from __future__ import annotations

import json
import os
import re
import subprocess
import tempfile

from iot_federated_agent_memory.mesh_os_ui import MESH_OS_HTML_UI
from iot_federated_agent_memory.window_chrome import legacy_palette_classes


def _extract_win_board_html() -> str:
    start = MESH_OS_HTML_UI.index('<div id="win-board"')
    end = MESH_OS_HTML_UI.index('<div id="win-network"', start)
    return MESH_OS_HTML_UI[start:end]


def _extract_board_script_block() -> str:
    scripts = re.findall(r"<script(?:\s+[^>]*)?>(.*?)</script>", MESH_OS_HTML_UI, flags=re.S | re.I)
    for script in scripts:
        if "function switchBoardTab(" in script and "async function loadBoardFeedAndThreads(" in script:
            return script
    raise AssertionError("Could not locate Cyberspace Board script block in MESH_OS_HTML_UI")


def _extract_js_segment(start_marker: str, end_marker: str) -> str:
    script = _extract_board_script_block()
    start = script.index(start_marker)
    end = script.index(end_marker, start)
    return script[start:end]


def _run_node(js_code: str) -> dict:
    with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as tf:
        tf.write(js_code)
        tf_path = tf.name
    try:
        proc = subprocess.run(["node", tf_path], capture_output=True, text=True)
        if proc.returncode != 0:
            raise AssertionError(f"Node script failed (rc={proc.returncode}): {proc.stderr}\nstdout={proc.stdout}")
        return json.loads(proc.stdout.strip())
    finally:
        if os.path.exists(tf_path):
            os.remove(tf_path)


def test_board_window_uses_celadon_and_ink_tokens():
    board_win = _extract_win_board_html()
    assert legacy_palette_classes(board_win) == []

    for token in (
        "bg-[#ecf1e6]",
        "bg-[#f4f8f0]",
        "bg-[#ffffff]",
        "border-[#111111]",
        "#107a47",
    ):
        assert token in board_win, f"Missing Celadon token {token!r} in #win-board"

    for required_id in (
        "boardTabBtn-discussions",
        "boardTabBtn-feed",
        "boardCuratedCountBadge",
        "boardTabBtn-graph",
        "boardTabBtn-verify",
        "boardUnifiedBar",
        "boardSearchInput",
        "boardSuggestList",
        "boardSortSelect",
        "boardAiSuggestBar",
        "boardAiSuggestionsBar",
        "boardAiModelBadge",
        "boardAiSuggestionChips",
        "boardFeedFilter-all",
        "boardFeedFilter-curated",
        "boardFeedFilter-solved",
        "boardFeedFilterInput",
        "boardCuratedFeedList",
        "boardActiveThreadsList",
        "boardGraphStatsBadge",
        "boardPendingVerifyCount",
    ):
        assert f'id="{required_id}"' in board_win


def test_board_ai_suggest_bar_always_visible_and_updates_live_in_node():
    board_win = _extract_win_board_html()
    unified_idx = board_win.index('id="boardUnifiedBar"')
    ai_bar_idx = board_win.index('id="boardAiSuggestBar"')
    suggest_list_idx = board_win.index('id="boardSuggestList"')
    assert unified_idx < ai_bar_idx < suggest_list_idx

    ai_bar_open_tag = board_win[ai_bar_idx - 20 : ai_bar_idx + 120]
    assert "hidden" not in ai_bar_open_tag
    for default_chip in ("[#graphrag]", "[@gemini-brain]", "[/search bm25]", "[/thread + New]"):
        assert default_chip in board_win

    js_ai_funcs = _extract_js_segment(
        "async function loadBoardAiSuggestions(",
        "async function onBoardSearchInput(",
    )
    js_helpers = """
    let boardSearchTokens = [];
    function escapeHtml(s) {
      return String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
    }
    function addBoardChip(tok) { if (!boardSearchTokens.includes(tok)) boardSearchTokens.push(tok); }
    function searchCyberspaceBoard() {}
    function submitBoardOmniInput() {}
    """
    node_script = (
        """
    const elements = {
      boardSearchInput: { value: 'bm25', focused: false, focus() { this.focused = true; } },
      boardAiSuggestBar: { className: 'px-3 py-2 bg-[#f4f8f0]', classList: { add(){}, remove(){}, contains(){ return false; } } },
      boardAiSuggestionChips: { innerHTML: '' },
      boardAiModelBadge: { textContent: '' },
    };
    const document = { getElementById(id) { return elements[id] || null; } };
    const fetchCalls = [];
    async function fetch(url, opts) {
      fetchCalls.push({ url, opts });
      return {
        ok: true,
        async json() {
          return {
            model: 'google/gemini-2.0-flash-exp:free',
            is_free: true,
            used_live_llm: true,
            suggestions: [
              { token: '#bm25', reason: 'Tag match' },
              { token: '@gemini-brain', reason: 'Agent helper' },
              { token: '/search bm25 graphrag', reason: 'Hybrid search' },
            ],
          };
        }
      };
    }
    """
        + js_helpers
        + "\n"
        + js_ai_funcs
        + """
    (async () => {
      await loadBoardAiSuggestions(false, 'bm25');
      const chipsHtmlAfterFetch = elements.boardAiSuggestionChips.innerHTML;
      const badgeAfterFetch = elements.boardAiModelBadge.textContent;
      applyBoardAiSuggestion('[#bm25]');
      const inputValAfterChip = elements.boardSearchInput.value;
      const tokensAfterChip = boardSearchTokens.slice();
      applyBoardAiSuggestion('/thread ');
      const inputValAfterThread = elements.boardSearchInput.value;
      console.log(JSON.stringify({
        fetchCalls,
        chipsHtmlAfterFetch,
        badgeAfterFetch,
        inputValAfterChip,
        tokensAfterChip,
        inputValAfterThread,
        suggestBarHidden: elements.boardAiSuggestBar.className.includes('hidden'),
      }));
    })();
    """
    )
    out = _run_node(node_script)
    assert len(out["fetchCalls"]) == 1
    assert "/api/board/ai-suggest?q=bm25" in out["fetchCalls"][0]["url"]
    assert "gemini-2.0-flash-exp:free" in out["badgeAfterFetch"]
    assert "Free LLM $0" in out["badgeAfterFetch"]
    assert "[#bm25]" in out["chipsHtmlAfterFetch"]
    assert "[@gemini-brain]" in out["chipsHtmlAfterFetch"]
    assert "[/search bm25 graphrag]" in out["chipsHtmlAfterFetch"]
    assert "bg-[#ffffff]" in out["chipsHtmlAfterFetch"]
    assert out["tokensAfterChip"] == ["#bm25"]
    assert out["inputValAfterThread"] == "/thread "
    assert out["suggestBarHidden"] is False


def test_load_board_feed_and_threads_runtime_parity_in_node():
    js_feed = _extract_js_segment(
        "let boardFeedFilter = 'all';",
        "function openBoardThreadFromFeed(",
    )
    js_helpers = """
    let _boardTopicsById = {};
    function escapeHtml(s) {
      return String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
    }
    """
    node_script = (
        """
    function makeEl(id) {
      return {
        id,
        innerHTML: '',
        textContent: '',
        value: '',
        className: '',
        classList: { add(){}, remove(){}, contains(){ return false; } },
      };
    }
    const elements = {
      boardCuratedFeedList: makeEl('boardCuratedFeedList'),
      boardActiveThreadsList: makeEl('boardActiveThreadsList'),
      boardFeedStatusMeta: makeEl('boardFeedStatusMeta'),
      boardFeedFilterInput: makeEl('boardFeedFilterInput'),
      'boardFeedFilter-all': makeEl('boardFeedFilter-all'),
      'boardFeedFilter-curated': makeEl('boardFeedFilter-curated'),
      'boardFeedFilter-solved': makeEl('boardFeedFilter-solved'),
      boardCuratedCountBadge: makeEl('boardCuratedCountBadge'),
    };
    const document = { getElementById(id) { return elements[id] || null; } };
    const sampleTopics = [
      {
        topic_id: 'topic_a',
        title: 'Hybrid BM25 + GraphRAG Benchmark',
        body: 'Comparing BM25 lexical scoring with 2-hop graph walks.',
        author_username: 'alejandro',
        curated: true,
        resolved: false,
        activity_score: 92,
        upvotes: 14,
        tags: ['bm25', 'graphrag'],
        posts: [
          { post_id: 'p1', author_username: 'oldpeer', body: 'Older first reply should not crowd top-2 preview' },
          { post_id: 'p2', author_username: 'maya', body: 'Verified recall jump on multi-hop queries.' },
          { post_id: 'p3', author_username: 'gemini-brain', is_agent: true, body: 'Suggested boosting entity-overlap alpha to 0.35.' },
        ],
      },
      {
        topic_id: 'topic_b',
        title: 'Zero-Account Ed25519 Key Rotation',
        body: 'Rotating subkeys cleanly across peers.',
        author_username: 'nina',
        curated: false,
        resolved: true,
        accepted_post_id: 'pb1',
        activity_score: 48,
        upvotes: 9,
        tags: ['crypto'],
        posts: [
          { post_id: 'pb1', author_username: 'ai:verifier-helper', body: 'Confirmed Ed25519 signature chain.' },
        ],
      },
      {
        topic_id: 'topic_c',
        title: 'Peer Mesh Relay Telemetry',
        body: 'Latency histogram over WebRTC mesh.',
        author_username: 'sam',
        curated: true,
        resolved: false,
        activity_score: 12,
        upvotes: 3,
        tags: ['webrtc'],
        posts: [],
      },
    ];
    async function fetch() {
      return { ok: true, async json() { return { topics: sampleTopics }; } };
    }
    """
        + js_helpers
        + "\n"
        + js_feed
        + """
    (async () => {
      await loadBoardFeedAndThreads();
      const firstPass = {
        allLabel: elements['boardFeedFilter-all'].textContent,
        curatedLabel: elements['boardFeedFilter-curated'].textContent,
        solvedLabel: elements['boardFeedFilter-solved'].textContent,
        curatedBadge: elements.boardCuratedCountBadge.textContent,
        feedHtml: elements.boardCuratedFeedList.innerHTML,
        threadsHtml: elements.boardActiveThreadsList.innerHTML,
      };
      setBoardFeedFilter('solved');
      await loadBoardFeedAndThreads();
      const solvedPass = {
        allLabel: elements['boardFeedFilter-all'].textContent,
        curatedLabel: elements['boardFeedFilter-curated'].textContent,
        solvedLabel: elements['boardFeedFilter-solved'].textContent,
        solvedBtnClass: elements['boardFeedFilter-solved'].className,
        allBtnClass: elements['boardFeedFilter-all'].className,
        statusMeta: elements.boardFeedStatusMeta.textContent,
        feedHtml: elements.boardCuratedFeedList.innerHTML,
        threadsHtml: elements.boardActiveThreadsList.innerHTML,
      };
      console.log(JSON.stringify({ firstPass, solvedPass }));
    })();
    """
    )
    out = _run_node(node_script)
    fp = out["firstPass"]
    assert fp["allLabel"] == "All (3)"
    assert fp["curatedLabel"] == "★ Curated (2)"
    assert fp["solvedLabel"] == "✓ Solved (1)"
    assert fp["curatedBadge"] == "2"

    feed_html = fp["feedHtml"]
    assert "ACTIVITY SCORE 92" in feed_html
    assert "[Load in Workstation]" in feed_html
    assert "loadTopicIntoWorkstation('topic_a')" in feed_html
    assert "★ CURATED" in feed_html
    assert "✓ SOLVED" in feed_html

    threads_html = fp["threadsHtml"]
    assert "#1 MOST ACTIVE · ACTIVITY SCORE 92" in threads_html
    assert "Older first reply should not crowd top-2 preview" not in threads_html
    assert "Verified recall jump on multi-hop queries." in threads_html
    assert "[AI] @gemini-brain" in threads_html
    assert "Suggested boosting entity-overlap alpha to 0.35." in threads_html
    assert 'id="threadQuickReply-topic_a"' in threads_html
    assert "#2 · ACTIVITY SCORE 48" in threads_html
    assert 'id="threadQuickReply-topic_b"' in threads_html

    sp = out["solvedPass"]
    assert sp["allLabel"] == "All (3)"
    assert sp["curatedLabel"] == "★ Curated (2)"
    assert sp["solvedLabel"] == "✓ Solved (1)"
    assert "bg-[#111111]" in sp["solvedBtnClass"]
    assert "text-[#ecf1e6]" in sp["solvedBtnClass"]
    assert "bg-[#f4f8f0]" in sp["allBtnClass"]
    assert sp["statusMeta"] == "1 topic(s) · solved"
    assert "[AI] @ai:verifier-helper" in sp["threadsHtml"]


def test_load_topic_into_workstation_opens_agentspace_and_triggers_load_in_node():
    js_ws = _extract_js_segment(
        "function openAgentSpaceWithTopic(",
        "function openBoardThreadFromFeed(",
    )
    node_script = (
        """
    async function runCases() {
      // Case 1: topic cached, win-agentspace closed, selectWorkstationTopicResult exists
      const calls1 = { toggled: [], finderTabs: [], selectedTopics: [], toasts: [], fetches: [] };
      let _boardTopicsById = { topic_cached: { topic_id: 'topic_cached', title: 'Cached Graph Topic' } };
      let spWin1 = {
        style: { display: 'none' },
        classList: { contains: (c) => c === 'hidden', remove(){} },
      };
      let document = { getElementById: (id) => (id === 'win-agentspace' ? spWin1 : null) };
      let fetch = async (url) => { calls1.fetches.push(url); return { ok: false }; };
      let toggleWindow = (id) => calls1.toggled.push(id);
      let bringToFront = () => {};
      let switchFinderTab = (t) => calls1.finderTabs.push(t);
      let selectWorkstationTopicResult = (tid) => calls1.selectedTopics.push(tid);
      let switchSpaceScope, resolveAndLoadSpaceOwner;
      let showQuickNotification = (msg) => calls1.toasts.push(msg);
      """
        + js_ws
        + """
      await loadTopicIntoWorkstation('topic_cached');

      // Case 2: uncached topic fetched from /api/board/topic, win-agentspace open, fallback loader
      const calls2 = { brought: 0, finderTabs: [], scopes: [], resolved: 0, fetches: [], ownerVal: '' };
      _boardTopicsById = {};
      const ownerInput = { value: '' };
      const spWin2 = {
        style: { display: 'flex' },
        classList: { contains: () => false, remove(){} },
      };
      document = {
        getElementById: (id) => {
          if (id === 'win-agentspace') return spWin2;
          if (id === 'spaceOwnerInput') return ownerInput;
          return null;
        }
      };
      fetch = async (url) => {
        calls2.fetches.push(url);
        return {
          ok: true,
          async json() {
            return { status: 'ok', topic: { topic_id: 'topic_remote', title: 'Remote Topic' } };
          }
        };
      };
      bringToFront = () => { calls2.brought += 1; };
      switchFinderTab = (t) => calls2.finderTabs.push(t);
      selectWorkstationTopicResult = undefined;
      switchSpaceScope = (s) => calls2.scopes.push(s);
      resolveAndLoadSpaceOwner = () => { calls2.resolved += 1; calls2.ownerVal = ownerInput.value; };
      showQuickNotification = () => {};

      await loadTopicIntoWorkstation('topic_remote');
      console.log(JSON.stringify({ calls1, calls2 }));
    }
    runCases();
    """
    )
    out = _run_node(node_script)
    c1 = out["calls1"]
    assert c1["fetches"] == []
    assert c1["toggled"] == ["win-agentspace"]
    assert c1["finderTabs"] == ["files"]
    assert c1["selectedTopics"] == ["topic_cached"]
    assert c1["toasts"] == ["📂 Loaded Cached Graph Topic in Workstation"]

    c2 = out["calls2"]
    assert c2["fetches"] == ["/api/board/topic?id=topic_remote&increment_views=0"]
    assert c2["brought"] == 1
    assert c2["finderTabs"] == ["files"]
    assert c2["scopes"] == ["topic"]
    assert c2["resolved"] == 1
    assert c2["ownerVal"] == "topic_remote"


def test_switch_board_tab_and_render_cyberspace_topics_celadon_parity_in_node():
    js_tabs = _extract_js_segment(
        "function switchBoardTab(",
        "function setBoardCategoryFilter(",
    )
    js_feed = _extract_js_segment(
        "let boardFeedFilter = 'all';",
        "function openBoardThreadFromFeed(",
    )
    js_render = _extract_js_segment(
        "function setReplyToNestedPost(",
        "function toggleBoardTopicThread(",
    )
    js_mentions = _extract_js_segment(
        "function formatBoardMentions(",
        "function insertBoardTag(",
    )
    node_script = (
        """
    function makeEl(id) {
      const classes = new Set();
      return {
        id,
        className: '',
        innerHTML: '',
        classList: {
          add(...args) { args.forEach(c => classes.add(c)); },
          remove(...args) { args.forEach(c => classes.delete(c)); },
          contains(c) { return classes.has(c); },
          toggle(c, force) {
            if (force === undefined) {
              if (classes.has(c)) { classes.delete(c); return false; }
              classes.add(c); return true;
            }
            if (force) classes.add(c); else classes.delete(c);
            return Boolean(force);
          },
        },
        _classes: classes,
      };
    }
    const elements = {
      'boardTab-discussions': makeEl('boardTab-discussions'),
      'boardTab-feed': makeEl('boardTab-feed'),
      'boardTab-graph': makeEl('boardTab-graph'),
      'boardTab-verify': makeEl('boardTab-verify'),
      'boardTabBtn-discussions': makeEl('boardTabBtn-discussions'),
      'boardTabBtn-feed': makeEl('boardTabBtn-feed'),
      'boardTabBtn-graph': makeEl('boardTabBtn-graph'),
      'boardTabBtn-verify': makeEl('boardTabBtn-verify'),
      boardTopicsFeed: makeEl('boardTopicsFeed'),
    };
    const document = { getElementById: (id) => elements[id] || null };
    const localStorage = { getItem: () => 'alejandro' };
    let _boardTopicsById = {};
    let activeBoardTab = 'discussions';
    let activeBoardTopicId = null;
    let isAdmin = false;
    let myPeerId = 'peer-1';
    async function fetch() { return { ok: false, async json() { return {}; } }; }
    function escapeHtml(s) {
      return String(s ?? '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
    }
    function loadAndDrawBoardGraph() {}
    function prefillVerificationFormDefaults() {}
    function loadVerificationCenterData() {}
    """
        + js_tabs
        + "\n"
        + js_feed
        + "\n"
        + js_mentions
        + "\n"
        + js_render
        + """
    switchBoardTab('feed');
    const feedTabBtnClass = elements['boardTabBtn-feed'].className;
    const discTabBtnClass = elements['boardTabBtn-discussions'].className;
    renderCyberspaceTopics([
      {
        topic_id: 't_celadon',
        title: 'Celadon Thread Render',
        body: 'Ping @gemini-brain and #graphrag',
        author_username: 'alejandro',
        author_verified: true,
        curated: true,
        resolved: true,
        score: 0.91,
        bm25_score: 0.72,
        graphrag_score: 0.88,
        matched_terms: ['graphrag'],
        tags: ['graphrag'],
        posts: [
          { post_id: 'p1', author_username: 'gemini-brain', is_agent: true, is_accepted: true, upvotes: 5, body: 'Verified #graphrag traversal.' }
        ],
      }
    ], true);
    console.log(JSON.stringify({
      feedTabBtnClass,
      discTabBtnClass,
      renderedFeedHtml: elements.boardTopicsFeed.innerHTML,
    }));
    """
    )
    out = _run_node(node_script)
    assert "bg-[#111111]" in out["feedTabBtnClass"]
    assert "text-[#ecf1e6]" in out["feedTabBtnClass"]
    assert "bg-[#ffffff]" in out["discTabBtnClass"]
    assert "text-[#111111]" in out["discTabBtnClass"]

    rendered = out["renderedFeedHtml"]
    assert legacy_palette_classes(rendered) == []
    assert "loadTopicIntoWorkstation('t_celadon')" in rendered
    assert "[Load in Workstation]" in rendered
    assert "[AI] @gemini-brain" in rendered
    assert "ubar-rank-mini" in rendered
    assert "how this ranked" in rendered
    assert 'id="boardThread-t_celadon"' in rendered
    assert 'id="replyInput-t_celadon"' in rendered
