---
allowed-tools: Bash(find:*), Bash(git pull:*), Bash(git log:*), Bash(git diff:*), Bash(git status:*), Bash(git branch:*), Bash(cd:*), Bash(echo:*), Bash(date:*), Bash(head:*), Bash(tail:*), LS, Read, Grep, Task
description: Pull latest changes and provide deep analysis of commits with visual code snippets
argument-hint: [days] (default: 2) | [days] [repo-filter]
---

# 🌅 Morning Sync Analysis - !`date "+%A, %B %d, %Y"`

## Configuration
- Analysis period: Last ${ARGUMENTS:-2} days
- Repository root: /Users/will/repos/jemena
- Current time: !`date "+%I:%M %p"`

## Repository Scan
!`echo "Discovering repositories..." && find /Users/will/repos/jemena -type d -name ".git" -not -path "*/\.terraform/*" | wc -l | xargs -I {} echo "Found {} repositories to analyze"`

## Your Task

I need you to **ultra think** about the changes that happened in the last ${ARGUMENTS:-2} days across all Jemena repositories. 

### Deep Analysis Requirements:

1. **Pull latest changes** from all repositories under `/Users/will/repos/jemena`

2. **Analyze each commit** to understand:
   - WHY the change was made (infer from commit message and code changes)
   - WHAT problem it solves
   - HOW it impacts the overall system
   - WHO made the change and when

3. **Visual Code Analysis** - For significant changes:
   - Show before/after code snippets
   - Highlight the key differences
   - Include file paths with line numbers (format: `path/to/file.py:42`)
   - Focus on the most impactful 3-5 lines of each change

4. **Smart Categorization**:
   - 🏗️ Infrastructure (Terraform, CI/CD)
   - 🔌 Integrations (APIs, external systems)
   - 📊 Analytics & Data Processing
   - 🛡️ Security & Permissions
   - 🧹 Refactoring & Tech Debt
   - 📝 Documentation
   - 🐛 Bug Fixes

5. **Impact Assessment**:
   - Rate each change: 🔴 Critical | 🟡 Important | 🟢 Minor
   - Identify dependencies between changes
   - Flag any breaking changes or risks

6. **Summary Format** - For each repository with changes:
   ```markdown
   ### 📁 repository-name
   **Activity**: X commits by Y authors
   **Key Theme**: [Main focus of changes]
   
   #### 🎯 Most Significant Change
   **Why**: [Explanation of the motivation]
   **File**: path/to/file.tf:123
   ```
   ```diff
   - old code line
   + new improved line
   ```
   
7. **Executive Summary** at the top:
   - Top 3 most important changes across all repos
   - Any urgent items requiring attention
   - Patterns or trends observed

### Extended Thinking Triggers

Ultra think about:
- Which changes are interconnected across repositories?
- What's the bigger picture behind these changes?
- Are there any potential issues or conflicts?
- What follow-up work might be needed?
- How do these changes align with the Databricks migration goals?

Provide the analysis in a way that helps me quickly understand what happened and why it matters, with visual code snippets that make the changes crystal clear.

## Begin Analysis

Start by discovering all repositories and pulling the latest changes...