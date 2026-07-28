# AGI Phase 5 — Institutional Investment Office

```text
COMPANY: AGI
FOUNDATION: AGI v3.6 Institutional Judgment Release (FROZEN)
STATUS: Ready to begin — Sprint 5.1 is highest priority
UPDATED: 2026-07-28
```

## Premise

Phases 1–4 built the Institutional Judgment Layer.

Phase 5 answers a different question:

> **Given all this intelligence, how does AGI behave like a CIO over time?**

AGI becomes a CIO not because it knows more, but because it  
**makes, manages, monitors, and updates investment decisions.**

---

## Architecture shift

### Today (through v3.6)

```text
Question → Institutional Intelligence → Judgment → Reasoning → Answer
```

### Tomorrow (Phase 5)

```text
Question
  → Institutional Intelligence   (frozen)
  → Judgment                     (frozen — IEW→ICC)
  → Investment Thesis            (living object)
  → Decision                     (separate from analysis)
  → Portfolio                    (relative capital allocation)
  → Monitoring                   (thesis stays alive)
  → Learning                     (why the investment underperformed)
```

That is a **CIO operating system**.

---

## Hard rule

**Phase 5 must not modify the Phase 4 judgment stack.**

Consume:

* Weighted evidence (IEW)
* Hypothesis space + evaluation (IHG / IHE)
* Committee report (ICR)
* Confidence report (ICC)
* Evidence graph + institutional memory
* Existing reasoning / ICE outputs as needed

Do **not** extend IEW / IHG / IHE / ICR / ICC. Do **not** add Sprint 4.6.

---

## Sprint sequence

| Sprint | Module | Impact | Job |
|--------|--------|-------:|-----|
| **5.1** | **Institutional Investment Thesis Engine (ITE)** | ⭐⭐⭐⭐⭐ | Turn judgment into a **living Investment Thesis** |
| **5.2** | Institutional Decision Engine (IDE) | ⭐⭐⭐⭐⭐ | Separate analysis from decision (positive ≠ buy) |
| **5.3** | Portfolio Intelligence Office | ⭐⭐⭐⭐☆ | Relative thinking across peers / book |
| **5.4** | Monitoring & Catalyst Engine | ⭐⭐⭐⭐⭐ | Keep theses alive; alert on material change |
| **5.5** | Decision Learning Engine | ⭐⭐⭐⭐⭐ | Why the investment underperformed (not only why reasoning failed) |

---

## Sprint 5.1 — Institutional Investment Thesis Engine (ITE)

**Highest priority. Natural bridge from analysis → CIO operation.**

Today AGI answers:

> Why is Infosys expensive?

Tomorrow it creates a persistent object:

```text
Investment Thesis
  Company                  Infosys
  Investment View          Quality compounder with durable pricing power
  Bull Case                …
  Base Case                …   ← from ICR roles
  Bear Case                …
  Evidence                 …   ← from IEW / graph / memory
  Catalysts                …
  Risks                    …
  Invalidation             …
  Monitoring Checklist     …
  Expected Holding Period  …
  Decision Status          Watch
  Position Size            —
  Confidence               …/100 + reason   ← from ICC
  Last Updated             …
```

A thesis is a **living object**, not a chat response.

### ITE design principles (for Sprint 5.1)

* Persist theses (identity, version, as-of, citations)
* Map ICR Bull/Base/Bear roles into thesis cases
* Attach ICC confidence + reason
* Surface missing evidence as monitoring gaps
* Decision Status starts conservative (`Watch` / `No Position`) until IDE (5.2)
* Replay-safe / deterministic construction from frozen judgment packs
* Soft-wire only — do not change Reasoning internals

---

## Sprint 5.2 — Institutional Decision Engine (IDE)

Separate **Analysis** from **Decision**.

```text
Analysis  → Very positive
Decision  → Wait
Why       → Valuation is excessive
```

That is how CIOs work. IDE consumes theses + valuation / risk / sizing constraints. It must never silently equate “strong thesis” with “buy”.

---

## Sprint 5.3 — Portfolio Intelligence Office

Think **relative**:

```text
Infosys vs TCS vs LTIM vs Global SaaS
```

Capital, concentration, correlation, and opportunity cost — not single-name cheerleading.

---

## Sprint 5.4 — Continuous Monitoring

Every thesis stays alive:

```text
New filing
  → Evidence Graph updates
  → Confidence changes
  → Committee / thesis cases update
  → Decision may change
  → Alert
```

---

## Sprint 5.5 — Decision Learning

RCI evolves from engineering root-cause into **investment learning**:

* Catalyst wrong
* Valuation wrong
* Macro changed
* Management changed
* Competition changed
* Timing wrong
* Position sizing wrong

Ask: *Why did the investment underperform?* — not only *Why was reasoning wrong?*

---

## Entry criteria for Sprint 5.1

- [x] Phase 4 judgment stack implemented (IEW→ICC)
- [x] AGI v3.6 freeze document published
- [ ] ICR + ICC landed on `main` (merge #245)
- [ ] Soft certification numbers reconfirmed on `main` tip
- [ ] ITE sprint brief approved — **next build**

---

## Explicit non-goals for Phase 5 start

* No new evidence-weighting / hypothesis / committee / confidence engines
* No multi-agent debate theatre
* No replacing chat answers without persistence
* No auto-trading / execution without human governance (out of scope until later)

---

## One-line mandate

**Stop teaching AGI how to think. Teach it how to run an investment office.**
