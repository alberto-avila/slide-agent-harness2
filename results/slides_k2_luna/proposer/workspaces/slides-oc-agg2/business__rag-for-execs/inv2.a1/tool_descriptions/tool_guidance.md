Tool guidance:
- Call plan_outline once before adding slides. Treat its titles as the complete plan: include the title and closing slides in the requested total, then add slides in that order.
- Use layout "title" for the first slide; put the subtitle in bullets[0].
- In this toolset, edit_slide does not accept a layout argument. If it reports an unexpected keyword argument for layout, omit that argument on the corrected call; do not repeat the same failing input.
- Call critique_deck before save_deck. Check each reported issue against the actual deck: fix genuine omissions, preferably by editing an existing slide when that resolves the issue. Do not add a redundant slide when the deck already has the requested closing takeaway or next steps.
- After saving, use the available deck read-back or inspection tool, consulting its schema rather than guessing its name or arguments. Confirm the saved deck has the planned slide count and readable slide content. If that read-back fails, use one schema-informed correction or available alternative; if verification still cannot be completed, do not claim the deck was verified.
