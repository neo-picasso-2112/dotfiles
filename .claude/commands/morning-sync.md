---
allowed-tools: Bash(*:*), LS, Read, Grep, Task
description: Advanced repository analysis with smart branch detection, activity filtering, and cross-repo insights  
argument-hint: [days] [--active-only] [--format=compact|detailed] [--repos=pattern] [--author=name]
---

# 🌅 Morning Sync Analysis - !`date "+%A, %B %d, %Y at %I:%M %p"`

## ⚙️ Smart Configuration
**Analysis Period**: ${ARGUMENTS:-2} days  
**Repository Root**: `/Users/will/repos/jemena`  
**Mode**: Advanced analysis with cross-repo intelligence

## 📡 Repository Discovery & Branch Intelligence
!`cd /Users/will/repos/jemena && for repo_git in $(find . -name ".git" -type d -not -path "*/\.terraform/*"); do repo_dir=$(dirname "$repo_git"); repo_name=$(basename "$repo_dir"); cd "$repo_dir"; default_branch=$(git symbolic-ref refs/remotes/origin/HEAD 2>/dev/null | cut -d/ -f4 || echo "main"); current_branch=$(git branch --show-current); recent_commits=$(git log --oneline --since="${ARGUMENTS:-2} days ago" | wc -l); echo "📁 $repo_name | Branch: $current_branch → $default_branch | Activity: $recent_commits commits"; cd /Users/will/repos/jemena; done`

## 🎯 Active Repository Filter
!`cd /Users/will/repos/jemena && echo "🔥 Repositories with activity in last ${ARGUMENTS:-2} days:" && for repo_git in $(find . -name ".git" -type d -not -path "*/\.terraform/*"); do repo_dir=$(dirname "$repo_git"); repo_name=$(basename "$repo_dir"); cd "$repo_dir"; commits=$(git log --oneline --since="${ARGUMENTS:-2} days ago" | wc -l); if [ "$commits" -gt 0 ]; then echo "   ✨ $repo_name: $commits commits"; fi; cd /Users/will/repos/jemena; done`

## 🧠 Your Ultra Think Mission

I need you to perform **advanced cross-repository analysis** of changes in the last ${ARGUMENTS:-2} days across Jemena infrastructure.

### 🎛️ **Smart Repository Operations**

**CRITICAL**: Before analyzing any repository, you MUST:

1. **🔄 Smart Branch Switching**: 
   - For `databricks-app-code-digital-analytics`: Switch to `dev` branch (not main)
   - For all other repos: Use `main` branch
   - Check current branch vs. default and switch if needed

2. **⚡ Batch Pull Operations**: Pull latest changes from ALL repositories in parallel

3. **🎯 Activity-First Analysis**: Focus only on repositories with commits in the specified timeframe

### 🏗️ **Repository Intelligence Map**

```bash
# Special repository configurations
databricks-app-code-digital-analytics → dev branch (active development)
app-datahub-*-databricks-aws-infra → main branch (production infrastructure)  
databricks-workspaces → main branch (workspace management)
databricks-unity-catalog → main branch (catalog management)
core-network-* → main branch (network infrastructure)
```

### 📊 **Enhanced Analysis Framework**

#### 1. **Cross-Repository Pattern Detection**
   - **Infrastructure → Application Flow**: AWS infra changes feeding into Databricks configs
   - **Authentication Cascades**: OAuth/API changes across multiple services
   - **Version Dependencies**: Terraform provider updates affecting multiple repos

#### 2. **Advanced Change Classification**
   - 🔴 **CRITICAL**: Production config, breaking changes, security updates
   - 🟡 **IMPORTANT**: New features, schema changes, integration updates  
   - 🟢 **MINOR**: Documentation, formatting, small fixes, comments
   - 🚨 **HOTFIX**: Emergency patches, urgent bug fixes
   - 🔧 **MAINTENANCE**: Dependency updates, refactoring, cleanup

#### 3. **Smart Impact Scoring**
   ```
   Score = (Files Changed × 2) + (Lines Changed ÷ 10) + (Criticality Multiplier)
   Criticality Multipliers: Production=3, Dev=2, Test=1, Docs=0.5
   ```

#### 4. **Dependency Relationship Analysis**
   - **AWS → Databricks**: Infrastructure changes enabling platform changes
   - **Unity Catalog → Workspaces**: Schema/permission changes affecting workspace configs
   - **Secrets → Multiple Repos**: Authentication changes cascading across services

#### 5. **Visual Code Intelligence**
   - **Before/After Diffs**: Focus on 3-5 most impactful lines
   - **File Path Context**: Include module/folder structure for better understanding
   - **Change Motivation**: Infer WHY from commit messages + code patterns

### 🎯 **Ultra Think Deep Analysis Requirements**

For each active repository, analyze:

1. **📈 Activity Metrics**: Commits, authors, files changed, line delta
2. **🧬 Change DNA**: What type of changes (config, code, schema, docs)
3. **🔗 Cross-Repo Links**: How changes connect to other repositories
4. **⚡ Urgency Indicators**: Commit timing, message tone, file criticality
5. **🎪 Story Arc**: The narrative behind the changes

### 🚀 **Execution Protocol**

1. **Discover & Filter**: Find repos → Check activity → Focus on active ones
2. **Smart Sync**: Switch to correct branches → Pull latest changes
3. **Parallel Analysis**: Analyze all active repos simultaneously 
4. **Pattern Recognition**: Identify cross-repo relationships and themes
5. **Executive Summary**: Synthesize findings into actionable insights

### 🎨 **Enhanced Output Format**

```markdown
## 📊 ACTIVITY HEATMAP
🔥🔥🔥 repo-name (12 commits) - Major changes
🔥🔥   repo-name (5 commits)  - Moderate activity  
🔥     repo-name (2 commits)  - Light activity

## 🎯 CROSS-REPO STORY
**Theme**: OAuth Authentication Overhaul
**Affected**: app-datahub-prod + databricks-workspaces + unity-catalog
**Impact**: 🔴 Critical - Production authentication flow
```

### 🔮 **Extended Thinking Triggers**

Ultra think about:
- **📈 Trend Analysis**: Are we seeing more infrastructure or application changes?
- **🧬 Change Patterns**: Do commits suggest planned work or reactive fixes?
- **⚡ Velocity Insights**: Is development accelerating or stabilizing?
- **🔗 System Architecture**: How do these changes reflect system evolution?
- **🎯 Strategic Alignment**: Do changes align with Databricks migration goals?
- **⚠️ Risk Detection**: Any patterns suggesting potential issues?

## 🚀 Begin Advanced Analysis

Execute smart repository discovery, branch switching, and comprehensive cross-repo analysis now.