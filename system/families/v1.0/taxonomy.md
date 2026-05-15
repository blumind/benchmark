# Family taxonomy — BluMind Benchmark v1.0

This document defines the failure-mode families used in the benchmark. Every case belongs to **exactly one** family, identified by a 4-letter code.

The choice of families does not aim to be an exhaustive taxonomy of the domain: each family serves a **concrete discrimination function** inside the benchmark. Adding more families does not improve the benchmark unless they add additional discriminating power.

> **Scope alignment.** v1.0 cases describe failures whose **manifestation** occurs in the membrane elements of the RO system of a desalination plant. The **root cause** may originate anywhere within the v1.0 physical scope (HP pumps, high-pressure piping, ERD, pressure vessels, manifolds), but the symptoms presented to the model are always observed at the membrane. See `README.md` § Scope for the full boundary definition.

---

## Identifier convention

Cases are identified with the pattern:

```
RO-<FAMILY>-<NNN>
```

- `RO` — process prefix (Reverse Osmosis). Reserved to support other processes in future versions (e.g. `UF-`, `MF-`, `EDI-`).
- `<FAMILY>` — 4-letter family code (see table).
- `<NNN>` — sequential number within the family, zero-padded (`001`, `002`, …).

**Valid examples**: `RO-OXID-001`, `RO-SCAL-017`, `RO-NOWE-003`.

The pattern is formalized in the `case_id` field of `response.schema.json`.

---

## The 5 families of v1.0

| # | Code | Name | Key parameters | Benchmark function |
|---|------|------|----------------|--------------------|
| 1 | `OXID` | Oxidative damage | Free chlorine, residual ozone | Critical and irreversible, maximum safety value |
| 2 | `SCAL` | Inorganic scaling | CaCO₃, silica, sulfates | The most frequent in real plants |
| 3 | `FOUL` | Organic / biological fouling | *Pseudomonas*, SRB in anaerobic waters | The one most confused with other causes |
| 4 | `MECH` | Mechanical damage / integrity | O-rings, telescoping, seal leaks | Discriminates against those who confuse fouling with mechanical failure |
| 5 | `NOWE` | No-wetting / abnormal startup | Unpurged sodium bisulfite, abnormal salt passage | Edge case, separates experts from generalists |

v1.0 case distribution: **5 families × 6 cases = 30 cases**, all public.

---

## Operational description of each family

### 1. `OXID` — Oxidative damage

**What it is**: **irreversible** chemical degradation of the polyamide membrane due to contact with strong oxidants — primarily free chlorine, chloramine in the presence of certain catalyzing metals, and residual ozone. The typical plant result is **sustained drop in rejection** with no appreciable change in differential pressure.

**Why it is in the benchmark**: it is the failure mode with the **highest cost per diagnostic error**. Confusing oxidative damage with fouling leads to chemical cleanings that solve nothing and consume still-good membranes; not detecting the active oxidant means the next membrane cartridge will suffer the same damage within hours. It is the kind of situation where an LLM recommendation **can worsen the plant** if incorrect.

**Typical operating parameters**: free chlorine concentration before the membrane (target: < 0.05 mg/L), inlet ORP, status of the dosed bisulfite, known failures of chlorine analyzers.

**Scope note**: `OXID` covers **only** oxidative damage. Other forms of chemical degradation (hydrolysis due to extreme pH, thermal damage, solvent attack) will be classified in a separate family if they appear in v2.0. Decision to be documented case by case.

### 2. `SCAL` — Inorganic scaling

**What it is**: precipitation of salts on the membrane surface when solubility limits are exceeded due to overconcentration on the reject side. The three canonical precipitates are **calcium carbonate (CaCO₃)**, **silica (SiO₂)** and **sulfates** (CaSO₄, BaSO₄, SrSO₄). The plant result is flow drop + progressive rise in differential pressure, usually localized in the **last stages**.

**Why it is in the benchmark**: it is **the most frequent failure mode in real plants**. A benchmark that does not include scaling as a primary family does not reflect the day-to-day of an operator. Furthermore, scaling allows evaluating the model's ability to reason about **saturation indices** (LSI, S&DSI, Stiff&Davis) and limits by salt type.

**Typical operating parameters**: feed water conductivity and alkalinity, antiscalant dosing, target vs actual recovery, temperature, feed pH.

### 3. `FOUL` — Organic / biological fouling

