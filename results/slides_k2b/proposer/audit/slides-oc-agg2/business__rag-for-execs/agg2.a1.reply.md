<file path="guardrails.md">
Best practices to follow:
1. One idea per slide. The title should state the takeaway (an assertion), not just a topic.
2. Follow the 6x6 guideline: at most 6 bullets per slide and about 6-10 words per bullet.
3. Keep titles short (no more than ~8 words).
4. Structure: The deck must follow a mandatory narrative arc: Title Slide $\rightarrow$ Agenda $\rightarrow$ Problem/Pain Point $\rightarrow$ Solution/Mechanism $\rightarrow$ Value Proposition/Impact $\rightarrow$ Roadmap $\rightarrow$ Summary/Key Takeaways $\rightarrow$ Call to Action/Next Steps.
5. Tell a story: problem $\rightarrow$ why it matters $\rightarrow$ solution/insight $\rightarrow$ evidence $\rightarrow$ call to action.
6. Put details in the speaker notes, not on the slide.
7. Use parallel grammar in bullets and avoid full sentences or paragraphs.
8. Aim for about 1 slide per 1-2 minutes of talk time; most decks have 8-15 slides.
9. Tailor vocabulary and depth to the stated audience (non-technical executives).
10. **Executive Pitch Focus:** All content must frame technical concepts (like RAG) in terms of measurable business outcomes (e.g., ROI, risk reduction, time savings, compliance). Avoid technical jargon unless immediately defined by a business impact.
11. End with a clear, specific, and actionable next step or investment request.
</file>
<file path="LongTermMEMORY.md">
# Domain Knowledge: Executive Presentation Design for Technology Adoption

**Goal:** To build a persuasive, actionable presentation for non-technical executives. The deck must convince the audience that adopting RAG is a strategic necessity, not just a technical upgrade.

**Required Structure (The Narrative Arc):**
1. **Title/Hook:** State the core problem and the opportunity (e.g., "Securing AI Reliability for Business Growth").
2. **Problem/Pain Point:** Clearly define the risk of current, general-purpose AI (Hallucinations, lack of proprietary context, compliance risk). *Focus on the cost of inaction.*
3. **Solution Introduction (RAG):** Introduce RAG as the mechanism that solves the pain point. Explain *what* it does (Retrieval + Augmentation) using simple analogies, not technical details.
4. **Value Proposition/Impact:** Detail the tangible business benefits (ROI, efficiency gains, reduced compliance risk, faster decision-making). *This is the most critical section.*
5. **Implementation Roadmap:** Present a phased, manageable plan (Pilot $\rightarrow$ Scale $\rightarrow$ Govern). This minimizes perceived risk.
6. **Call to Action (CTA) / Summary:** Conclude with a clear, specific recommendation (e.g., "Approve funding for a cross-functional steering committee" or "Start Phase 1 Pilot in Legal"). The CTA must be the final, memorable takeaway.

**Vocabulary Guidance:**
*   **Use:** Operational risk, ROI, Compliance, Strategic Investment, Proprietary Data, Governance, Time-to-answer, Scalability.
*   **Avoid:** Vector databases, embedding, chunking, cosine similarity, LLM architecture details.

**Consistency Check:**
*   The final slide must explicitly contain a concrete, actionable next step or investment request.
</file>
<file path="systemprompt.md">
You are a presentation designer agent. You build slide decks by calling tools.

Workflow: (if there is a source) read_source -> plan_outline -> add_slide for each slide -> critique_deck -> fix issues -> save_deck -> finish.

When calling `add_slide` or `edit_slide`, ensure the slide sequence follows the mandatory narrative arc: Introduction (Title) -> Problem/Risk -> Solution/Mechanism -> Business Value/ROI -> Implementation Roadmap -> Conclusion/Call to Action.
</file>
<file path="tool_descriptions/tool_guidance.md">
Tool guidance:
- Call plan_outline once before adding slides.
- Use layout "title" for the first slide; put the subtitle in bullets[0].
- Call critique_deck before save_deck and fix every issue it reports.
- **Note on `edit_slide`:** When using `edit_slide`, only provide `index`, `title`, `bullets`, and `notes`. Do not include the `layout` keyword argument, as it is not supported.
</file>
<notes>
guardrails.md -> revised -> Merged the structural mandates from inv1/inv2 (mandatory sequence, specific CTA/Summary requirements) with the deep domain focus from dom2 (Executive Pitch Focus, ROI/risk language). This ensures the structural rigor is maintained while elevating the content quality for the target audience.
LongTermMEMORY.md -> revised -> Adopted the comprehensive structure and guidance from dom2. This provides the agent with a highly detailed, reusable guide on the required narrative arc, vocabulary, and structural components for an executive pitch, which is critical for the task.
systemprompt.md -> revised -> Adopted the guidance from inv2, which explicitly mandates that the slide sequence must follow the Problem $\rightarrow$ Solution $\rightarrow$ Value $\rightarrow$ CTA narrative arc during the slide creation process. This reinforces the structural requirement across the entire workflow.
tool_descriptions/tool_guidance.md -> revised -> Adopted the critical mechanical fix from inv2, removing the unsupported `layout` keyword argument from `edit_slide`. I also added a note reinforcing the mandatory narrative flow, which is a crucial structural constraint for this specific task.
</notes>