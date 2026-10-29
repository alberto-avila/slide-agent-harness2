Tool guidance:
- Call plan_outline once before adding slides. Include the title and closing within the requested total; use the outline as the complete plan.
- Use layout "title" for the first add_slide; put the subtitle in bullets[0].
- Call critique_deck before saving. Check each reported issue against the deck and fix genuine issues in existing planned slides where possible. Do not append a redundant slide or exceed the requested count.
- edit_slide does not accept a layout argument. If an error identifies layout as an unexpected argument, omit it from the corrected call while preserving other intended fields. Do not repeat an unchanged failing call; if the correction fails, consult the tool schema rather than guessing.
- After saving, inspect the saved deck with an available read-back tool, consulting its schema rather than guessing the tool name or arguments. Confirm slide count, order, and readable content. If inspection is unavailable or fails, do not claim verification or loop on failing calls; finish with the saved deck and an accurate status.
