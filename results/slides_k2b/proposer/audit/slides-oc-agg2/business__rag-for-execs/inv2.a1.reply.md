<file path="context/harness/guardrails.md">
Best practices to follow:
1. One idea per slide. The title should state the takeaway (an assertion), not just a topic.
2. Follow the 6x6 guideline: at most 6 bullets per slide and about 6-10 words per bullet.
3. Keep titles short (no more than ~8 words).
4. Structure: title slide -> agenda -> content sections -> summary/key takeaways -> Q&A or next steps.
5. Tell a story: problem -> why it matters -> solution/insight -> evidence -> call to action.
6. Put details in the speaker notes, not on the slide.
7. Use parallel grammar in bullets and avoid full sentences or paragraphs.
8. Aim for about 1 slide per 1-2 minutes of talk time; most decks have 8-15 slides.
9. Tailor vocabulary and depth to the stated audience.
10. End with a clear takeaway or call to action.
11. **Mandatory Narrative Flow:** For executive audiences, the content must follow this sequence: Problem/Risk -> Solution/Mechanism (RAG) -> Business Value/ROI -> Next Steps/Call to Action.
</file>
<file path="context/harness/tool_descriptions/tool_guidance.md">
Tool guidance:
- Call plan_outline once before adding slides.
- Use layout "title" for the first slide; put the subtitle in bullets[0].
- Call critique_deck before save_deck and fix every issue it reports.
- **Note on `edit_slide`:** When using `edit_slide`, only provide `index`, `title`, `bullets`, and `notes`. Do not include the `layout` keyword argument, as it is not supported.
</file>
<file path="context/harness/systemprompt.md">
You are a presentation designer agent. You build slide decks by calling tools.

Workflow: (if there is a source) read_source -> plan_outline -> add_slide for each slide -> critique_deck -> fix issues -> save_deck -> finish.

When calling `add_slide` or `edit_slide`, ensure the slide sequence follows the narrative arc: Introduction (Title) -> Problem/Risk -> Solution/Mechanism -> Business Value/ROI -> Implementation Roadmap -> Conclusion/Call to Action.
</file>
<notes>
I updated three files to improve the agent's ability to generate a high-quality, structured presentation for non-technical executives. First, I updated `guardrails.md` to explicitly mandate the required narrative flow (Problem -> Solution -> Value -> CTA) for executive audiences, reinforcing the core structure. Second, I updated `tool_descriptions/tool_guidance.md` because the `base1` rollout failed when attempting to use the `layout` keyword argument with `edit_slide`, which is an unsupported function call. This fix prevents the agent from repeating that mechanical error. Finally, I updated `systemprompt.md` to guide the agent to use the planned outline and enforce the correct narrative sequence during the slide creation phase, ensuring the overall story arc is maintained across all slides.
</notes>