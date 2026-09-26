---
name: sn-lab
description: >-
  Launch the SN1/SN2 Reaction Lab, a local app that animates nucleophilic
  substitution mechanisms. Use when a student wants to visualize, see, or
  understand how SN1 or SN2 reactions happen, "show me an SN2 mechanism",
  "animate a nucleophilic substitution", or invokes /sn-lab. Picks a
  substrate, nucleophile, and solvent from a curated textbook set (suggesting
  examples if none are given), predicts which mechanism dominates with the
  reasoning, and animates backside attack + inversion (SN2) or the
  carbocation intermediate (SN1) next to a reaction-energy diagram. No
  dependencies to install; nothing to configure.
argument-hint: "[substrate] [nucleophile] [solvent]"
---

# /sn-lab

Launch a local, single-page app that predicts and animates SN1 vs. SN2
nucleophilic substitution for a curated set of textbook substrates,
nucleophiles, and solvents.

## What to do

`<skill-dir>` is the "Base directory for this skill" reported when the skill
is invoked; use that absolute path.

1. Launch the app in the background:

   ```
   python3 "<skill-dir>/scripts/skill_launch.py"
   ```

   It's stdlib-only Python (no venv, no pip install, no Node) -- it just
   serves `frontend/` as static files on `http://127.0.0.1:8030` and opens
   that URL in the browser. If the port is already in use, rerun with
   `--port 8031` (or another free port).

2. The app opens with a working example already filled in and visualized, so
   there's nothing further you need to do to make it show something. If the
   student named a substrate, nucleophile, or solvent in `$ARGUMENTS`, tell
   them which dropdowns to change to match (the app has no text-input parsing
   -- it works entirely from its three `<select>` dropdowns plus one-click
   example buttons), since everything lives in one static page with no API to
   drive from here.

3. Point out, in your own words: they can pick any combination from the three
   dropdowns and press "Visualize the reaction", or click one of the example
   buttons for a ready-made scenario (classic SN2, classic SN1, a genuinely
   borderline secondary case, a solvolysis case, a resonance-stabilized
   primary case, and a sterically-hindered case where both mechanisms are
   slow). Whichever mechanism the app predicts, it explains why in plain
   language, then animates it: nucleophile approaching, leaving group
   departing, and (for SN2) the inversion of the other three groups, or (for
   SN1) the flat carbocation intermediate and attack from either face. A
   reaction-energy diagram runs alongside it, its marker tracking the
   animation.

4. Mention the playback controls once: Play/Pause, Step (jumps to the next or
   previous keyframe: reactants, transition state / intermediate, products),
   Reset, a speed slider, and a scrub bar to drag through the mechanism by
   hand.

There is nothing to draft or write back -- unlike voiceover or smithers, this
skill has no ongoing session state and no API for you to poll or push to. It
is entirely self-contained in the browser once launched.

## Scope

This is a teaching tool over a fixed, curated set (nine substrates spanning
methyl/primary/secondary/tertiary plus resonance-stabilized and sterically
hindered cases, nine nucleophiles, eight solvents) -- not a general molecule
drawer. If a student asks about a substrate that isn't in the list, say so and
suggest the closest curated analog (e.g., "we don't have 2-chlorobutane, but
2-bromobutane behaves the same way -- only the leaving group differs").
