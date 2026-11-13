# "Lights On": a story season for quests

> **Status: design, awaiting approval to build.** Nothing in this note is implemented yet.

The quests become a story season set in TinCan's Light Net vs Dark Net world. You play a new **Courier**. Every chapter is a real thing someone in your life needs help with, and every chapter ends in a **Brain Arena duel**, so dueling becomes the habit.

## Chapter pattern

Every chapter follows the same five beats:

1. **Hook:** a short opener, like a text from someone you know who's in trouble.
2. **Real task:** something you actually do in TinCan.
3. **Brain Arena duel:** ask two models the same question side by side.
4. **Vote:** your vote is a story choice. The brain that wins most often becomes your companion in later chapters.
5. **Reward:** XP, the existing quest badge, and the next story beat.

The zero-knowledge and mesh explanations stop being quests. They move into a short, optional **"how it worked"** note after each chapter.

Chapters unlock in order. Each one maps onto an existing `QUEST_CATALOG` key in `iot_federated_agent_memory/mesh_os_engine.py`, so the quest engine barely changes. It needs a chapter order, story text and an unlock gate.

## Act One: Waking Up

| # | Chapter | Replaces | `QUEST_CATALOG` key(s) | Real task | Duel |
| --- | --- | --- | --- | --- | --- |
| 1 | **Abuela's Text** | First Handshake | `workstation_handshake` | Your grandma forwards "your package is on hold, pay $2". Connect your laptop and paste the text. | Is it a scam, and what should she do? Vote for the answer you'd actually send her. |
| 2 | **The Letter** | Sealed Courier | `sealed_courier` (opening it counts as `inbox_decryption`) | Your cousin has to send you a lease and a gate code, and the Dark Net reads plain email. You send a sealed envelope and they open it on their end. | Explain what the seal protects against, in one paragraph. |
| 3 | **Moving Day** | New Ranger quest | No existing key yet. Until it's built, completion counts through `brain_arena_match`; the build adds a `ranger_moving_day` key. | Open your dev folder in the Ranger file browser and pick a messy project. This teaches the file browser. | Write that project's README. |

## Act Two: Building the Crew

| # | Chapter | Replaces | `QUEST_CATALOG` key(s) | Real task | Duel |
| --- | --- | --- | --- | --- | --- |
| 4 | **Movie Night** | Broadcast DJ + Party Signal | `curator_drop`, `watchparty_reaction` | A friend is far away. Drop a video into a watch party and react together live. | Pick the next video and pitch it in two lines. |
| 5 | **The Apprentice** | Apprentice Signal + Mentor Guidance | `mentee_hand_raise`, `mentor_guidance` | Your little brother's first Python script crashes. He raises his hand and you approve the session. | Who explains the bug more simply? |

## Act Three: Holding the Line

| # | Chapter | Replaces | `QUEST_CATALOG` key(s) | Real task | Duel |
| --- | --- | --- | --- | --- | --- |
| 6 | **The Council** | HITL Commander | `coop_hitl_trigger` | Your agent wants to send an email for you, and you approve or deny it. The lesson is that the human always signs off. | Should the agent have asked? Vote for the better reasoning. |
| 7 | **Verified Light** (finale) | Cyberspace Architect + Verified Citizen | `cyberspace_verified`, `cyberspace_post` | Get verified, then post a warning on the board about the scam from chapter 1 and tag `@verifier-agent`, so it helps the next abuela. | Write the warning post. |

The Brain Arena duel itself (`brain_arena_match`, "Synapse Arbiter") is the shared final beat of every chapter, so it has no chapter of its own.

## "How it worked" notes (optional, after each chapter)

- **The Letter:** X25519 sealed envelopes, and why only the recipient's key can open them (the old "Zero-Knowledge Reader" content).
- **Movie Night:** WebRTC relay and the mesh, and how the watch party stays in sync.
- **The Council:** human-in-the-loop approvals.
- **Verified Light:** how `@verifier-agent` attests identity.

## To build (once approved)

- **Catalog:** chapter metadata (act, order, hook, story text, how-it-worked text) next to `QUEST_CATALOG`.
- **Unlocks:** chapters unlock in order, gated on the previous chapter's key(s).
- **Companion:** track which model wins most votes per player.
- **New quest:** add the `ranger_moving_day` key.
- **Billing:** duels bill the signed-in account (PR #12), so every chapter's duel needs a sign-in. Chapter 1 has to handle new accounts that only have the 10 starter tokens.
