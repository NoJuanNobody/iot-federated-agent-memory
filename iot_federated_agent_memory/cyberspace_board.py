#!/usr/bin/env python3
"""
Cyberspace Discussion Board, Hybrid BM25 + GraphRAG Knowledge Base,
and Autonomous Identity Verification Agent (@verifier-agent) for TinCan Mesh OS.

Features:
1. Discussion Board with Topics & Threaded Replies:
   - Self-tagging & peer username mentions (@username)
   - AI Agent tagging (@gemini-brain, @claude-brain, @grok-brain, @openai-brain, @verifier-agent)
   - Automatic AI Agent thread participation when tagged
   - Concept / topic hashtags (#cyberspace, #graphrag, #bm25, etc.)
2. Information Retrieval with Okapi BM25:
   - Exact IDF, TF saturation (k1=1.5), and document length normalization (b=0.75)
   - Per-term score breakdown and matched snippet highlighting
3. GraphRAG Knowledge Base Search:
   - Multi-relational Knowledge Graph over Topics, Posts, @Users, @Agents, and #Tags
   - 1-hop and 2-hop personalized subgraph traversal + Hybrid BM25+GraphRAG ranking
   - Contextual GraphRAG synthesis explaining cross-topic and cross-agent connections
4. Identity Verification Agent (@verifier-agent):
   - Dispatches structured verification forms to unverified peers / usernames
   - Validates and attests completed forms, syncing with PeerAccountRegistry
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import re
import sqlite3
import threading
import time
import uuid
from collections import Counter, defaultdict
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

KNOWN_AI_AGENTS: Dict[str, Dict[str, str]] = {
    "gemini-brain": {
        "alias": "gemini-brain",
        "display_name": "Gemini 2.5 Flash (@gemini-brain)",
        "specialty": "GraphRAG synthesis, multimodal systems, and high-speed cyberspace indexing",
    },
    "claude-brain": {
        "alias": "claude-brain",
        "display_name": "Claude 3.7 Sonnet (@claude-brain)",
        "specialty": "Distributed systems architecture, formal verification, and protocol design",
    },
    "claude-sonnet": {
        "alias": "claude-brain",
        "display_name": "Claude 3.7 Sonnet (@claude-sonnet)",
        "specialty": "Distributed systems architecture, formal verification, and protocol design",
    },
    "grok-brain": {
        "alias": "grok-brain",
        "display_name": "Grok 3 (@grok-brain)",
        "specialty": "Real-time telemetry, adversarial stress-testing, and low-latency mesh routing",
    },
    "openai-brain": {
        "alias": "openai-brain",
        "display_name": "GPT-4o (@openai-brain)",
        "specialty": "Information retrieval, BM25 lexical scoring, and multi-agent orchestration",
    },
    "gpt-4o": {
        "alias": "openai-brain",
        "display_name": "GPT-4o (@gpt-4o)",
        "specialty": "Information retrieval, BM25 lexical scoring, and multi-agent orchestration",
    },
    "deepseek-r1": {
        "alias": "gemini-brain",
        "display_name": "DeepSeek R1 (@deepseek-r1)",
        "specialty": "Mathematical reasoning, cryptographic proofs, and graph algorithms",
    },
    "verifier-agent": {
        "alias": "verifier-agent",
        "display_name": "Identity Verification Agent (@verifier-agent)",
        "specialty": "Mandatory operator identity verification, form dispatch, and cryptographic attestation",
    },
    "tincan-agent": {
        "alias": "gemini-brain",
        "display_name": "TinCan Mesh Agent (@tincan-agent)",
        "specialty": "Zero-knowledge relay operations, TOFU contact pinning, and cyberspace navigation",
    },
}

STOPWORDS: Set[str] = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "from",
    "has", "have", "he", "in", "is", "it", "its", "of", "on", "or", "that",
    "the", "to", "was", "were", "will", "with", "we", "you", "they", "this",
    "can", "how", "what", "when", "where", "who", "why",
}


def parse_cyberspace_tags(text: str) -> Dict[str, List[str]]:
    """
    Extract @username mentions, @agent mentions, and #topic hashtags from text.
    Separates AI agent mentions from human/peer username mentions.
    """
    if not text:
        return {"user_mentions": [], "agent_mentions": [], "hashtags": []}

    raw_mentions = re.findall(r"(?<![\w.])@([a-zA-Z0-9_\-]+)", text)
    raw_hashtags = re.findall(r"(?<![\w.])#([a-zA-Z0-9_\-]+)", text)

    user_mentions: List[str] = []
    agent_mentions: List[str] = []
    seen_users: Set[str] = set()
    seen_agents: Set[str] = set()

    for m in raw_mentions:
        low = m.lower()
        if low in KNOWN_AI_AGENTS or low.endswith("-agent") or low.endswith("-brain"):
            if low not in seen_agents:
                seen_agents.add(low)
                agent_mentions.append(low)
        else:
            if low not in seen_users:
                seen_users.add(low)
                user_mentions.append(low)

    hashtags: List[str] = []
    seen_tags: Set[str] = set()
    for t in raw_hashtags:
        low = t.lower()
        if low not in seen_tags:
            seen_tags.add(low)
            hashtags.append(low)

    return {
        "user_mentions": user_mentions,
        "agent_mentions": agent_mentions,
        "hashtags": hashtags,
    }


def tokenize_for_bm25(text: str) -> List[str]:
    """Tokenize text into normalized terms for BM25 indexing and retrieval."""
    if not text:
        return []
    tokens = re.findall(r"[@#]?[a-zA-Z0-9_\-]+", text.lower())
    result: List[str] = []
    for tok in tokens:
        clean = tok.lstrip("@#")
        if len(clean) >= 2 and clean not in STOPWORDS:
            result.append(clean)
            # Also keep prefixed @user or #tag token for exact entity boost
            if tok.startswith(("@", "#")):
                result.append(tok)
    return result


class BM25Retriever:
    """
    Okapi BM25 Information Retrieval Engine over Cyberspace Topics & Threaded Posts.
    Formula:
      score(D, Q) = sum_{i=1..n} IDF(q_i) * ((f(q_i, D) * (k1 + 1)) / (f(q_i, D) + k1 * (1 - b + b * |D| / avgdl)))
    """

    def __init__(self, k1: float = 1.5, b: float = 0.75) -> None:
        self.k1 = k1
        self.b = b
        self.documents: Dict[str, Dict[str, Any]] = {}
        self.doc_tokens: Dict[str, List[str]] = {}
        self.doc_freqs: Dict[str, Counter] = {}
        self.doc_lengths: Dict[str, int] = {}
        self.df: Dict[str, int] = defaultdict(int)
        self.avgdl: float = 1.0
        self.N: int = 0

    def index_documents(self, docs: List[Dict[str, Any]]) -> None:
        """Build or rebuild the BM25 inverted index from a list of topic/post documents."""
        self.documents.clear()
        self.doc_tokens.clear()
        self.doc_freqs.clear()
        self.doc_lengths.clear()
        self.df.clear()

        total_len = 0
        for doc in docs:
            doc_id = str(doc["topic_id"])
            self.documents[doc_id] = doc
            # Weight title and tags 2x for field-aware BM25 relevance
            title_text = (doc.get("title") or "") + " " + (doc.get("title") or "")
            tags_text = " ".join(f"#{t} {t}" for t in doc.get("tags", []))
            mentions_text = " ".join(
                [f"@{u} {u}" for u in doc.get("user_mentions", [])]
                + [f"@{a} {a}" for a in doc.get("agent_mentions", [])]
                + [f"@{doc.get('author_username', '')}"]
            )
            posts_text = " ".join(
                f"@{p.get('author_username', '')} {p.get('body', '')}"
                for p in doc.get("posts", [])
            )
            full_text = f"{title_text} {tags_text} {mentions_text} {doc.get('body', '')} {posts_text}"
            tokens = tokenize_for_bm25(full_text)
            freq = Counter(tokens)

            self.doc_tokens[doc_id] = tokens
            self.doc_freqs[doc_id] = freq
            self.doc_lengths[doc_id] = len(tokens)
            total_len += len(tokens)

            for term in freq.keys():
                self.df[term] += 1

        self.N = len(docs)
        self.avgdl = (total_len / self.N) if self.N > 0 else 1.0

    def compute_idf(self, term: str) -> float:
        """Compute Okapi BM25 Inverse Document Frequency for a term."""
        n_q = self.df.get(term, 0)
        if n_q == 0 or self.N == 0:
            return 0.0
        return math.log(1.0 + (self.N - n_q + 0.5) / (n_q + 0.5))

    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """Rank indexed topics against query using Okapi BM25."""
        q_tokens = tokenize_for_bm25(query)
        if not q_tokens or self.N == 0:
            return []

        results: List[Dict[str, Any]] = []
        for doc_id, doc in self.documents.items():
            freq = self.doc_freqs[doc_id]
            dl = self.doc_lengths[doc_id]
            score = 0.0
            matched_terms: List[str] = []
            term_scores: Dict[str, float] = {}

            for q in q_tokens:
                tf = freq.get(q, 0)
                if tf <= 0:
                    continue
                idf = self.compute_idf(q)
                denom = tf + self.k1 * (1.0 - self.b + self.b * (dl / max(1.0, self.avgdl)))
                t_score = idf * ((tf * (self.k1 + 1.0)) / denom)
                score += t_score
                if q not in matched_terms:
                    matched_terms.append(q)
                term_scores[q] = round(term_scores.get(q, 0.0) + t_score, 4)

            if score > 0.0:
                results.append(
                    {
                        "topic_id": doc_id,
                        "topic": doc,
                        "bm25_score": round(score, 4),
                        "matched_terms": matched_terms,
                        "term_scores": term_scores,
                    }
                )

        results.sort(key=lambda r: r["bm25_score"], reverse=True)
        return results[:top_k]


class CyberspaceGraphRAG:
    """
    GraphRAG Knowledge Graph & Multi-Hop Retrieval Engine over the Cyberspace Board.
    Connects Topics, Posts, @Users, @Agents, and #Tags into a property graph G = (V, E),
    supporting personalized multi-hop traversal and hybrid BM25 + GraphRAG fusion.
    """

    def __init__(self) -> None:
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.edges: List[Dict[str, Any]] = []
        self.adj: Dict[str, List[Tuple[str, str, float]]] = defaultdict(list)
        self.topic_to_entities: Dict[str, Set[str]] = defaultdict(set)

    def _add_node(self, node_id: str, node_type: str, label: str, **attrs: Any) -> None:
        if node_id not in self.nodes:
            self.nodes[node_id] = {
                "id": node_id,
                "type": node_type,
                "label": label,
                "weight": 1,
                **attrs,
            }
        else:
            self.nodes[node_id]["weight"] = self.nodes[node_id].get("weight", 1) + 1
            for k, v in attrs.items():
                if v is not None:
                    self.nodes[node_id][k] = v

    def _add_edge(self, source: str, target: str, relation: str, weight: float = 1.0) -> None:
        if source == target:
            return
        self.edges.append(
            {
                "source": source,
                "target": target,
                "relation": relation,
                "weight": weight,
            }
        )
        self.adj[source].append((target, relation, weight))
        self.adj[target].append((source, relation, weight))

    def build_graph(self, topics: List[Dict[str, Any]]) -> None:
        """Construct the Cyberspace Knowledge Graph from topics, posts, mentions, and tags."""
        self.nodes.clear()
        self.edges.clear()
        self.adj.clear()
        self.topic_to_entities.clear()

        for topic in topics:
            t_id = str(topic["topic_id"])
            t_node = f"topic:{t_id}"
            author = (topic.get("author_username") or "anonymous").lower().lstrip("@")
            author_node = f"user:@{author}"

            self._add_node(
                t_node,
                "topic",
                topic.get("title", t_id),
                topic_id=t_id,
                category=topic.get("category", "cyberspace"),
                author=f"@{author}",
            )
            self._add_node(author_node, "user", f"@{author}", username=author)
            self._add_edge(author_node, t_node, "AUTHORED_TOPIC", weight=1.5)
            self.topic_to_entities[t_id].add(author_node)

            # Topic-level tags
            tags = [str(x).lower().lstrip("#") for x in topic.get("tags", []) if x]
            for tag in tags:
                tag_node = f"tag:#{tag}"
                self._add_node(tag_node, "tag", f"#{tag}", tag=tag)
                self._add_edge(t_node, tag_node, "TAGGED_WITH", weight=1.2)
                self.topic_to_entities[t_id].add(tag_node)

            # Co-occurrence edges between tags on the same topic
            for i in range(len(tags)):
                for j in range(i + 1, len(tags)):
                    self._add_edge(f"tag:#{tags[i]}", f"tag:#{tags[j]}", "CO_OCCURS", weight=0.6)

            # Topic-level user mentions
            for u in topic.get("user_mentions", []):
                u_clean = u.lower().lstrip("@")
                u_node = f"user:@{u_clean}"
                self._add_node(u_node, "user", f"@{u_clean}", username=u_clean)
                self._add_edge(t_node, u_node, "MENTIONS_USER", weight=1.3)
                self._add_edge(author_node, u_node, "TAGGED_PEER", weight=1.0)
                self.topic_to_entities[t_id].add(u_node)

            # Topic-level AI agent mentions
            for a in topic.get("agent_mentions", []):
                a_clean = a.lower().lstrip("@")
                a_node = f"agent:@{a_clean}"
                self._add_node(a_node, "agent", f"@{a_clean}", agent=a_clean)
                self._add_edge(t_node, a_node, "MENTIONS_AGENT", weight=1.4)
                self._add_edge(author_node, a_node, "INVOKED_AGENT", weight=1.1)
                self.topic_to_entities[t_id].add(a_node)

            # Posts / Replies inside the topic
            for post in topic.get("posts", []):
                p_author = (post.get("author_username") or "anonymous").lower().lstrip("@")
                is_agent = bool(post.get("is_agent"))
                p_actor_node = f"agent:@{p_author}" if is_agent else f"user:@{p_author}"
                self._add_node(
                    p_actor_node,
                    "agent" if is_agent else "user",
                    f"@{p_author}",
                )
                rel = "AGENT_SYNTHESIZED_IN" if is_agent else "REPLIED_IN"
                self._add_edge(p_actor_node, t_node, rel, weight=1.3)
                self.topic_to_entities[t_id].add(p_actor_node)

                for u in post.get("user_mentions", []):
                    u_clean = u.lower().lstrip("@")
                    u_node = f"user:@{u_clean}"
                    self._add_node(u_node, "user", f"@{u_clean}", username=u_clean)
                    self._add_edge(t_node, u_node, "MENTIONS_USER", weight=1.1)
                    self._add_edge(p_actor_node, u_node, "TAGGED_PEER", weight=0.9)
                    self.topic_to_entities[t_id].add(u_node)

                for a in post.get("agent_mentions", []):
                    a_clean = a.lower().lstrip("@")
                    a_node = f"agent:@{a_clean}"
                    self._add_node(a_node, "agent", f"@{a_clean}", agent=a_clean)
                    self._add_edge(t_node, a_node, "MENTIONS_AGENT", weight=1.2)
                    self.topic_to_entities[t_id].add(a_node)

                for h in post.get("hashtags", []):
                    h_clean = h.lower().lstrip("#")
                    h_node = f"tag:#{h_clean}"
                    self._add_node(h_node, "tag", f"#{h_clean}", tag=h_clean)
                    self._add_edge(t_node, h_node, "TAGGED_WITH", weight=1.0)
                    self.topic_to_entities[t_id].add(h_node)

    def retrieve_subgraph_and_scores(
        self,
        query: str,
        bm25_results: List[Dict[str, Any]],
        max_hops: int = 2,
    ) -> Tuple[Dict[str, float], Dict[str, List[str]], Dict[str, Any]]:
        """
        Execute multi-hop GraphRAG activation spreading from query entities and BM25 seed topics.
        Returns:
          - graph_scores: {topic_id: score}
          - topic_paths: {topic_id: [human-readable multi-hop paths]}
          - subgraph: {nodes, edges, seed_entities}
        """
        parsed = parse_cyberspace_tags(query)
        q_tokens = tokenize_for_bm25(query)

        seed_nodes: Dict[str, float] = {}

        # 1. Explicit @user, @agent, #tag mentions in query
        for u in parsed["user_mentions"]:
            nid = f"user:@{u}"
            if nid in self.nodes:
                seed_nodes[nid] = 2.0
        for a in parsed["agent_mentions"]:
            nid = f"agent:@{a}"
            if nid in self.nodes:
                seed_nodes[nid] = 2.2
        for h in parsed["hashtags"]:
            nid = f"tag:#{h}"
            if nid in self.nodes:
                seed_nodes[nid] = 2.0

        # 2. Match query tokens against node labels/IDs (users, agents, tags, topics)
        for nid, ninfo in self.nodes.items():
            lbl_low = ninfo.get("label", "").lower()
            for tok in q_tokens:
                clean_tok = tok.lstrip("@#")
                if len(clean_tok) >= 3 and clean_tok in lbl_low:
                    seed_nodes[nid] = max(seed_nodes.get(nid, 0.0), 1.4)

        # 3. Also seed from top BM25 topics so 2-hop graph expansion discovers related topics
        for idx, r in enumerate(bm25_results[:3]):
            t_nid = f"topic:{r['topic_id']}"
            if t_nid in self.nodes:
                seed_nodes[t_nid] = max(seed_nodes.get(t_nid, 0.0), 1.2 / (idx + 1))

        # Multi-hop Personalized Activation Spreading (BFS up to max_hops)
        activation: Dict[str, float] = defaultdict(float)
        paths_to_node: Dict[str, List[str]] = defaultdict(list)
        visited_Subgraph_nodes: Set[str] = set()

        for s_nid, s_val in seed_nodes.items():
            activation[s_nid] += s_val
            visited_Subgraph_nodes.add(s_nid)
            s_label = self.nodes[s_nid]["label"]
            paths_to_node[s_nid].append(f"Seed({s_label})")

        frontier: Dict[str, float] = dict(seed_nodes)
        decay = 0.55

        for hop in range(1, max_hops + 1):
            next_frontier: Dict[str, float] = defaultdict(float)
            for curr_nid, curr_score in frontier.items():
                curr_label = self.nodes.get(curr_nid, {}).get("label", curr_nid)
                for nbr_nid, rel, edge_weight in self.adj.get(curr_nid, []):
                    spread = curr_score * edge_weight * (decay ** hop)
                    if spread < 0.08:
                        continue
                    activation[nbr_nid] += spread
                    next_frontier[nbr_nid] = max(next_frontier[nbr_nid], spread)
                    visited_Subgraph_nodes.add(nbr_nid)
                    nbr_label = self.nodes.get(nbr_nid, {}).get("label", nbr_nid)
                    path_str = f"{curr_label} --[{rel}]--> {nbr_label}"
                    if len(paths_to_node[nbr_nid]) < 4 and path_str not in paths_to_node[nbr_nid]:
                        paths_to_node[nbr_nid].append(path_str)
            frontier = next_frontier

        # Collect topic graph scores
        topic_graph_scores: Dict[str, float] = {}
        topic_paths: Dict[str, List[str]] = {}
        for nid, score in activation.items():
            if nid.startswith("topic:"):
                t_id = nid.split("topic:", 1)[1]
                # Boost by connected activated entities
                entity_bonus = sum(
                    activation.get(ent, 0.0) * 0.25
                    for ent in self.topic_to_entities.get(t_id, set())
                )
                topic_graph_scores[t_id] = round(score + entity_bonus, 4)
                topic_paths[t_id] = paths_to_node.get(nid, [])

        # Extract induced subgraph for visualization / inspection
        sub_nodes = [
            self.nodes[nid]
            for nid in visited_Subgraph_nodes
            if nid in self.nodes
        ]
        sub_edges = [
            e
            for e in self.edges
            if e["source"] in visited_Subgraph_nodes and e["target"] in visited_Subgraph_nodes
        ]

        subgraph = {
            "seed_entities": [self.nodes[k]["label"] for k in seed_nodes if k in self.nodes],
            "nodes": sub_nodes[:60],
            "edges": sub_edges[:120],
            "total_graph_nodes": len(self.nodes),
            "total_graph_edges": len(self.edges),
        }
        return topic_graph_scores, topic_paths, subgraph

    def get_full_graph_snapshot(self) -> Dict[str, Any]:
        """Return full knowledge graph summary and node/edge lists."""
        counts_by_type: Dict[str, int] = defaultdict(int)
        for n in self.nodes.values():
            counts_by_type[n.get("type", "unknown")] += 1
        return {
            "nodes": list(self.nodes.values()),
            "edges": self.edges,
            "stats": {
                "total_nodes": len(self.nodes),
                "total_edges": len(self.edges),
                "by_type": dict(counts_by_type),
            },
        }


class CyberspaceBoardEngine:
    """
    Main engine for the TinCan Cyberspace Discussion Board,
    BM25 + GraphRAG hybrid search, and the @verifier-agent identity verification workflow.
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        account_registry: Optional[Any] = None,
        ai_router: Optional[Any] = None,
        tincan_relay: Optional[Any] = None,
        webrtc_relay: Optional[Any] = None,
        seed: bool = True,
    ) -> None:
        self._lock = threading.RLock()
        if db_path is None:
            data_dir = (
                os.environ.get("TINCAN_DATA_DIR")
                or os.environ.get("RAILWAY_VOLUME_MOUNT_PATH")
                or os.path.dirname(os.path.abspath(__file__))
            )
            os.makedirs(data_dir, exist_ok=True)
            db_path = os.path.join(data_dir, "cyberspace_board.db")
        self.db_path = db_path
        self.account_registry = account_registry
        self.ai_router = ai_router
        self.tincan_relay = tincan_relay
        self.webrtc_relay = webrtc_relay

        self.bm25 = BM25Retriever(k1=1.5, b=0.75)
        self.graphrag = CyberspaceGraphRAG()

        self._init_db()
        if seed:
            self._seed_initial_knowledge_base()
        self._rebuild_indices()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA synchronous=NORMAL;")

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS cyberspace_topics (
                    topic_id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    body TEXT NOT NULL,
                    category TEXT DEFAULT 'cyberspace',
                    author_peer_id TEXT NOT NULL,
                    author_username TEXT NOT NULL,
                    author_verified INTEGER DEFAULT 1,
                    tags_json TEXT DEFAULT '[]',
                    user_mentions_json TEXT DEFAULT '[]',
                    agent_mentions_json TEXT DEFAULT '[]',
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS cyberspace_posts (
                    post_id TEXT PRIMARY KEY,
                    topic_id TEXT NOT NULL,
                    parent_post_id TEXT DEFAULT '',
                    author_peer_id TEXT NOT NULL,
                    author_username TEXT NOT NULL,
                    is_agent INTEGER DEFAULT 0,
                    author_verified INTEGER DEFAULT 1,
                    body TEXT NOT NULL,
                    user_mentions_json TEXT DEFAULT '[]',
                    agent_mentions_json TEXT DEFAULT '[]',
                    hashtags_json TEXT DEFAULT '[]',
                    created_at REAL NOT NULL,
                    FOREIGN KEY(topic_id) REFERENCES cyberspace_topics(topic_id)
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS verification_forms (
                    request_id TEXT PRIMARY KEY,
                    peer_id TEXT NOT NULL,
                    target_username TEXT DEFAULT '',
                    status TEXT DEFAULT 'pending',
                    sent_by TEXT DEFAULT '@verifier-agent',
                    reason TEXT DEFAULT '',
                    form_schema_json TEXT NOT NULL,
                    submitted_data_json TEXT DEFAULT '{}',
                    attestation_hash TEXT DEFAULT '',
                    sent_at REAL NOT NULL,
                    completed_at REAL DEFAULT 0.0
                )
                """
            )
            conn.commit()

    def _seed_initial_knowledge_base(self) -> None:
        """Seed rich initial Cyberspace Knowledge Base topics if database is empty."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM cyberspace_topics")
            count = cursor.fetchone()[0]
            if count > 0:
                return

        now = time.time()
        seed_topics = [
            {
                "topic_id": "topic-cyberspace-graphrag",
                "title": "Welcome to TinCan Cyberspace Knowledge Base: GraphRAG & BM25 Architecture",
                "body": (
                    "Welcome to the TinCan Cyberspace Discussion Board! Builders can tag themselves (@alejandro), "
                    "tag collaborators (@harper @collaborator), and tag AI agents (@gemini-brain @claude-brain) "
                    "to co-build a living knowledge graph in #cyberspace using #graphrag and #bm25 retrieval."
                ),
                "category": "architecture",
                "author_peer_id": "peer-primary-mac",
                "author_username": "alejandro",
                "tags": ["cyberspace", "graphrag", "bm25", "knowledge-base", "mesh-os"],
                "created_at": now - 3600,
                "replies": [
                    {
                        "post_id": "post-seed-01",
                        "author_peer_id": "agent:gemini-brain",
                        "author_username": "gemini-brain",
                        "is_agent": 1,
                        "body": (
                            "🤖 [@gemini-brain Synthesis]: Indexed #cyberspace topic by @alejandro. "
                            "Our hybrid #graphrag + #bm25 pipeline links every @username mention, AI agent invocation, "
                            "and concept tag into a 2-hop property graph alongside Okapi BM25 lexical scoring."
                        ),
                        "created_at": now - 3500,
                    },
                    {
                        "post_id": "post-seed-02",
                        "author_peer_id": "peer-secondary-node",
                        "author_username": "harper",
                        "is_agent": 0,
                        "body": (
                            "Tagging myself (@harper) and @alejandro! Can @openai-brain explain how BM25 term saturation "
                            "complements multi-hop #graphrag traversal when searching #webrtc and #ed25519 topics?"
                        ),
                        "created_at": now - 3400,
                    },
                    {
                        "post_id": "post-seed-03",
                        "author_peer_id": "agent:openai-brain",
                        "author_username": "openai-brain",
                        "is_agent": 1,
                        "body": (
                            "🤖 [@openai-brain Synthesis]: Great question @harper and @alejandro! Okapi #bm25 captures exact "
                            "high-IDF technical tokens like #ed25519 and #webrtc (k1=1.5, b=0.75), while #graphrag traverses "
                            "shared @username and @agent edges to surface semantically linked threads."
                        ),
                        "created_at": now - 3350,
                    },
                ],
            },
            {
                "topic_id": "topic-identity-verification",
                "title": "Cyberspace Identity Verification Protocol & @verifier-agent Onboarding",
                "body": (
                    "Every participant in the TinCan Cyberspace Knowledge Base is verified by @verifier-agent. "
                    "When a new peer joins or tags @verifier-agent, the agent dispatches the #verification form "
                    "(Full Name, @username, Email, Phone, and PII attestation) to establish #zero-knowledge trust with @alejandro."
                ),
                "category": "security",
                "author_peer_id": "agent:verifier-agent",
                "author_username": "verifier-agent",
                "tags": ["verification", "security", "zero-knowledge", "identity", "cyberspace"],
                "created_at": now - 2400,
                "replies": [
                    {
                        "post_id": "post-seed-04",
                        "author_peer_id": "agent:claude-brain",
                        "author_username": "claude-brain",
                        "is_agent": 1,
                        "body": (
                            "🤖 [@claude-brain Synthesis]: Attesting @verifier-agent protocol. Combining #ed25519 node keys "
                            "with verified operator forms ensures sybil-resistant #cyberspace discussions."
                        ),
                        "created_at": now - 2300,
                    }
                ],
            },
            {
                "topic_id": "topic-federated-mesh-webrtc",
                "title": "Sub-80ms WebRTC Media & CRDT Gossip Synchronization Across Nodes",
                "body": (
                    "Testing low-latency #webrtc screensharing and #crdt state sync between @alejandro on Mac Studio "
                    "and @harper on Collaborator Node with @grok-brain monitoring UDP telemetry in #mesh-os."
                ),
                "category": "networking",
                "author_peer_id": "peer-primary-mac",
                "author_username": "alejandro",
                "tags": ["webrtc", "crdt", "mesh-os", "telemetry"],
                "created_at": now - 1800,
                "replies": [
                    {
                        "post_id": "post-seed-05",
                        "author_peer_id": "agent:grok-brain",
                        "author_username": "grok-brain",
                        "is_agent": 1,
                        "body": (
                            "🤖 [@grok-brain Synthesis]: Telemetry locked for @alejandro and @harper! #webrtc signaling "
                            "and #crdt gossip vectors are nominal across the #mesh-os relay."
                        ),
                        "created_at": now - 1750,
                    }
                ],
            },
        ]

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for st in seed_topics:
                parsed = parse_cyberspace_tags(st["body"])
                merged_tags = list(dict.fromkeys(st["tags"] + parsed["hashtags"]))
                cursor.execute(
                    """
                    INSERT OR IGNORE INTO cyberspace_topics (
                        topic_id, title, body, category, author_peer_id, author_username,
                        author_verified, tags_json, user_mentions_json, agent_mentions_json,
                        created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?, ?)
                    """,
                    (
                        st["topic_id"],
                        st["title"],
                        st["body"],
                        st["category"],
                        st["author_peer_id"],
                        st["author_username"],
                        json.dumps(merged_tags),
                        json.dumps(parsed["user_mentions"]),
                        json.dumps(parsed["agent_mentions"]),
                        st["created_at"],
                        st["created_at"],
                    ),
                )
                for rep in st.get("replies", []):
                    r_parsed = parse_cyberspace_tags(rep["body"])
                    cursor.execute(
                        """
                        INSERT OR IGNORE INTO cyberspace_posts (
                            post_id, topic_id, parent_post_id, author_peer_id, author_username,
                            is_agent, author_verified, body, user_mentions_json, agent_mentions_json,
                            hashtags_json, created_at
                        )
                        VALUES (?, ?, '', ?, ?, ?, 1, ?, ?, ?, ?, ?)
                        """,
                        (
                            rep["post_id"],
                            st["topic_id"],
                            rep["author_peer_id"],
                            rep["author_username"],
                            rep["is_agent"],
                            rep["body"],
                            json.dumps(r_parsed["user_mentions"]),
                            json.dumps(r_parsed["agent_mentions"]),
                            json.dumps(r_parsed["hashtags"]),
                            rep["created_at"],
                        ),
                    )
            conn.commit()

    def _load_all_topics_from_db(self) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM cyberspace_topics ORDER BY updated_at DESC")
            topic_rows = [dict(r) for r in cursor.fetchall()]

            cursor.execute("SELECT * FROM cyberspace_posts ORDER BY created_at ASC")
            post_rows = [dict(r) for r in cursor.fetchall()]

        posts_by_topic: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        for p in post_rows:
            posts_by_topic[p["topic_id"]].append(
                {
                    "post_id": p["post_id"],
                    "topic_id": p["topic_id"],
                    "parent_post_id": p.get("parent_post_id") or "",
                    "author_peer_id": p["author_peer_id"],
                    "author_username": p["author_username"],
                    "is_agent": bool(p["is_agent"]),
                    "author_verified": bool(p["author_verified"]),
                    "body": p["body"],
                    "user_mentions": json.loads(p.get("user_mentions_json") or "[]"),
                    "agent_mentions": json.loads(p.get("agent_mentions_json") or "[]"),
                    "hashtags": json.loads(p.get("hashtags_json") or "[]"),
                    "created_at": p["created_at"],
                }
            )

        topics: List[Dict[str, Any]] = []
        for t in topic_rows:
            t_id = t["topic_id"]
            t_posts = posts_by_topic.get(t_id, [])
            tags = json.loads(t.get("tags_json") or "[]")
            user_mentions = json.loads(t.get("user_mentions_json") or "[]")
            agent_mentions = json.loads(t.get("agent_mentions_json") or "[]")

            # Aggregate all unique mentions across topic + replies
            all_users = list(dict.fromkeys(user_mentions + [u for p in t_posts for u in p["user_mentions"]]))
            all_agents = list(dict.fromkeys(agent_mentions + [a for p in t_posts for a in p["agent_mentions"]]))
            all_tags = list(dict.fromkeys(tags + [h for p in t_posts for h in p["hashtags"]]))

            topics.append(
                {
                    "topic_id": t_id,
                    "title": t["title"],
                    "body": t["body"],
                    "category": t["category"],
                    "author_peer_id": t["author_peer_id"],
                    "author_username": t["author_username"],
                    "author_verified": bool(t["author_verified"]),
                    "tags": all_tags,
                    "user_mentions": all_users,
                    "agent_mentions": all_agents,
                    "posts": t_posts,
                    "reply_count": len(t_posts),
                    "created_at": t["created_at"],
                    "updated_at": t["updated_at"],
                }
            )
        return topics

    def _rebuild_indices(self) -> None:
        """Synchronize in-memory BM25 inverted index and GraphRAG property graph."""
        with self._lock:
            topics = self._load_all_topics_from_db()
            self.bm25.index_documents(topics)
            self.graphrag.build_graph(topics)

    # =========================================================================
    # Identity Verification Agent (@verifier-agent)
    # =========================================================================

    def is_peer_verified(self, peer_id: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Check if a peer has a verified identity in PeerAccountRegistry or completed verification form."""
        peer_id = (peer_id or "").strip()
        if not peer_id:
            return False, None
        if peer_id.startswith("agent:"):
            return True, {"peer_id": peer_id, "username": peer_id.split(":", 1)[1], "verified": True}

        if self.account_registry is not None:
            acc = self.account_registry.get_account_by_peer(peer_id)
            if acc and acc.get("username") and acc.get("email") and acc.get("consent_pii"):
                # Exclude auto-provisioned temporary guest accounts from counting as verified humans
                if not str(acc.get("email", "")).endswith("@mesh.local"):
                    return True, acc

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM verification_forms WHERE peer_id = ? AND status = 'completed' ORDER BY completed_at DESC LIMIT 1",
                (peer_id,),
            )
            row = cursor.fetchone()
            if row:
                data = json.loads(row["submitted_data_json"] or "{}")
                data["attestation_hash"] = row["attestation_hash"]
                data["verified"] = True
                return True, data

        return False, None

    def dispatch_verification_form(
        self,
        peer_id: str,
        target_username: str = "",
        reason: str = "Mandatory Cyberspace Identity Verification",
    ) -> Dict[str, Any]:
        """
        Have @verifier-agent send a structured identity verification form to a peer/user.
        Delivers via database queue, WebRTC signaling bus, and TinCan Relay inbox if applicable.
        """
        peer_id = (peer_id or "anonymous-peer").strip()
        target_username = (target_username or "").strip().lstrip("@")
        req_id = f"vrf-{uuid.uuid4().hex[:10]}"
        now = time.time()

        form_schema = {
            "form_id": req_id,
            "title": "TinCan Cyberspace Identity Verification Form",
            "dispatched_by": "@verifier-agent",
            "peer_id": peer_id,
            "target_username": target_username,
            "reason": reason,
            "instructions": (
                "Hello from @verifier-agent! Before posting or tagging peers in the Cyberspace Knowledge Base, "
                "please complete and sign this identity verification form so we can verify who you are."
            ),
            "fields": [
                {"name": "full_name", "label": "Full Legal / Real Name", "type": "text", "required": True},
                {"name": "username", "label": "Cyberspace Username (@handle)", "type": "text", "required": True, "default": target_username},
                {"name": "email", "label": "Verified Contact Email", "type": "email", "required": True},
                {"name": "phone_number", "label": "Phone Number (SMS/2FA)", "type": "tel", "required": True},
                {"name": "role", "label": "Role / Affiliation", "type": "select", "required": True, "default": "FAU Graduate School / Academic"},
                {"name": "bio", "label": "Cyberspace Knowledge Domain / Bio", "type": "text", "required": False},
                {"name": "consent_pii", "label": "I attest my identity and consent to operator verification", "type": "checkbox", "required": True},
            ],
        }

        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO verification_forms (
                        request_id, peer_id, target_username, status, sent_by,
                        reason, form_schema_json, submitted_data_json, attestation_hash, sent_at
                    )
                    VALUES (?, ?, ?, 'pending', '@verifier-agent', ?, ?, '{}', '', ?)
                    """,
                    (req_id, peer_id, target_username, reason, json.dumps(form_schema), now),
                )
                conn.commit()

        # Emit real-time signal over WebRTC bus so browser UI pops up the agent verification form
        if self.webrtc_relay is not None:
            try:
                self.webrtc_relay.exchange_signal(
                    sender_id="@verifier-agent",
                    receiver_id=peer_id,
                    signal_type="verification_form",
                    sdp_or_candidate=form_schema,
                    room="main",
                )
            except Exception:
                pass

        # Also deliver to TinCan Blind Relay inbox if peer_id is a tc: address or alias
        if self.tincan_relay is not None:
            try:
                self.tincan_relay.send(
                    {
                        "from": "@verifier-agent",
                        "to": peer_id,
                        "ciphertext": json.dumps(
                            {
                                "type": "VERIFICATION_FORM_DISPATCH",
                                "agent": "@verifier-agent",
                                "form": form_schema,
                            }
                        ),
                    }
                )
            except Exception:
                pass

        return {
            "status": "dispatched",
            "agent": "@verifier-agent",
            "request_id": req_id,
            "peer_id": peer_id,
            "target_username": target_username,
            "reason": reason,
            "form": form_schema,
            "sent_at": now,
        }

    def submit_verification_form(
        self,
        peer_id: str,
        full_name: str,
        username: str,
        email: str,
        phone_number: str,
        role: str = "Researcher / Student",
        bio: str = "",
        consent_pii: bool = True,
        request_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process and verify a user's submitted identity form via @verifier-agent.
        Registers the user in PeerAccountRegistry and issues a cryptographic attestation hash.
        """
        peer_id = (peer_id or "").strip()
        full_name = (full_name or "").strip()
        username = (username or "").strip().lstrip("@").lower()
        email = (email or "").strip().lower()
        phone_number = (phone_number or "").strip()
        role = (role or "Researcher / Student").strip()
        bio = (bio or "").strip()

        if not peer_id:
            raise ValueError("peer_id is required for identity verification")
        if len(full_name) < 2:
            raise ValueError("Full Name is required (minimum 2 characters)")
        if len(username) < 2:
            raise ValueError("Username (@handle) is required (minimum 2 characters)")
        if not re.match(r"^[\w\.-]+@[\w\.-]+\.\w+$", email):
            raise ValueError(f"Invalid email address: {email}")
        cleaned_phone = re.sub(r"[^\d+]", "", phone_number)
        if len(re.sub(r"\D", "", cleaned_phone)) < 10:
            raise ValueError("Valid phone number (minimum 10 digits) is required")
        if not consent_pii:
            raise ValueError("Identity attestation & PII consent is required by @verifier-agent")

        now = time.time()
        attestation_payload = f"{peer_id}:{username}:{full_name}:{email}:{cleaned_phone}:{int(now)}"
        attestation_hash = hashlib.sha256(attestation_payload.encode("utf-8")).hexdigest()[:24]

        account_record = None
        if self.account_registry is not None:
            account_record = self.account_registry.register_account(
                peer_id=peer_id,
                full_name=full_name,
                phone_number=phone_number,
                email=email,
                username=username,
                role=role,
                consent_pii=True,
            )

        submitted_data = {
            "peer_id": peer_id,
            "full_name": full_name,
            "username": username,
            "email": email,
            "phone_number": phone_number,
            "role": role,
            "bio": bio,
            "consent_pii": True,
            "verified_by": "@verifier-agent",
            "attestation_hash": attestation_hash,
            "verified_at": now,
            "badge": "✅ Verified Cyberspace Citizen",
        }

        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                if request_id:
                    cursor.execute(
                        """
                        UPDATE verification_forms
                        SET status = 'completed',
                            target_username = ?,
                            submitted_data_json = ?,
                            attestation_hash = ?,
                            completed_at = ?
                        WHERE request_id = ?
                        """,
                        (username, json.dumps(submitted_data), attestation_hash, now, request_id),
                    )
                else:
                    req_id = f"vrf-{uuid.uuid4().hex[:10]}"
                    cursor.execute(
                        """
                        INSERT INTO verification_forms (
                            request_id, peer_id, target_username, status, sent_by,
                            reason, form_schema_json, submitted_data_json, attestation_hash, sent_at, completed_at
                        )
                        VALUES (?, ?, ?, 'completed', '@verifier-agent', 'Direct Form Submission', '{}', ?, ?, ?, ?)
                        """,
                        (req_id, peer_id, username, json.dumps(submitted_data), attestation_hash, now, now),
                    )
                # Also mark any other pending forms for this peer_id as completed
                cursor.execute(
                    """
                    UPDATE verification_forms
                    SET status = 'completed',
                        submitted_data_json = ?,
                        attestation_hash = ?,
                        completed_at = ?
                    WHERE peer_id = ? AND status = 'pending'
                    """,
                    (json.dumps(submitted_data), attestation_hash, now, peer_id),
                )
                conn.commit()

        return {
            "status": "verified",
            "verified": True,
            "agent": "@verifier-agent",
            "peer_id": peer_id,
            "username": f"@{username}",
            "full_name": full_name,
            "attestation_hash": attestation_hash,
            "badge": "✅ Verified Cyberspace Citizen",
            "account": account_record or submitted_data,
        }

    def get_verification_status(self, peer_id: str) -> Dict[str, Any]:
        """Inspect a peer's verification status and any pending form sent by @verifier-agent."""
        verified, profile = self.is_peer_verified(peer_id)
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM verification_forms WHERE peer_id = ? ORDER BY sent_at DESC LIMIT 5",
                ((peer_id or "").strip(),),
            )
            forms = []
            for r in cursor.fetchall():
                forms.append(
                    {
                        "request_id": r["request_id"],
                        "peer_id": r["peer_id"],
                        "target_username": r["target_username"],
                        "status": r["status"],
                        "sent_by": r["sent_by"],
                        "reason": r["reason"],
                        "form": json.loads(r["form_schema_json"] or "{}"),
                        "attestation_hash": r["attestation_hash"],
                        "sent_at": r["sent_at"],
                        "completed_at": r["completed_at"],
                    }
                )

        return {
            "peer_id": peer_id,
            "verified": verified,
            "verified_by": "@verifier-agent" if verified else None,
            "profile": profile,
            "pending_forms": [f for f in forms if f["status"] == "pending"],
            "history": forms,
        }

    # =========================================================================
    # Discussion Board: Topics, Replies & Automatic @Agent Participation
    # =========================================================================

    def _resolve_username(self, peer_id: str, provided_username: Optional[str] = None) -> Tuple[str, bool]:
        """Resolve a peer's @username and verification status."""
        verified, profile = self.is_peer_verified(peer_id)
        if provided_username and provided_username.strip():
            clean = provided_username.strip().lstrip("@").lower()
            return clean, verified
        if profile and profile.get("username"):
            return str(profile["username"]).strip().lstrip("@").lower(), verified
        clean_peer = re.sub(r"[^a-zA-Z0-9_\-]", "", peer_id)[:16].lower() or "anonymous"
        return clean_peer, verified

    def _generate_agent_reply(
        self,
        agent_handle: str,
        topic_title: str,
        trigger_body: str,
        author_username: str,
        tags: List[str],
        user_mentions: List[str],
    ) -> str:
        """Synthesize an intelligent response when an AI agent (@gemini-brain, @verifier-agent, etc.) is tagged."""
        agent_key = agent_handle.lower().lstrip("@")
        agent_meta = KNOWN_AI_AGENTS.get(
            agent_key,
            {
                "alias": "gemini-brain",
                "display_name": f"AI Agent (@{agent_key})",
                "specialty": "Cyberspace knowledge synthesis",
            },
        )

        # Special handling if @verifier-agent is tagged in a thread!
        if agent_key == "verifier-agent":
            mentioned_Targets = [u for u in user_mentions if u != author_username]
            if mentioned_Targets:
                for target_u in mentioned_Targets:
                    self.dispatch_verification_form(
                        peer_id=f"user:{target_u}",
                        target_username=target_u,
                        reason=f"Tagged by @{author_username} in topic '{topic_title}' for identity verification",
                    )
                targets_str = ", ".join(f"@{u}" for u in mentioned_Targets)
                return (
                    f"🛡️ [@verifier-agent Dispatch]: Identity verification form has been sent to {targets_str} "
                    f"(requested by @{author_username}). Once they fill out Full Name, @username, Email, Phone, "
                    f"and sign the PII attestation, their #cyberspace citizen badge will activate."
                )
            return (
                f"🛡️ [@verifier-agent Status]: Verified request from @{author_username}. "
                f"Any unverified participant can complete the mandatory identity form via `/api/verify/submit` "
                f"or `tincan verify submit` to receive cryptographic attestation in #cyberspace."
            )

        # Retrieve relevant GraphRAG context to ground the agent's reply
        search_res = self.search(f"{topic_title} {trigger_body}", mode="hybrid", top_k=2)
        related_titles = [
            r["title"] for r in search_res.get("results", []) if r.get("title") != topic_title
        ][:2]
        context_note = (
            f" Cross-linked in Knowledge Graph with: {', '.join(repr(t) for t in related_titles)}."
            if related_titles
            else ""
        )
        tags_str = " ".join(f"#{t}" for t in tags[:4]) if tags else "#cyberspace #graphrag"
        users_str = " ".join(f"@{u}" for u in ([author_username] + [u for u in user_mentions if u != author_username])[:3])

        # If live ai_router is provided and configured with an API key, attempt completion
        if self.ai_router is not None and os.environ.get("OPENROUTER_API_KEY"):
            try:
                resp = self.ai_router.dispatch_completion(
                    alias=agent_meta["alias"],
                    messages=[
                        {
                            "role": "system",
                            "content": (
                                f"You are @{agent_key} ({agent_meta['display_name']}), an AI agent in the TinCan Cyberspace "
                                f"Knowledge Base. Keep your response concise (2-3 sentences), mention {users_str}, "
                                f"and reference relevant tags ({tags_str})."
                            ),
                        },
                        {
                            "role": "user",
                            "content": f"Topic: {topic_title}\nPost by @{author_username}: {trigger_body}",
                        },
                    ],
                    max_tokens=180,
                )
                content = resp.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                if content:
                    return f"🤖 [@{agent_key}]: {content}"
            except Exception:
                pass

        return (
            f"🤖 [@{agent_key} Synthesis]: Acknowledged {users_str} on \"{topic_title}\". "
            f"Indexed key concepts ({tags_str}) into the TinCan Cyberspace Knowledge Graph "
            f"(specialty: {agent_meta['specialty']}).{context_note}"
        )

    def create_topic(
        self,
        peer_id: str,
        title: str,
        body: str,
        category: str = "cyberspace",
        tags: Optional[List[str]] = None,
        author_username: Optional[str] = None,
        require_verification: bool = False,
        auto_agent_reply: bool = True,
    ) -> Dict[str, Any]:
        """
        Create a new discussion topic in the Cyberspace Knowledge Base.
        Automatically extracts @username tags, @agent tags, and #hashtags,
        and invokes tagged AI agents to post replies.
        """
        peer_id = (peer_id or "anonymous-peer").strip()
        title = (title or "").strip()
        body = (body or "").strip()
        category = (category or "cyberspace").strip().lower()

        if not title:
            raise ValueError("Topic title is required")
        if not body:
            raise ValueError("Topic body is required")

        username, is_verified = self._resolve_username(peer_id, author_username)

        if require_verification and not is_verified:
            dispatch = self.dispatch_verification_form(
                peer_id=peer_id,
                target_username=username,
                reason=f"Attempted to create topic '{title}' without completed identity verification",
            )
            return {
                "status": "verification_required",
                "require_verification": True,
                "agent": "@verifier-agent",
                "message": (
                    "🛡️ @verifier-agent has sent you the Identity Verification Form. "
                    "Please fill out the form to verify who you are before posting."
                ),
                "verification_dispatch": dispatch,
            }

        parsed = parse_cyberspace_tags(f"{title} {body}")
        explicit_tags = [str(t).strip().lstrip("#").lower() for t in (tags or []) if str(t).strip()]
        merged_tags = list(dict.fromkeys(explicit_tags + parsed["hashtags"] + [category]))

        # Ensure self-tag is recorded if user tagged themselves or authored the topic
        user_mentions = parsed["user_mentions"]
        agent_mentions = parsed["agent_mentions"]

        topic_id = f"topic-{uuid.uuid4().hex[:10]}"
        now = time.time()

        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO cyberspace_topics (
                        topic_id, title, body, category, author_peer_id, author_username,
                        author_verified, tags_json, user_mentions_json, agent_mentions_json,
                        created_at, updated_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        topic_id,
                        title,
                        body,
                        category,
                        peer_id,
                        username,
                        1 if is_verified else 0,
                        json.dumps(merged_tags),
                        json.dumps(user_mentions),
                        json.dumps(agent_mentions),
                        now,
                        now,
                    ),
                )
                conn.commit()

            self._rebuild_indices()

            # If any AI agents were tagged (@gemini-brain, @verifier-agent, etc.), auto-reply!
            if auto_agent_reply and agent_mentions:
                for agent_handle in agent_mentions[:3]:
                    reply_text = self._generate_agent_reply(
                        agent_handle=agent_handle,
                        topic_title=title,
                        trigger_body=body,
                        author_username=username,
                        tags=merged_tags,
                        user_mentions=user_mentions,
                    )
                    self.create_post(
                        topic_id=topic_id,
                        peer_id=f"agent:{agent_handle}",
                        body=reply_text,
                        author_username=agent_handle,
                        is_agent=True,
                        auto_agent_reply=False,
                    )

            return self.get_topic(topic_id)

    def create_post(
        self,
        topic_id: str,
        peer_id: str,
        body: str,
        author_username: Optional[str] = None,
        parent_post_id: str = "",
        is_agent: bool = False,
        require_verification: bool = False,
        auto_agent_reply: bool = True,
    ) -> Dict[str, Any]:
        """Add a reply/post to an existing topic, parsing @username, @agent, and #tag mentions."""
        topic_id = (topic_id or "").strip()
        peer_id = (peer_id or "anonymous-peer").strip()
        body = (body or "").strip()
        if not topic_id:
            raise ValueError("topic_id is required")
        if not body:
            raise ValueError("Post body is required")

        existing_topic = self.get_topic(topic_id)
        if not existing_topic:
            raise ValueError(f"Topic '{topic_id}' not found")

        username, is_verified = self._resolve_username(peer_id, author_username)
        if is_agent:
            is_verified = True

        if require_verification and not is_verified:
            dispatch = self.dispatch_verification_form(
                peer_id=peer_id,
                target_username=username,
                reason=f"Attempted to reply in topic '{existing_topic['title']}' without verification",
            )
            return {
                "status": "verification_required",
                "require_verification": True,
                "agent": "@verifier-agent",
                "message": (
                    "🛡️ @verifier-agent has sent you the Identity Verification Form. "
                    "Please complete verification to post in this thread."
                ),
                "verification_dispatch": dispatch,
            }

        parsed = parse_cyberspace_tags(body)
        post_id = f"post-{uuid.uuid4().hex[:10]}"
        now = time.time()

        with self._lock:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO cyberspace_posts (
                        post_id, topic_id, parent_post_id, author_peer_id, author_username,
                        is_agent, author_verified, body, user_mentions_json, agent_mentions_json,
                        hashtags_json, created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        post_id,
                        topic_id,
                        parent_post_id or "",
                        peer_id,
                        username,
                        1 if is_agent else 0,
                        1 if is_verified else 0,
                        body,
                        json.dumps(parsed["user_mentions"]),
                        json.dumps(parsed["agent_mentions"]),
                        json.dumps(parsed["hashtags"]),
                        now,
                    ),
                )
                cursor.execute(
                    "UPDATE cyberspace_topics SET updated_at = ? WHERE topic_id = ?",
                    (now, topic_id),
                )
                conn.commit()

            self._rebuild_indices()

            # Trigger AI agent responses if a human tagged an AI agent in their reply
            agent_replies: List[Dict[str, Any]] = []
            if auto_agent_reply and not is_agent and parsed["agent_mentions"]:
                for agent_handle in parsed["agent_mentions"][:2]:
                    reply_text = self._generate_agent_reply(
                        agent_handle=agent_handle,
                        topic_title=existing_topic["title"],
                        trigger_body=body,
                        author_username=username,
                        tags=existing_topic.get("tags", []) + parsed["hashtags"],
                        user_mentions=parsed["user_mentions"],
                    )
                    ag_post = self.create_post(
                        topic_id=topic_id,
                        peer_id=f"agent:{agent_handle}",
                        body=reply_text,
                        author_username=agent_handle,
                        parent_post_id=post_id,
                        is_agent=True,
                        auto_agent_reply=False,
                    )
                    agent_replies.append(ag_post)

            updated_topic = self.get_topic(topic_id)
            return {
                "status": "posted",
                "post_id": post_id,
                "topic_id": topic_id,
                "author_username": f"@{username}",
                "author_verified": is_verified,
                "user_mentions": parsed["user_mentions"],
                "agent_mentions": parsed["agent_mentions"],
                "hashtags": parsed["hashtags"],
                "agent_replies": agent_replies,
                "topic": updated_topic,
            }

    def get_topic(self, topic_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single topic with all posts and connected GraphRAG entities."""
        with self._lock:
            topics = self._load_all_topics_from_db()
            for t in topics:
                if t["topic_id"] == topic_id:
                    t_node = f"topic:{topic_id}"
                    neighbors = [
                        {
                            "node": nbr,
                            "label": self.graphrag.nodes.get(nbr, {}).get("label", nbr),
                            "type": self.graphrag.nodes.get(nbr, {}).get("type", "entity"),
                            "relation": rel,
                        }
                        for nbr, rel, _ in self.graphrag.adj.get(t_node, [])
                    ]
                    t["graph_connections"] = neighbors
                    return t
        return None

    def list_topics(
        self,
        category: Optional[str] = None,
        tag: Optional[str] = None,
        mentioned_user: Optional[str] = None,
        mentioned_agent: Optional[str] = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """List discussion topics with optional filtering by category, #tag, @username, or @agent."""
        with self._lock:
            topics = self._load_all_topics_from_db()

        if category:
            cat_low = category.strip().lower()
            topics = [t for t in topics if t.get("category", "").lower() == cat_low]
        if tag:
            tag_low = tag.strip().lstrip("#").lower()
            topics = [t for t in topics if tag_low in [x.lower() for x in t.get("tags", [])]]
        if mentioned_user:
            u_low = mentioned_user.strip().lstrip("@").lower()
            topics = [
                t
                for t in topics
                if u_low == t.get("author_username", "").lower()
                or u_low in [x.lower() for x in t.get("user_mentions", [])]
                or any(p.get("author_username", "").lower() == u_low for p in t.get("posts", []))
            ]
        if mentioned_agent:
            a_low = mentioned_agent.strip().lstrip("@").lower()
            topics = [
                t
                for t in topics
                if a_low in [x.lower() for x in t.get("agent_mentions", [])]
                or any(p.get("author_username", "").lower() == a_low for p in t.get("posts", []))
            ]

        graph_snap = self.graphrag.get_full_graph_snapshot()
        return {
            "count": len(topics[:limit]),
            "total_topics": len(topics),
            "topics": topics[:limit],
            "available_agents": list(KNOWN_AI_AGENTS.values()),
            "graph_stats": graph_snap["stats"],
        }

    # =========================================================================
    # Hybrid Search: BM25 Information Retrieval + GraphRAG Knowledge Traversal
    # =========================================================================

    def search(
        self,
        query: str,
        mode: str = "hybrid",
        top_k: int = 10,
        max_hops: int = 2,
    ) -> Dict[str, Any]:
        """
        Search Cyberspace topics and posts using:
          - 'bm25': Okapi BM25 lexical information retrieval
          - 'graphrag': Multi-hop Knowledge Graph activation spreading
          - 'hybrid' (default): Weighted fusion (0.55 BM25 + 0.45 GraphRAG) with subgraph & synthesis
        """
        query = (query or "").strip()
        mode = (mode or "hybrid").strip().lower()
        if not query:
            listed = self.list_topics(limit=top_k)
            return {
                "query": "",
                "mode": mode,
                "results": listed["topics"],
                "subgraph": self.graphrag.get_full_graph_snapshot(),
                "synthesis": "Showing recent Cyberspace Knowledge Base topics.",
            }

        with self._lock:
            bm25_raw = self.bm25.search(query, top_k=max(top_k * 2, 20))
            bm25_map: Dict[str, Dict[str, Any]] = {r["topic_id"]: r for r in bm25_raw}
            graph_scores, topic_paths, subgraph = self.graphrag.retrieve_subgraph_and_scores(
                query=query,
                bm25_results=bm25_raw,
                max_hops=max_hops,
            )

            all_topics_map = {t["topic_id"]: t for t in self._load_all_topics_from_db()}

        candidate_ids = set(bm25_map.keys()) | set(graph_scores.keys())
        max_bm25 = max((r["bm25_score"] for r in bm25_raw), default=1.0) or 1.0
        max_graph = max(graph_scores.values(), default=1.0) or 1.0

        combined_results: List[Dict[str, Any]] = []
        for t_id in candidate_ids:
            topic = all_topics_map.get(t_id)
            if not topic:
                continue
            b_entry = bm25_map.get(t_id, {})
            raw_bm25 = float(b_entry.get("bm25_score", 0.0))
            raw_graph = float(graph_scores.get(t_id, 0.0))

            norm_bm25 = raw_bm25 / max_bm25 if max_bm25 > 0 else 0.0
            norm_graph = raw_graph / max_graph if max_graph > 0 else 0.0

            if mode == "bm25":
                if raw_bm25 <= 0:
                    continue
                final_score = raw_bm25
            elif mode == "graphrag":
                if raw_graph <= 0:
                    continue
                final_score = raw_graph
            else:
                final_score = round(0.55 * norm_bm25 + 0.45 * norm_graph, 4)

            combined_results.append(
                {
                    "topic_id": t_id,
                    "title": topic["title"],
                    "body": topic["body"],
                    "category": topic["category"],
                    "author_username": f"@{topic['author_username']}",
                    "author_verified": topic["author_verified"],
                    "tags": topic["tags"],
                    "user_mentions": [f"@{u}" for u in topic["user_mentions"]],
                    "agent_mentions": [f"@{a}" for a in topic["agent_mentions"]],
                    "reply_count": topic["reply_count"],
                    "posts": topic["posts"],
                    "score": round(final_score, 4),
                    "bm25_score": round(raw_bm25, 4),
                    "graphrag_score": round(raw_graph, 4),
                    "matched_terms": b_entry.get("matched_terms", []),
                    "term_scores": b_entry.get("term_scores", {}),
                    "graph_paths": topic_paths.get(t_id, []),
                }
            )

        combined_results.sort(key=lambda x: (x["score"], x["bm25_score"], x["graphrag_score"]), reverse=True)
        top_results = combined_results[:top_k]

        # Build GraphRAG synthesis summary
        if top_results:
            top_titles = [f"\"{r['title']}\" (by {r['author_username']})" for r in top_results[:3]]
            involved_users = sorted(
                {u for r in top_results for u in ([r["author_username"]] + r["user_mentions"])}
            )
            involved_agents = sorted({a for r in top_results for a in r["agent_mentions"]})
            involved_tags = sorted({f"#{t}" for r in top_results for t in r["tags"][:5]})
            synthesis = (
                f"GraphRAG + BM25 Synthesis for '{query}' ({mode.upper()} mode): "
                f"Retrieved {len(top_results)} connected topic(s) led by {', '.join(top_titles)}. "
                f"Active Cyberspace Peers: {', '.join(involved_users[:6]) or 'none'}. "
                f"Tagged AI Agents: {', '.join(involved_agents[:5]) or 'none'}. "
                f"Knowledge Graph Concepts: {', '.join(involved_tags[:8])}."
            )
        else:
            synthesis = f"No Cyberspace topics matched '{query}' in {mode.upper()} mode. Create a new topic and tag @gemini-brain!"

        return {
            "query": query,
            "mode": mode,
            "count": len(top_results),
            "results": top_results,
            "subgraph": subgraph,
            "synthesis": synthesis,
        }


__all__ = [
    "BM25Retriever",
    "CyberspaceBoardEngine",
    "CyberspaceGraphRAG",
    "KNOWN_AI_AGENTS",
    "parse_cyberspace_tags",
    "tokenize_for_bm25",
]
