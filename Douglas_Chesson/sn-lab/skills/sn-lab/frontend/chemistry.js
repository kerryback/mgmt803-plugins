// Curated textbook data + the SN1/SN2 decision heuristic.
// Every substrate has exactly three non-leaving substituents (`groups`), so the
// carbon is always a simple sp3 center with one leaving group.

const SUBSTRATES = [
  {
    id: "methyl-bromide",
    name: "Bromomethane -- CH3Br",
    formula: "CH3Br",
    cls: "methyl",
    groups: ["H", "H", "H"],
    lg: "Br",
    note: "No steric hindrance to backside attack, and a methyl cation is far too unstable to form.",
  },
  {
    id: "ethyl-bromide",
    name: "Bromoethane -- CH3CH2Br",
    formula: "CH3CH2Br",
    cls: "primary",
    groups: ["H", "H", "CH3"],
    lg: "Br",
    note: "Primary carbon: open to backside attack, and a primary cation would be too unstable to form.",
  },
  {
    id: "isopropyl-bromide",
    name: "2-Bromopropane -- (CH3)2CHBr",
    formula: "(CH3)2CHBr",
    cls: "secondary",
    groups: ["H", "CH3", "CH3"],
    lg: "Br",
    note: "Secondary carbon: a secondary cation is stable enough to form, but backside attack is still possible. Nucleophile and solvent decide.",
  },
  {
    id: "sec-butyl-bromide",
    name: "2-Bromobutane -- CH3CHBrCH2CH3",
    formula: "CH3CHBrCH2CH3",
    cls: "secondary",
    groups: ["H", "CH3", "CH2CH3"],
    lg: "Br",
    note: "Secondary carbon, same tradeoff as 2-bromopropane -- also a classic stereocenter, so SN2 gives clean inversion and SN1 gives a racemic mixture.",
  },
  {
    id: "bromocyclohexane",
    name: "Bromocyclohexane",
    formula: "C6H11Br",
    cls: "secondary",
    groups: ["H", "ring-CH2", "ring-CH2"],
    lg: "Br",
    note: "Secondary and cyclic, but otherwise behaves like an open-chain secondary halide.",
  },
  {
    id: "tert-butyl-bromide",
    name: "2-Bromo-2-methylpropane -- (CH3)3CBr",
    formula: "(CH3)3CBr",
    cls: "tertiary",
    groups: ["CH3", "CH3", "CH3"],
    lg: "Br",
    note: "Tertiary carbon: the three methyls block backside attack outright, so SN2 cannot compete. The tertiary cation is stable, so SN1 dominates whenever ionization is possible.",
  },
  {
    id: "benzyl-bromide",
    name: "Benzyl bromide -- PhCH2Br",
    formula: "C6H5CH2Br",
    cls: "primary",
    resonance: "benzylic",
    groups: ["H", "H", "C6H5"],
    lg: "Br",
    note: "Primary carbon, so backside attack is wide open -- but the cation is resonance-stabilized by the ring, so SN1 is also a real option. Behaves like a secondary substrate.",
  },
  {
    id: "allyl-bromide",
    name: "Allyl bromide -- CH2=CHCH2Br",
    formula: "C3H5Br",
    cls: "primary",
    resonance: "allylic",
    groups: ["H", "H", "CH=CH2"],
    lg: "Br",
    note: "Primary carbon, but resonance with the adjacent double bond stabilizes the cation. Behaves like a secondary substrate.",
  },
  {
    id: "neopentyl-bromide",
    name: "Neopentyl bromide -- (CH3)3CCH2Br",
    formula: "(CH3)3CCH2Br",
    cls: "primary",
    hindered: true,
    groups: ["H", "H", "C(CH3)3"],
    lg: "Br",
    note: "Primary, so no stable cation can form -- but the bulky tert-butyl group right next door blocks backside attack too. Both mechanisms are slow; SN2 eventually wins, at a crawl.",
  },
];

const NUCLEOPHILES = [
  { id: "hydroxide", name: "Hydroxide -- HO⁻", symbol: "HO⁻", strength: "strong", charge: -1 },
  { id: "methoxide", name: "Methoxide -- CH3O⁻", symbol: "CH3O⁻", strength: "strong", charge: -1 },
  { id: "cyanide", name: "Cyanide -- NC⁻", symbol: "NC⁻", strength: "strong", charge: -1 },
  { id: "azide", name: "Azide -- N3⁻", symbol: "N3⁻", strength: "strong", charge: -1 },
  { id: "iodide", name: "Iodide -- I⁻", symbol: "I⁻", strength: "strong", charge: -1 },
  { id: "thiolate", name: "Ethanethiolate -- CH3CH2S⁻", symbol: "CH3CH2S⁻", strength: "strong", charge: -1 },
  { id: "ammonia", name: "Ammonia -- NH3", symbol: "NH3", strength: "moderate", charge: 0 },
  { id: "water", name: "Water -- H2O", symbol: "H2O", strength: "weak", charge: 0 },
  { id: "methanol", name: "Methanol -- CH3OH", symbol: "CH3OH", strength: "weak", charge: 0 },
];

