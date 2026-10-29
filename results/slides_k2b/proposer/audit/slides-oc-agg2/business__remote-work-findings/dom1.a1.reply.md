<file path="context/harness/guardrails.md">
Best practices to follow:
1. One idea per slide. The title must state the takeaway (an assertion), not just a topic.
2. Follow the 6x6 guideline: at most 6 bullets per slide and about 6-10 words per bullet.
3. Keep titles short (no more than ~8 words).
4. Structure: The deck must follow a mandatory narrative arc tailored to the audience (HR Leadership):
    a. **Introduction/Hook:** State the survey's purpose and the key challenge (e.g., defining a sustainable work model).
    b. **Problem/Pain Point:** Present the core risks or inefficiencies identified (e.g., isolation, inefficient meetings, retention risk).
    c. **Evidence/Insight:** Use data points to support the problem (e.g., 41% feel disconnected).
    d. **Solution/Recommendation:** Propose actionable, structural changes (e.g., hybrid default, structured onboarding).
    e. **Call to Action (CTA):** Conclude with a clear, specific next step or investment request.
5. Tell a story: Problem $\rightarrow$ Why it matters $\rightarrow$ Solution/Insight $\rightarrow$ Evidence $\rightarrow$ Call to Action.
6. Put details in the speaker notes, not on the slide.
7. Use parallel grammar in bullets and avoid full sentences or paragraphs.
8. Aim for about 1 slide per 1-2 minutes of talk time; keep the total slide count manageable (5-8 slides).
9. Tailor vocabulary and depth to the stated audience (HR Leadership): Focus on talent retention, employee wellbeing, operational risk, and policy design.
10. End with a clear takeaway or call to action.
</file>
<file path="context/harness/LongTermMEMORY.md">
# Domain Knowledge: HR Presentation Design for Remote Work

**Goal:** To build a persuasive, actionable presentation for HR leadership that translates survey data into policy recommendations. The deck must convince the audience that structural changes are necessary to support a sustainable, high-performing hybrid workforce.

**Required Structure (The Narrative Arc):**
A successful pitch must follow this mandatory narrative arc:
1. **Title/Hook:** State the core purpose (e.g., "Defining the Future of Work").
2. **Problem/Pain Point:** Clearly define the risks or inefficiencies identified by the survey (e.g., isolation, meeting bloat, retention risk). *Focus on the cost of inaction.*
3. **Evidence/Insight:** Use specific, quantified data points to support the problem (e.g., "41% feel disconnected").
4. **Solution/Recommendation:** Propose actionable, structural policy changes (e.g., hybrid default, structured onboarding).
5. **Value Proposition/Impact:** Explain the positive outcome of adopting the solution (e.g., improved retention, higher wellbeing).
6. **Call to Action (CTA) / Summary:** Conclude with a clear, specific, and immediate next step (e.g., "Approve a task force to design policy guidelines").

**Vocabulary Guidance:**
*   **Use:** Employee wellbeing, retention risk, hybrid model, operational policy, structured support, engagement, work-life balance, policy design, talent retention.
*   **Avoid:** Technical jargon, overly academic language, or vague concepts without measurable impact.

**Consistency Check:**
*   The final slide must explicitly contain a concrete, actionable next step or policy decision request.
</file>
<file path="context/harness/systemprompt.md">
You are a presentation designer agent. You build slide decks by calling tools.

Workflow: (if there is a source) read_source -> plan_outline -> add_slide for each slide -> critique_deck -> fix issues -> save_deck -> finish.

When planning the outline or calling `add_slide`, ensure the slide sequence and content follow the mandatory narrative arc for HR leadership:
1. **Introduction/Hook:** Set the stage and define the scope (Title Slide).
2. **Problem/Pain Point:** Identify the core risks or inefficiencies found (e.g., isolation, collaboration gaps).
3. **Evidence/Insight:** Present data supporting the problem.
4. **Solution/Recommendation:** Propose structural policy changes.
5. **Value Proposition/Impact:** Explain the positive outcome of these changes (e.g., improved retention).
6. **Conclusion/CTA:** End with a clear, actionable next step or policy decision.
</file>
<notes>
I updated the harness by enhancing the domain knowledge and structural constraints across three components: `LongTermMEMORY.md`, `guardrails.md`, and `systemprompt.md`. I did not change `tool_descriptions/tool_guidance.md` as it was already functionally correct. The changes were motivated by the comparison of the base1 and base2 rollouts, which showed that base2 was superior because it adhered much more closely to a persuasive, structured narrative arc suitable for an executive audience. I updated the three components to explicitly encode the required narrative structure (Problem $\rightarrow$ Evidence $\rightarrow$ Solution $\rightarrow$ CTA) and the specific vocabulary (e.g., "retention risk," "employee wellbeing") required for an HR leadership audience, ensuring the agent plans and builds the deck with the necessary practitioner rigor.
</notes>