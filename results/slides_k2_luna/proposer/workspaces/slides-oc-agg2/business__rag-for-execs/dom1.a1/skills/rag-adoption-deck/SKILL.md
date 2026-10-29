---
name: rag-adoption-deck
description: Use when preparing an executive presentation about whether or why an organization should adopt Retrieval-Augmented Generation (RAG).
---

# RAG adoption deck

Build a decision deck, not a technology explainer. For non-technical executives, define Retrieval-Augmented Generation (RAG) once in plain language; connect it to a business workflow, evidence, tradeoffs, and a decision.

## Analytic move

Compare RAG with the current approach and relevant simpler alternatives for the stated use case. Use the task material and authorized sources as inputs. Deliver a recommendation or decision request supported by evidence, with assumptions and unresolved questions identified. Do not treat “adopt RAG” as the conclusion before assessing fit.

## Artifact contract

For a roughly six-slide deck, fit the story into the requested count; do not add a separate agenda or append a summary after the decision slide.

1. State the proposed decision or takeaway.
2. Describe the business problem or workflow and its evidenced impact.
3. Explain how RAG works at a high level and what it does not solve.
4. Make the value case using supported evidence, distinguishing measured results from hypotheses.
5. Present a bounded pilot, including the use case, authoritative data, access controls, owner, baseline, and success measures where the source material supports them.
6. Close with the decision requested, conditions for proceeding, and material open questions.

Before finishing, check that the recommendation follows from the evidence; every proposed benefit has a supportable basis or is explicitly a hypothesis; the pilot measures the stated benefit; and material risks or dependencies are not hidden in speaker notes alone. Put source details, caveats, assumptions, and implementation explanation in notes. Keep slide text concise and executive-readable.

## Decision rule

Recommend a pilot only when the proposed workflow, usable authoritative source material, permission handling, and a way to measure results are sufficiently defined. If those conditions are unclear, make the next decision a discovery or feasibility step rather than claiming readiness to scale. Resolve conflicting claims against the authorized source material; if they remain unresolved, state the conflict and its decision relevance.

## RAG-specific checks

- Describe retrieval as supplying relevant material to inform generation; do not imply the model is restricted to that material unless the design evidence establishes this.
- Do not promise that retrieval guarantees correctness, prevents hallucinations, makes every answer auditable, or ensures compliance.
- Treat source quality, freshness, retrieval quality, access permissions, and evaluation as dependencies to verify, not automatic properties of RAG.
- Compare against simpler options, such as improving search or using existing knowledge tools, when relevant to the stated workflow.
- Do not invent company data, use cases, ROI, metrics, pilot departments, vendors, or success thresholds. If the material gives no evidence for a claimed benefit, label it as a hypothesis or leave it out.
- Never invent authorities, standards, identifiers, or citations. Attribute factual claims to authorized sources; if none are supplied, keep company-specific claims conditional and make the evidence gap explicit.
- Use executive language focused on workflow, risk, value, and decision criteria. Avoid implementation jargon unless it changes the decision; explain any necessary term in plain language.