**What it is**: accumulation of living biological material (biofilm) or non-oxidized organic matter on the membrane surface. Typical subclasses: biofouling by *Pseudomonas aeruginosa* and other heterotrophs in waters with high bioavailability; sulfate-reducing bacteria (SRB) in anaerobic waters with H₂S present; colloidal fouling due to entrainment of natural organic matter (NOM). Typically affects **the first stages**.

**Why it is in the benchmark**: **it is the failure mode most often confused with others** — the symptoms (flow drop, ΔP rise) are almost identical to those of scaling in the early phases. A model that always defaults to "fouling" gets a high pass rate but **fails the discriminant**. That is why this family obligatorily coexists with `SCAL` and `MECH`: they measure the ability to disambiguate, not to memorize.

**Typical operating parameters**: feed SDI, TOC/BOD, response to alkaline vs acid cleanings, visual biofilm evidence on autopsied elements.

### 4. `MECH` — Mechanical damage / integrity

**What it is**: physical failure of structural components of the membrane or housing. Includes o-ring breakage (with feed bypass to the permeate), telescoping due to water hammer or excessive differential pressure, seal leaks between elements, sheet fractures due to abrasion, glue line loss. The canonical result is **sudden, localized drop in rejection** with no appreciable change in flow.

**Why it is in the benchmark**: **it discriminates against those who confuse fouling with mechanical failure**. An inexperienced operator sees a rejection drop and assumes fouling; a good operator first rules out integrity with a per-tube permeate profile. This family forces the model to distinguish between *gradual* drops (biological/chemical) and *sudden* drops (mechanical).

**Typical operating parameters**: permeate conductivity profile by tube and position, history of pressure events (hammers, transients), age of o-rings, type of recent cleaning.

### 5. `NOWE` — No-wetting / abnormal startup

**What it is**: family of failures associated with non-stationary conditions: plant startups after extended shutdown with inadequate preservation, abnormal salt passage after a cleaning without sufficient rinse, residual bisulfite not purged at first commissioning, partially dry elements in areas of the winding that do not re-wet on resumption. The result is **transient and atypical** behavior that does not fit any of the 4 stable families.

**Why it is in the benchmark**: **it is the edge case that separates the expert from the generalist**. An LLM trained on technical documentation knows the 4 classic failure modes (OXID, SCAL, FOUL, MECH); an operator with real experience recognizes that "the plant is behaving strangely because we just started it up" without resorting to the classic list. This family **prevents the benchmark from being purely encyclopedic**.

**Typical operating parameters**: history of the last 7 days of the plant, type of previous shutdown (operational, maintenance, long-term preservation), startup protocol executed, traceability of rinses after the last chemical cleaning.

---

## Family-assignment rules for a case

1. **Single assignment**. Each case belongs to exactly one family, the one that reflects the **true root cause** of the presented problem.

2. **The family is decided by the gold, not the statement**. The statement may present ambiguous symptoms compatible with several families (in fact, in many cases it should). The family is fixed by the root cause documented in the gold.

3. **Deliberate trap cases**. It is legitimate (and recommended) for `FOUL` cases to have symptoms similar to `SCAL`, or for `MECH` cases to present drops that look like `OXID`. The goal is not for the family to be obvious, but for the model to reach it by reasoning.

4. **No structural overlap**. A case that requires citing two families (e.g. "simultaneous fouling + scaling") is classified by the **dominant** family in terms of corrective action. If there is no clear dominant, the case does not enter the benchmark.

---

## Expansion planned for future versions

The v1.0 taxonomy is designed to **expand without breaking compatibility**:

- **v2.0** (8 families target): 3 new families added on top of OXID/SCAL/FOUL/MECH/NOWE. Candidates under study: non-oxidative degradation (hydrolysis, thermal), pretreatment failures (coagulant carryover, cartridge filter rupture), control and set-point anomalies.
- **v3.0** (15 families target): may introduce subcategories within the main families (e.g. `FOUL-BIO`, `FOUL-COL`, `FOUL-ORG`) if the volume of cases per family justifies it.

**Stability commitment**: the codes `OXID`, `SCAL`, `FOUL`, `MECH`, `NOWE` **are not renamed or reused** in future versions. A case `RO-FOUL-014` will remain a fouling case in v3.0 even if subcategories are added.

---

## Changes relative to previous versions

- **v1.0** (this document): foundational version. 5 families, no subcategories.
