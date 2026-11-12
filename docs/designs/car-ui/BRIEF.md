# TinCan OS · aftermarket car head unit

Design brief for UI concepts. Mockups only — no code changes in any repo.

## Goals

Bring TinCan Mesh OS onto a landscape aftermarket dashboard display (onboard computer, likely AMD, with a dashcam). The screen should feel like the same zen shell people already know, adapted for a car: glanceable while moving, fully usable when parked or by a passenger, and honest about identity and recording.

Tony asked that the look take a cue from Apple CarPlay’s structure — rounded app tiles, a clear persistent dock, glanceable cards — and then make it TinCan’s. No Apple assets, icons, SF Symbols, Apple logos, or the CarPlay name appear in the UI. Icons are drawn for this kit. The signature surface is a **dirty gradient**: grainy, slightly gritty color blends instead of clean ones, built with an SVG `feTurbulence` noise overlay on soft mixed washes.

## Constraints

- Head-unit canvas: **1280×720**. One later direction may use 1920×720 ultrawide.
- Dark, low-glare night palette. No navy. No gold. No xAI, Grok, or SpaceX marks.
- Stay consistent with the Mesh OS zen shell (see Reference, below). Do not invent a new brand.
- Touch targets **76px minimum**, meant for a parked driver or a passenger. Nothing in the driving view invites precise tapping.
- Watching and riding are open; pairing, switching drivers, browsing clips, and writing to a space are gated on a passkey and on being parked.
- Mockups only. Source lives in `/workspace/brand/tincan/car-ui/`, never inside a git checkout.

## Reference look

Pulled from the live Mesh OS design tokens in `iot-commit` / `iot-fam` (`DESIGN.md` and `iot_federated_agent_memory/zen_shell.py`), not invented:

| Token | Value | Use |
| --- | --- | --- |
| sumi / sumi-soft | `#0e0d0b` / `#17150f` | Stage and cards |
| washi | `#ece6da` and quiet/dim/hairline alphas | Type and lines |
| persimmon (kaki) | `#d0703f` | Active route, REC, focus |
| wash-rust / wash-moss / wash-umber | `#964622` / `#42522e` / `#705436` | Dirty-gradient washes |
| Mark type | Shippori Mincho 500/600 | Titles, speed, tile names |
| UI type | Zen Kaku Gothic New 400/500 | Meta, pills, body |
| Radii | panel 14–24px, tiles ~26px, capsules 999px | Cards and dock tiles |
| Grain | Already part of the zen shell (`#zenGrain`) | Extended here as the dirty gradient |

The existing shell is “a hushed ink-and-paper room around a vertical video feed, with every tool behind one mark.” Owner direction already on the product (2026-11-11): non-intrusive, “almost like Japanese zen, but dirty gradients,” feed as the room. The car parked home keeps that feed as atmosphere; the dock and tiles sit on top of it.

The Mesh OS token `wash-indigo` (`#2e365c`) is not used here — it reads as navy, which Tony dislikes.

## Information hierarchy

**Moving (above 0 mph).** One glance, then eyes back on the road.

1. Next maneuver and distance
2. Speed
3. Now playing (title only)
4. Dashcam REC (small, persistent)
5. Mesh status (small, persistent)

No clip browser, no launcher grid, no driver switcher, no search, no text fields.

**Parked.** Details may come forward: launcher and feed, full dashcam browser, identity and pairing, spaces sync.

## Touch targets

Dock tiles, media play, driver rows, clip rows, and launcher tiles are **80×80px or larger** (above the 76px floor). Driving-view chrome that is not a glance control is not offered as a target. Locked dock items stay visible so the layout does not jump, but they do not invite a tap.

## Night-dark, low-glare palette

Sumi grounds every screen. Washi is never used at full-field brightness — titles sit on sumi, secondary type at 60–66% washi. Persimmon is reserved for REC, the next-turn badge, and the active driver. Washes of rust, moss, and umber are mixed and then dirtied with grain so the glow stays soft. No pure white, no gold metallic, no cool navy night mode.

## Motion-lock rules (above 0 mph)

Hidden or disabled until the car is parked:

- Launcher / app grid
- Dashcam clip browser and delete/share
- Spaces browsing and manual sync controls
- Driver switcher and “add a driver”
- Account pairing and any typing
- Message composition

Still visible while moving: next turn, speed, now-playing, REC indicator, mesh seal, and a dimmed dock so the layout stays familiar. Copy on the driving view states the lock in plain language.

## Passkey identity

- Unlock prompt, verbatim intent: “Unlock with Face ID or fingerprint on your phone.”
- The head unit waits; the biometric happens on the phone, not on the dash camera.
- On success, the car pairs to the owner’s TinCan account and holds a sealed driver key on the unit.
- A driver switcher lists the owner and a Guest slot. Switching or adding a driver is parked-only and requires a passkey for that person.
- Watching the feed and hearing media do not require unlock; recording to a space and changing who is driving do.

## Dashcam behavior

- Loop recording can run while moving; a small REC pill is always glanceable.
- Events (hard brake, impact, manual save) lock so the loop cannot overwrite them.
- The clip browser opens only when parked. Locked events sit first; ordinary loop clips follow.
- Locked clips can sync to a TinCan space (here, “Tony’s Garage”). Sync status is a parked-only card, not a driving distraction.

## Directions

All three sit inside the same CarPlay-inspired, dirty-gradient language. They vary dock position, card density, and gradient mood — not the brand.

1. **Sumi Dock** (rendered first). Left persistent dock, warm sumi + persimmon + moss washes, large glance cards. Closest to a classic landscape head-unit map: dock on the thumb side, content to the right. Parked home keeps the zen feed as a vertical clip beside rounded tiles.
2. **Low Deck** (not rendered in this early pass). Bottom dock, wider landscape cards, calmer moss-heavy grain. Built for a passenger reaching across, and for ultrawide 1920×720 if needed.
3. **Mesh Halo** (not rendered in this early pass). Denser stacked cards, rust-heavier grit, identity built around two nodes and a string (the TinCan mark) instead of a single gate card.

## Recommendation

**Sumi Dock**, for this first pass: the left dock stays put across driving, parked, identity, and dashcam, so the motion lock can dim items without changing the skeleton. The parked feed column is the clearest link back to the zen shell. Low Deck and Mesh Halo should still be mocked if Tony wants a bottom reach or a heavier grain, but Sumi Dock is the one to put on the call.

## Open questions for Tony

- Is a left dock the right reach on this head unit, or would a bottom dock fit the dash better?
- Keep the phrase “Face ID,” or say “passkey on your phone” so the UI never uses an Apple product name?
- Confirm event-lock triggers (hard brake, impact, manual) and whether the loop may run while the car is unlocked / guest-driven.
- Is 1280×720 the real panel, or should the next pass be 1920×720 ultrawide?
- Besides Tony and Guest, should a named second driver appear in the switcher?
