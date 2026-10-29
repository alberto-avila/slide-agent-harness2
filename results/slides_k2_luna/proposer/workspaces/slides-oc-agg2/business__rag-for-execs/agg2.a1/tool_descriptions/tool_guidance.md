Tool guidance:
- Call plan_outline once before adding slides; use its titles as the complete plan, including the title and closing slides.
- Use layout "title" for the first add_slide; put the subtitle in bullets[0].
- Call critique_deck before save_deck. Check reported issues against the deck and fix valid ones in planned slides where possible; do not append a redundant slide if the requested count can be met by revising the closing slide.
- Do not pass a layout argument to edit_slide. If a tool error names an unexpected argument, remove it and retry once; do not repeat an unchanged failing call.
- After saving, inspect the saved deck with an available presentation or file-reading tool. Confirm the planned slide count and readable slide content.