const SOLVENTS = [
  { id: "water", name: "Water", type: "protic" },
  { id: "methanol", name: "Methanol", type: "protic" },
  { id: "ethanol", name: "Ethanol", type: "protic" },
  { id: "acetic-acid", name: "Acetic acid", type: "protic" },
  { id: "acetone", name: "Acetone", type: "aprotic" },
  { id: "dmso", name: "DMSO", type: "aprotic" },
  { id: "dmf", name: "DMF", type: "aprotic" },
  { id: "acetonitrile", name: "Acetonitrile", type: "aprotic" },
];

const EXAMPLES = [
  {
    label: "Classic SN2",
    substrate: "ethyl-bromide",
    nucleophile: "hydroxide",
    solvent: "acetone",
  },
  {
    label: "Classic SN1",
    substrate: "tert-butyl-bromide",
    nucleophile: "water",
    solvent: "water",
  },
  {
    label: "Secondary: it depends",
    substrate: "sec-butyl-bromide",
    nucleophile: "ammonia",
    solvent: "ethanol",
  },
  {
    label: "Secondary, solvolysis",
    substrate: "isopropyl-bromide",
    nucleophile: "methanol",
    solvent: "methanol",
  },
  {
    label: "Resonance-stabilized",
    substrate: "benzyl-bromide",
    nucleophile: "water",
    solvent: "ethanol",
  },
  {
    label: "Steric trap",
    substrate: "neopentyl-bromide",
    nucleophile: "azide",
    solvent: "dmf",
  },
];

function byId(list, id) {
  return list.find((x) => x.id === id);
}

// Returns { mechanism: "SN2"|"SN1"|"borderline", reasons: string[], slow: bool }
function decideMechanism(substrate, nucleophile, solvent) {
  const reasons = [];

  if (substrate.cls === "tertiary") {
    reasons.push(
      `${substrate.name} is tertiary: the three alkyl groups crowd the backside of the carbon, so SN2 is blocked outright.`
    );
    reasons.push(
      "A tertiary carbocation is stable (hyperconjugation from three alkyl groups), so ionization can proceed on its own."
    );
    reasons.push(
      solvent.type === "protic"
        ? `${solvent.name} is protic -- it stabilizes both the departing leaving group and the carbocation by hydrogen bonding, which speeds ionization.`
        : `${solvent.name} is aprotic -- ionization is slower here than in a protic solvent, but SN2 is still blocked, so SN1 remains the only path.`
    );
    return { mechanism: "SN1", reasons, slow: false };
  }

  if (substrate.hindered) {
    reasons.push(
      `${substrate.name} is primary, so no stable carbocation can form -- SN1 is not viable.`
    );
    reasons.push(
      "The bulky neopentyl-type branch sits one carbon away from the leaving group and swings directly into the path of an incoming nucleophile, so even SN2 is very slow."
    );
    reasons.push("SN2 still happens eventually -- it is simply the only door left, and it is a narrow one.");
    return { mechanism: "SN2", reasons, slow: true };
  }

  if (substrate.cls === "methyl" || (substrate.cls === "primary" && !substrate.resonance)) {
    reasons.push(
      `${substrate.name} is ${substrate.cls}: the backside of the carbon is wide open, and a ${substrate.cls} carbocation is too unstable to form.`
    );
    reasons.push("SN2 is the only mechanism available, regardless of the nucleophile or solvent chosen.");
    reasons.push(
      nucleophile.strength === "weak"
        ? `${nucleophile.name} is a weak nucleophile, so the reaction will simply be slow SN2, not a switch to SN1.`
        : `${nucleophile.name} is a good nucleophile here, so the reaction proceeds readily by SN2.`
    );
    return { mechanism: "SN2", reasons, slow: nucleophile.strength === "weak" };
  }

  // Secondary, or primary with resonance stabilization (benzylic/allylic): genuinely borderline.
  let score = 0;
  if (substrate.resonance) {
    reasons.push(
      `${substrate.name} is primary, but the cation is stabilized by resonance (${substrate.resonance}), so it behaves like a secondary substrate -- either mechanism is plausible.`
    );
  } else {
    reasons.push(
      `${substrate.name} is secondary: a secondary carbocation is stable enough to form, and backside attack is still geometrically possible. The nucleophile and solvent decide which wins.`
    );
  }

  if (nucleophile.strength === "strong") {
    score += 2;
    reasons.push(`${nucleophile.name} is a strong, reactive nucleophile -- it favors SN2 by attacking before a cation can form.`);
  } else if (nucleophile.strength === "moderate") {
    score += 0.4;
    reasons.push(`${nucleophile.name} is a moderate nucleophile -- a mild push toward SN2.`);
  } else {
    score -= 2;
    reasons.push(`${nucleophile.name} is a weak nucleophile -- it is a poor attacker, which favors SN1 (it can instead trap the carbocation once one forms).`);
  }

  if (solvent.type === "aprotic") {
    score += 1.5;
    reasons.push(`${solvent.name} is polar aprotic -- it does not cage the nucleophile in hydrogen bonds, keeping it "naked" and reactive, which favors SN2.`);
  } else {
    score -= 1.5;
    reasons.push(`${solvent.name} is protic -- it stabilizes the leaving group and any carbocation by hydrogen bonding, and it weakens the nucleophile, which favors SN1.`);
  }

  if (score > 1.5) {
    return { mechanism: "SN2", reasons, slow: false };
  }
  if (score < -1.5) {
    return { mechanism: "SN1", reasons, slow: false };
  }
  reasons.push("These factors pull in opposite directions -- in practice both mechanisms compete, with a mix of products.");
  return { mechanism: "borderline", reasons, slow: false };
}
