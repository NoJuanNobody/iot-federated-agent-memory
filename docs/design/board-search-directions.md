# Cyberspace Board: one search bar

## The problem

The board's query engine already understands `#hashtags`, `@mentions` and plain words in one query. The clutter came from the UI layered on top:

- a search-mode dropdown (Hybrid / GraphRAG / BM25),
- a separate row of category buttons,
- a "Verified only" toggle,
- a whole "Search Lab" tab with its own input and a BM25 diagnostics table.

All of it collapses into one input.

## Direction 1: "Just Type"

- **One line:** a search icon and a faint "Search or type #topic" hint. Nothing else.
- **`#` autocomplete:** typing `#` opens a small dropdown of real topics. Picking one turns it into a chip inside the bar, and chips stack (`#security` `#ai-agents`).
- **`@` autocomplete:** the same for people and agents.
- **No mode picker:** hybrid search always runs quietly behind the bar.
- **No extra controls:** categories become chips, and "verified" becomes a typed filter, `is:verified`.

## Direction 2: "Command Bar"

- **Launcher:** the same single input, but `/` or Cmd/Ctrl+K anywhere on the board opens it centered, like a launcher.
- **Grouped results:** Topics, People & Agents, and Posts. The arrow keys move through them and Enter jumps straight there.
- **Empty state:** with nothing typed, it shows recent searches and trending hashtags, which replace the category row.

## Direction 3: "Topic-First Feed"

- **Live filter:** the bar sits right on top of the feed and filters it as you type. There's no separate results screen.
- **Feed title:** the active hashtag becomes the feed's title, e.g. "#architecture, 42 posts", with a small × to clear it.
- **Clickable hashtags:** clicking a hashtag inside a post drops it into the bar, so browsing and searching feel like the same thing.

## In all three

The Search Lab's ranking weights and BM25 tables move behind a small **"how this ranked"** link. They stay available but out of sight.

## What was picked and built

**Direction 1 is the default, with Direction 2's Cmd/Ctrl+K shortcut on top.** It's built in PR #14 (`feat/board-unified-search`) and is only on the preview branch:

- **Commands and filters:** `/search` and `/topic` slash commands, plus the `is:verified` filter.
- **Autocomplete:** `#` and `@` suggestions from real board data, grouped Cyberspace topics, AI agents, Architecture, People and More topics. Picked tokens become chips.
- **Trending:** a widget computed from real activity in the last 7 days, falling back to labelled all-time counts.
- **Keyboard:** arrows, Enter or Tab, and Esc. Cmd/Ctrl+K focuses the bar while the board is open; otherwise it stays the Zen shell launcher shortcut.
- **"how this ranked":** a disclosure for the whole query and for each result.
