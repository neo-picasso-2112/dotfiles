---
allowed-tools: Bash(git status), Bash(git diff:*), Bash(git log:*), Bash(git branch:*), Bash(git show:*)
argument-hint: [base-branch]
description: Generate merge request title and description from branch changes
model: claude-sonnet-4-5-20250929
---

Analyze the current feature branch changes and generate a merge request title and description that's casual yet informative for developers.

Context: I'm on a feature branch and need to create a merge request. The base branch is: ${ARGUMENTS:-main}

Please:
1. First, check what branch I'm currently on using `git branch --show-current`
2. Look at the git diff between the current branch and the base branch to understand what changed
3. Review recent commit messages with `git log` to understand the development journey
4. Analyze the changes to understand the intent and purpose

Then generate:
- **MR Title**: A clear, concise title (50-72 chars) that captures the main change
- **MR Description**: A friendly 3-5 sentence description that:
  - Explains WHY these changes were made (the problem or need)
  - Briefly describes WHAT was changed (high-level, not every detail)
  - Mentions any important context developers should know
  - Keeps a casual, conversational tone without being overly technical

Format the output like this:
```
Title: [Your generated title here]

Description:
[Your generated description here]
```

Focus on making it easy for other devs to understand the purpose at a glance. Think of it like explaining the changes to a colleague over coffee - clear but not formal.