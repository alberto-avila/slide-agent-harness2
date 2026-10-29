<edits>
component: guardrails.md
candidates: agg2, dom2, inv1, inv2
change: All four removed the base guidance for a mandatory agenda and routine 8–15-slide decks, and made the requested count more binding. The wording varied: agg2 says to fit opening, evidence, and closing within the count; dom2 says to match it; inv1 explicitly counts title and closing; inv2 refers to a requested range.
observed: In base1, critique prompted an eighth slide after a seven-slide outline; base2 grew from six to seven after critique. The edited runs agg2 and dom2 each saved six slides; inv1 also finished with six. Inv2 saved six slides, but its rollout shows an outline of five content titles followed by a title slide, then unresolved critique issues. The count guidance changed alongside other components in each candidate, so the contrast does not isolate guardrails.
verdict: confounded
</edits>

<edits>
component: systemprompt.md
candidates: agg2, dom2, inv1, inv2
change: The edits differed. agg2 revised the workflow and added a trigger to load the survey skill. dom2 added the same kind of skill trigger but left the base workflow intact. inv1 added a planned closing slide and post-save reopening. inv2 gave a more explicit process for interpreting the requested count, planning and adding slides, fixing critique issues, and inspecting the saved deck.
observed: agg2 planned and saved six slides, but finished after saving without inspecting. In dom2, critique led to editing the existing final slide; the rollout then saved six slides. Inv1 revised the existing final slide after critique, saved six slides, and used `view_deck` before finishing. Inv2 saved and finished with unresolved critique issues—including no closing takeaway—and did not inspect. Each rollout also changed other components, so these outcomes do not isolate the system prompt.
verdict: confounded
</edits>

<edits>
component: tool_descriptions/tool_guidance.md
candidates: agg2, inv1, inv2
change: agg2 added count-aware planning, a planned final takeaway, a preference for revising rather than appending after critique, post-save inspection, and a retry instruction to omit an unsupported `layout` argument. Inv1 added count-aware planning, in-place critique fixes, and inspection, but no layout-argument retry instruction. Inv2 added count/range-aware planning, one slide per planned title, in-place fixes where possible, and inspection.
observed: In agg2, the deck stayed at six slides and critique reported no issues, but the run ended after save without the requested inspection; no `edit_slide` retry was exercised. In inv1, critique prompted an edit to the existing final slide; three attempts with `layout` failed, then an edit without it succeeded, and the saved deck was inspected. In inv2, critique issues remained unresolved and the run saved and finished without inspection. System-prompt edits also addressed planning and inspection in these candidates, so the component’s contribution is not isolated.
verdict: confounded
</edits>

<edits>
component: skills/hr_survey_deck/SKILL.md
candidates: agg2, dom2
change: agg2 added an on-demand skill for an HR survey deck, covering story planning, source attribution, qualifier and population preservation, and a final source-check. dom2 added a longer skill with a six-slide default structure, decision framing, and this workspace’s specific survey facts and recommendations.
observed: agg2’s six-slide deck avoids base2’s claim that commute time is a job-satisfaction factor and does not call the burnout change significant, but it introduces an unsupported onboarding pilot in its closing slide. Dom2’s six-slide deck retains some distinctions but also makes stronger causal or policy claims, such as linking location to wellbeing and presenting recommendations as policy. Both skill edits appeared alongside other harness changes and each has only one rollout, so their effects cannot be separated.
verdict: confounded
</edits>

NO_ENTRY