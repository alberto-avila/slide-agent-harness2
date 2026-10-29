# business/rag-for-execs

- adopted: `agg1`  (run `slides-oc-agg2/business/rag-for-execs/agg1`)
- components: always-on edits only; 4,383 always-on chars

## What each edit did
component: guardrails.md
candidates: agg1
change: Adopted the enhanced executive focus and detailed structure from the `dom2` candidate. This updated the structure to mandate a specific narrative arc and reinforced the focus on business outcomes.
observed: The resulting deck (agg1) consistently frames technical concepts (RAG) in terms of measurable business outcomes (ROI, compliance risk, time savings), and the structure follows the Problem $\rightarrow$ Solution $\rightarrow$ Value $\rightarrow$ CTA flow.
verdict: helped
component: LongTermMEMORY.md
candidates: agg1
change: Adopted the comprehensive structure and guidance from `dom2`. This provided a detailed, reusable guide on the required narrative arc, specific vocabulary (ROI, Compliance), and structural components for an executive pitch.
observed: The narrative flow is highly consistent, and the vocabulary used in the slides and notes (e.g., "operational risk," "strategic necessity," "measurable ROI") is perfectly tailored to a non-technical executive audience.
verdict: helped
component: tool_descriptions/tool_guidance.md
candidates: agg1
change: Adopted the mechanical fix from the `inv2` candidate, removing the unsupported `layout` keyword argument from `edit_slide`.
observed: The agent successfully executes the slide editing process without attempting to pass unsupported arguments, ensuring technical stability during the generation process.
verdict: helped
component: systemprompt.md
candidates: agg1
change: Updated to explicitly enforce the mandatory narrative arc (Problem $\rightarrow$ Solution $\rightarrow$ Value $\rightarrow$ CTA) across the entire slide creation process, combining the structural rigor of `inv2` with the content focus of `dom2`.
observed: The final deck structure (agg1) strictly adheres to the mandated sequence: Title $\rightarrow$ Problem (Slide 3) $\rightarrow$ Solution (Slide 4) $\rightarrow$ Value (Slide 5) $\rightarrow$ CTA (Slide 7).
verdict: helped

## Transferable lesson
- **cue**: When generating persuasive content for a high-stakes, non-technical audience (e.g., executives) that requires a specific, multi-stage argument (e.g., technology adoption).
- **lesson**: The system's long-term memory and system prompt must enforce a rigid, multi-stage narrative structure (Problem $\rightarrow$ Solution $\rightarrow$ Value $\rightarrow$ CTA) and simultaneously inject domain-specific constraints (e.g., "must use ROI language," "must avoid jargon") to ensure the content is both structurally sound and contextually relevant to the audience's priorities.
- **evidence**: The combination of the structural mandates from `inv2` (enforcing the mandatory narrative arc in `systemprompt.md`) and the domain-specific content guidance from `dom2` (defining the required narrative arc and vocabulary in `LongTermMEMORY.md`). This combination resulted in the `agg1` rollout, which demonstrated a perfect blend of structural rigor and executive-level business focus.
- **confidence**: high, because the successful output (agg1) is a direct and visible result of combining these two distinct types of constraints (structural enforcement and domain knowledge injection).
