# The BluMind Technical Committee

The **BluMind Technical Committee** is the body of senior practitioners
and researchers responsible for the integrity of the BluMind Benchmark.
It is the institutional authority behind every score, classification,
and appeal decision published in this repository.

This document is the canonical public reference for the committee. The
operational protocol — how the committee scores submissions, runs
appeals, and protects reviewer anonymity — is described in
[`docs/submission_guide.md`](docs/submission_guide.md).

---

## Mission and institutional role

BluMind evaluates AI models applied to the operation of water treatment
plants. The benchmark is meaningful only to the extent that its scoring
is grounded in real operational judgement. The committee exists to
ensure that grounding — score by score, case by case, version by
version.

The committee is **distributed and remote**, with members operating
from their respective locations. It functions as an institutional body,
not as the personal vehicle of any single member.

---

## Responsibilities

The committee is responsible for:

- **Scoring** every model response in the benchmark, applying the
  rubric and gold references defined in
  [`system/rubric/v1.0/`](system/rubric/v1.0/) and
  [`docs/methodology.md`](docs/methodology.md).
- **Resolving disagreement** within the scoring process, escalating to
  the full committee for collective decisions when two independent
  scorers cannot converge.
- **Reviewing appeals** filed by submitters under the procedure
  described in
  [`docs/submission_guide.md`](docs/submission_guide.md#appeals).
- **Refining the rubric, taxonomy, and case set** between benchmark
  versions, ensuring continuity and reproducibility while incorporating
  operational evidence accumulated during the prior version.
- **Approving new cases** before they enter a benchmark version.
- **Maintaining the integrity** of the public/commercial data split
  defined in this repository.

---

## Composition (v1.0)

The committee operates with a public roster and additional members
whose names are not yet publicly listed. The roster is updated as
those members complete their clearance to be listed publicly.

### Public members

**Álvaro Díaz del Río Redondo** — CEO and Founder of **BluMind**.
Previously **Head of Innovation and New Business Development at
Tedagua and Cobra Infraestructuras Hidráulicas (Grupo Cobra)** for over
five years, leading the creation of an innovation portfolio aligned
with corporate strategy across the water and energy verticals —
including project origination, corporate venturing, public and private
R&D funding, acceleration programs, and pilot execution of new digital
technologies in the water sector. **Mining Engineer from the
Universidad Politécnica de Madrid (UPM)** with an **Executive Master in
Innovation Leadership from IE Business School**.

**Rafael Jiménez Garrido** — Country Manager and Director of
Operations at **Whitewater Group**, with full P&L responsibility for
international EPC water infrastructure operations. Leads
multidisciplinary teams of 100+ professionals across engineering,
operations, and project delivery in complex international environments.
External Lecturer at the **Master's Degree in Desalination and Water
Reuse, Universidad de Alicante**. Industry expert contributor at
**ALADYR** (Latin American Desalination and Water Reuse Association).
Combines a strong engineering foundation with senior operational and
business leadership.

### Members pending public disclosure

Three additional senior international figures of the water sector are
part of the committee. Their names are not yet publicly listed,
pending clearance from their respective organizations, and are
expected to be disclosed during the v1.0 foundational phase:

- **Senior Advisor** — global desalination and water sector.
  *Negotiation in progress.*
- **C-level global** — CEO of an international water solutions
  operator and senior role in a sectoral industry body.
  *Negotiation in progress.*
- **Executive Director, Water** — large-scale water infrastructure
  programme, Middle East.
  *Negotiation in progress.*

These descriptions are intentionally non-specific to protect ongoing
arrangements. Names and full bios are added to this document only after
explicit written consent from the member.

---

## Selection and onboarding

New committee members are selected by invitation, based on:

- A minimum of **10 years of senior operational, technical, or
  research experience** in the water treatment sector, with priority
  in v1.0 to reverse-osmosis desalination.
- A demonstrable track record (publications, leadership roles, public
  projects, sectoral teaching, association membership) verifiable by
  the existing committee.
- No active commercial relationship with a model provider, evaluation
  laboratory, or system submitter that would create a material
  conflict of interest. Where such a relationship exists, the
  conflict-of-interest protocol below applies.

Upon acceptance, a new member signs the BluMind committee agreement,
which covers public listing, confidentiality of internal deliberations,
anonymity in scoring artifacts, and adherence to the rubric in force at
the time of scoring. Onboarding includes a calibration exercise on a
pilot case set so that newly seated members align with the rubric
before their first scoring of a submitted system.

---

## Confidentiality and anonymity protocol

The committee operates under two separate transparency rules — one
public, one private — that intentionally coexist:

- **Public**: the names of committee members are listed in this
  document and on BluMind's official website. This is what gives the
  benchmark its institutional weight.
- **Private**: when a specific response is scored, individual
  reviewers are identified in scoring files only by `reviewer_id`
  (`R01`, `R02`, …). The mapping from `reviewer_id` to identity is
  maintained in a registry kept outside this repository and is **not
  published**.

This separation protects individual reviewers from external pressure
on specific scores while preserving the institutional authority of the
committee as a whole. Committee members may publicly state their
membership in the committee. They may not publicly state which
specific score or critical-fail decision they cast for a given
submission.

The full protocol is described in
[`docs/submission_guide.md`](docs/submission_guide.md#scoring-by-the-blumind-technical-committee).

---

## Decision-making and governance

Day-to-day scoring uses two independent reviewers per response. The
committee escalates a response to **collective review** when:

- The two independent reviewers cannot reconcile their scores after a
  written exchange.
- An appeal has been filed by a submitter (see
  [Appeals](docs/submission_guide.md#appeals)).
- A new case is proposed for inclusion in the benchmark.
- The rubric, taxonomy, or scoring policy is being modified between
  versions.

During the foundational phase, collective decisions are taken by
consensus among publicly listed members, with not-yet-public members
participating under the same anonymity rules they hold elsewhere.
Formal voting procedures, term lengths, and rotation rules will be
introduced when the public roster reaches five members or earlier if
operational evidence requires it.

The committee does not delegate scoring or appeal decisions to
automated systems. AI tools may be used internally for transcription,
search, or summarization, but the operative judgement on every score
and decision remains with human committee members.

---

## Conflicts of interest

A committee member must disclose, in writing and before scoring
begins, any material relationship with a submitted system or its
provider, including:

- Current or recent employment, consulting, or advisory roles with the
  submitter.
- Financial interest in the submitter or in a direct competitor.
- Close personal or family relationship with a person responsible for
  the submitted system.

Once disclosed, the affected member **does not score** that
submission, **does not participate** in any appeal related to it, and
**does not influence** the scoring of other members for that
submission. The committee records the disclosure internally so that
the integrity of the evaluation can be audited later if needed.

Members are also expected to refuse engagements that would create such
conflicts in the future. Where a relationship is unavoidable, the
member may step back from a defined set of submissions or, in extreme
cases, from the committee for a limited period.

---

## Contact

For matters concerning the committee — including appeals, reviewer
recruitment, governance, or to flag a possible conflict of interest —
write to `committee@blumind.es`.

For benchmark submissions, use `submissions@blumind.es`. For pricing,
custom evaluations, and general inquiries, use `info@blumind.es`.
The full contact directory is in
[`docs/submission_guide.md`](docs/submission_guide.md#contact).
