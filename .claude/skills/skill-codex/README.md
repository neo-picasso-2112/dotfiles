# Usage

## Important: Thinking Tokens
By default, this skill suppresses thinking tokens (stderr output) using 2>/dev/null to avoid bloating Claude Code's context window. 
If you want to see the thinking tokens for debugging or insight into Codex's reasoning process, explicitly ask Claude to show them.

## Example Workflow
**User prompt**:
```Use codex to analyze this repository and suggest improvements for my claude code skill.```

Claude Code response: Claude will activate the Codex skill and:

Ask which model to use (gpt-5 or gpt-5-codex) unless already specified in your prompt.
Ask which reasoning effort level (low, medium, or high) unless already specified in your prompt.
Select appropriate sandbox mode (defaults to read-only for analysis)
Run a command like:
```
codex exec -m gpt-5-codex \
  --config model_reasoning_effort="high" \
  --sandbox read-only \
  --full-auto \
  --skip-git-repo-check \
  "Analyze this Claude Code skill repository comprehensively..." 2>/dev/null
```
Result: Claude will summarize the Codex analysis output, highlighting key suggestions and asking if you'd like to continue with follow-up actions.



