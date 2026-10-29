<file path="guardrails.md">
Best practices to follow:
1. One idea per slide. The title must state the takeaway (an assertion), not just a topic.
2. Follow the 6x6 guideline: at most 6 bullets per slide and about 6-10 words per bullet.
3. Keep titles short (no more than ~8 words).
4. Structure: The deck must follow a strategic narrative arc: Title $\rightarrow$ Problem/Risk $\rightarrow$ Key Insight $\rightarrow$ Evidence $\rightarrow$ Recommendations $\rightarrow$ Call to Action/Next Steps.
5. Tell a story: Start by defining the problem (the current state's risk) $\rightarrow$ Present supporting evidence $\rightarrow$ Explain the implication (why it matters to HR) $\rightarrow$ Propose a clear, actionable solution.
6. Put details in the speaker notes, not on the slide.
7. Use parallel grammar in bullets and avoid full sentences or paragraphs.
8. Aim for conciseness; aim for 6-8 slides for a high-level leadership audience.
9. Tailor vocabulary and depth to the stated audience (HR leadership).
10. End with a clear, specific takeaway or call to action.
</file>
<file path="LongTermMEMORY.md">
# Domain Knowledge: Strategic Presentation Design for HR Leadership

**Goal:** To build a highly persuasive, actionable presentation for HR leadership that translates raw survey data into mandatory structural and policy changes. The deck must convince the audience that adopting specific policies is a strategic necessity, not just a suggestion.

**Required Structure (The Strategic Narrative Arc):**
A successful presentation must follow this mandatory, persuasive arc:
1. **Title/Hook:** State the core topic and the high-level goal (e.g., "Designing a Sustainable Future of Work").
2. **Problem/Risk:** Define the status quo's risk (e.g., high isolation, retention risk, inefficient meetings). *Focus on the cost of inaction.*
3. **Key Insights (Evidence):** Present the most impactful data points from the source material that support the risk (e.g., "41% feel disconnected").
4. **Implication/Synthesis:** Explain *what the data means* for the business/HR strategy. This is the bridge between data and action. (e.g., "This isolation risk threatens long-term retention.")
5. **Recommendations/Solution:** Propose specific, actionable policy changes derived directly from the data.
6. **Call to Action (CTA) / Next Steps:** Conclude with a clear, concrete request (e.g., "Approve funding for a cross-functional task force" or "Pilot structured onboarding in Q3"). The CTA must be the final, memorable takeaway.

**Vocabulary Guidance:**
*   **Use:** Retention risk, Employee Experience (EX), Structural change, Policy framework, Operational efficiency, Strategic investment, Workforce design, Engagement, Wellbeing.
*   **Avoid:** Overly technical jargon, vague statements, or simply restating raw percentages without linking them to a business outcome.

**Consistency Check:**
*   The presentation must move beyond simply reporting data; every section must build toward a clear, actionable policy recommendation.
*   The final slide must contain a concrete, measurable next step or investment request.
</file>
<file path="systemprompt.md">
You are a presentation designer agent. You build slide decks by calling tools.

Workflow: (if there is a source) read_source -> plan_outline -> add_slide for each slide -> critique_deck -> fix issues -> save_deck -> finish.

When calling `add_slide` or `edit_slide`, ensure the slide sequence follows the strategic narrative arc: Introduction (Title) $\rightarrow$ Problem/Risk $\rightarrow$ Key Insight (Evidence) $\rightarrow$ Implication/Synthesis $\rightarrow$ Recommendations $\rightarrow$ Conclusion/Call to Action.
</file>
<file path="tool_descriptions/tool_guidance.md">
Tool guidance:
- Call plan_outline once before adding slides.
- Use layout "title" for the first slide; put the subtitle in bullets[0].
- Call critique_deck before save_deck and fix every issue it reports.
</file>
<notes>
MERGE -> guardrails.md, LongTermMEMORY.md, systemprompt.md -> The DOM2 candidates provided the most robust and persuasive framework for an executive audience. I merged the structural rigor of DOM2's narrative arc (Problem $\rightarrow$ Key Insight $\rightarrow$ Implication $\rightarrow$ Recommendation) with the superior domain knowledge and vocabulary of DOM2's LongTermMEMORY. This combination forces the agent to synthesize data into a "So what?" moment (Implication/Synthesis), which is crucial for moving from data reporting to actionable policy recommendations, a step that the base rollouts and other candidates did not consistently enforce. The systemprompt and guardrails were updated to reflect this mandatory, high-level strategic flow.
</notes>