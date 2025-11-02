---
description: Provide a code review for the branch $ARGUMENTS
model: openai/gpt-5-codex-high
---
Provide a code review for the given pull request.

To do this, follow these steps precisely:

1. Check with the user which repository folder to do a code review for this feature branch unless otherwise specified. If no $ARGUMENTS is provided, then assume user wants you to review the current branch in current repository.
2. Use another agent to give you a list of file paths to (but not the contents of) any relevant CLAUDE.md files from the codebase: the root CLAUDE.md file (if one exists), as well as any CLAUDE.md files in the directories whose files the pull request modified.
- In addition, this agent should also explore @/Users/williamnguyen/repos/docs/<name-of-repository> to check if there are any markdown documentation recursively that might be relevant. You will need to list files and run `grep` to find relevant documentation. Remember to swap out `<name-of-repository` for the repository folder name you're doing the code review for.
3. Use an agent to view the branch, and ask the agent to return a summary of the change
4. Then, launch 4 parallel agents to independently code review the change. The agents should do the following, then return a list of issues and the reason each issue was flagged (eg. CLAUDE.md adherence, bug, historical git context, etc.):
   a. Agents #1 and #2: Independently audit the changes to make sure they compily with the CLAUDE.md
   b. Agent #3: Read the file changes in the pull request, then do a shallow scan for obvious bugs. Avoid reading extra context beyond the changes, focusing just on the changes themselves. Focus on large bugs, and avoid small issues and nitpicks. Ignore likely false positives.
   c. Agent #5: Read the git blame and history of the code modified, to identify any bugs in light of that historical context
5. For each issue found in #4, launch a parallel agent that takes the PR, issue description, and list of CLAUDE.md files (from step 2), and returns a score to indicate the agent's level of confidence for whether the issue is real or false positive. To do that, the agent should score each issue on a scale from 0-100, indicating its level of confidence. For issues that were flagged due to CLAUDE.md instructions, the agent should double check that the CLAUDE.md actually calls out that issue specifically. The scale is (give this rubric to the agent verbatim):
   a. 0: Not confident at all. This is a false positive that doesn't stand up to light scrutiny, or is a pre-existing issue.
   b. 25: Somewhat confident. This might be a real issue, but may also be a false positive. The agent wasn't able to verify that it's a real issue. If the issue is stylistic, it is one that was not explicitly called out in the relevant CLAUDE.md.
   c. 50: Moderately confident. The agent was able to verify this is a real issue, but it might be a nitpick or not happen very often in practice. Relative to the rest of the PR, it's not very important.
   d. 75: Highly confident. The agent double checked the issue, and verified that it is very likely it is a real issue that will be hit in practice. The existing approach in the PR is insufficient. The issue is very important and will directly impact the code's functionality, or it is an issue that is directly mentioned in the relevant CLAUDE.md.
   e. 100: Absolutely certain. The agent double checked the issue, and confirmed that it is definitely a real issue, that will happen frequently in practice. The evidence directly confirms this.
6. Filter out any issues with a score less than 80. If there are no issues that meet this criteria, do not proceed.
7. Finally, output the code review to the user sorted by critical issues first.

Examples of false positives, for steps 4 and 5:

- Pre-existing issues
- Something that looks like a bug but is not actually a bug
- Pedantic nitpicks that a senior engineer wouldn't call out
- Issues that a linter will catch (no need to run the linter to verify)
- General code quality issues (eg. lack of test coverage, general security issues), unless explicitly required in CLAUDE.md
- Issues that are called out in CLAUDE.md, but explicitly silenced in the code (eg. due to a lint ignore comment)

Notes:
- Use !`git fetch origin` to fetch remote branches and `git switch $1` to switch to the branch to do a code review.
- Make a todo list first
- You must cite and link each bug (eg. if referring to a CLAUDE.md or some documentation found under docs/, you must the directory path)
- For your comment, follow the following format precisely (assuming for this example that you found 3 issues):

---

## Code review

Found 3 issues:

1. <brief description of bug> (CLAUDE.md says "<...>")

<link to file and line + line range for context>

2. <brief description of bug> (some/other/CLAUDE.md says "<...>")

<link to file path and line+ line range for context>

3. <brief description of bug> (bug due to <file and code snippet>)

<link to file and line + line range for context>

---

- Or, if you found no issues:
No issues found. Checked for bugs and repository documentation and CLAUDE.md compliance.
---
