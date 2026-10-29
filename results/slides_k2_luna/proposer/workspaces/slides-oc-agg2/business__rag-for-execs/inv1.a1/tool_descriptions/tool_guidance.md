Tool guidance:
- Call plan_outline once before adding slides. Include the title and closing in the requested total; use the outline as the complete slide plan.
- Use layout "title" for the first add_slide; put the subtitle in bullets[0].
- Do not pass a layout argument to edit_slide. If a tool error names an unexpected argument, remove that argument and retry once; if the retry fails, stop and diagnose rather than repeating the call.
- Call critique_deck before save_deck. Fix its issues by editing planned slides where possible, then critique again. Do not append a slide if the requested total can be met by revising the planned closing slide.
- After saving, reopen or inspect the saved deck with an available presentation or file-reading tool. Confirm the saved deck opens and its slide order and count match the plan. If no inspection tool is available, do not claim that the saved deck was reopened.
