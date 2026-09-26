# sn-lab

Animate SN1 and SN2 nucleophilic substitution reactions.

Claude launches a small local app -- a single static page, no install step --
where you pick a substrate, nucleophile, and solvent from a curated textbook
set. It predicts which mechanism wins and explains why, then animates it: the
backside attack and inversion of SN2, or the carbocation intermediate and
either-face attack of SN1, next to a reaction-energy diagram.

## Install

```
/plugin marketplace add kerryback/mgmt803-plugins
/plugin install sn-lab@mgmt803
```

Then `/sn-lab`, optionally naming a substrate, nucleophile, or solvent.

## What it covers

Nine substrates spanning methyl, primary, secondary, and tertiary halides,
plus two special cases worth seeing: resonance-stabilized primary substrates
(benzylic, allylic) that behave like secondary ones, and a sterically hindered
primary substrate (neopentyl bromide) where both mechanisms are slow. Nine
nucleophiles from strong (hydroxide, cyanide, azide) to weak (water,
methanol). Eight solvents, protic and polar aprotic.

If nothing is picked, the app opens with a worked example already visualized,
and one-click buttons fill in five more: a classic SN2, a classic SN1, a
genuinely borderline secondary case, a solvolysis case, and the steric-trap
case.

## How the call is made

Substrate class decides most of it: methyl/primary substrates can only go
SN2 (no stable carbocation forms), tertiary substrates can only go SN1
(backside attack is blocked outright). Secondary substrates -- and primary
ones stabilized by resonance -- are genuine toss-ups decided by nucleophile
strength (strong favors SN2) and solvent (protic favors SN1, polar aprotic
favors SN2). When it's genuinely close, the app says so and lets you toggle
between both animated pathways.

## Scope

A curated teaching set, not a general structure drawer -- there's no free-text
molecule input. If what you want isn't in the dropdowns, the closest curated
analog usually behaves the same way (the halide identity rarely changes which
mechanism wins).
