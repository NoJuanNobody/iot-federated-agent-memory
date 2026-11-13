# Brain Arena: which models can play

Full model tables, the autocomplete design and sources are on the Page **[TinCan Arena Model Registry Research](https://cursor.com/canvas/store-134f6331-1d79-4b67-9053-9bc2f50256f5/f1a2c4c3-3761-4ca3-a481-d82a46b3bc32)**. The work is tracked in Linear **AI-164 to AI-186** ("Ai mesíah" team, Backlog).

## Coverage by key

- **The OpenRouter key already covers five of the nine default duels:** text, budget text, free text, code and image.
- **Video, music, voice and 3D each need one more provider key.**
- **fal.ai is the best single extra key** because it covers the most media models.

## Not usable in the arena

- **No usable public API:** Midjourney, Suno and Udio. They're kept on a watchlist ([AI-186](https://linear.app/ai-mesiah/issue/AI-186/arena-watchlist-no-public-api-midjourney-suno-udio-sora-imagen-veo)).
- **Shut down:** the Sora API.
- **Dropped from Google's Gemini API:** Imagen 4 and the Veo 3 preview models. Runway still resells Veo 3.1.

## Problems found in `iot_federated_agent_memory/ai_gateway.py`

- **Stale defaults:** the gateway still defaults to old model IDs (`openai/gpt-4o`, `google/gemini-2.5-flash`).
- **Made-up Rodin entries:** `DEFAULT_OPENROUTER_MODELS` has `ronin/*` IDs and prices (`ronin/hyper3d-rodin-v2`, `ronin/regular`, `ronin/sketch`, `ronin/detail`, `ronin/smooth`). Hyper3D's real tiers are Gen-2 and Gen-2.5. The arena already excludes `ronin/` / `rodin/` / `hyper3d/` IDs from duels (PR #12).

## Linear tickets

- [AI-164](https://linear.app/ai-mesiah/issue/AI-164/arena-configurable-model-targets-model-registry): parent ticket, linked to the AI gateway and Rodin gateway tickets (AI-160, AI-163).
- [AI-165](https://linear.app/ai-mesiah/issue/AI-165/arena-model-registry-autocompletetag-search-for-the-model-id-field): the model registry, plus the autocomplete with hashtag and @provider search for the model ID field.
- **AI-166 to AI-185:** one ticket per provider, each listing the key, endpoint, models, capabilities and pricing. Pika (AI-178) is evaluate-only, because its API needs a $10/month membership and approval before signing up.
- [AI-186](https://linear.app/ai-mesiah/issue/AI-186/arena-watchlist-no-public-api-midjourney-suno-udio-sora-imagen-veo): watchlist for the models with no API.
- **Unconfirmed prices:** some prices couldn't be confirmed from official pages (Ideogram, Black Forest Labs, Luma, Meshy, Kling, Meta direct). Those tickets are marked "confirm".

## Who pays for a duel

As of PR #12, duels bill the **signed-in user's own account**. They never use the shared `peer` bucket:

- each side is checked against its worst-case token cost before dispatch (402 if the account can't cover it),
- each side is charged at the model's real cost and tagged `kind='arena'` in `token_ledger` with the match id and both models,
- the per-match cost is stored on `arena_matches`.

See [the credit lifecycle note](tincan-credit-lifecycle.md#brain-arena-duels).
