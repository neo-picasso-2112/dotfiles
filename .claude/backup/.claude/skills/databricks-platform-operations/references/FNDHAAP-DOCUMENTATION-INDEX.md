# FNDHAAP Architecture Documentation Index

**Created**: 2025-11-16
**Source**: 4 FNDHAAP design PDFs extracted and analyzed
**Purpose**: Provide Claude Code with complete architectural context for understanding Databricks platform on AWS

---

## Quick Navigation

### For Understanding Overall Architecture
- **Start here**: `/Users/williamnguyen/repos/FNDHAAP-ARCHITECTURE-SUMMARY.md`
  - Covers: WHY decisions were made, HOW components connect, WHAT constraints exist, WHEN to apply patterns
  - Sections: Critical decisions, network topology, security, repository structure, CI/CD rules
  - Best for: Design reviews, architecture questions, decision-making context

### For Visual Understanding
- **Next**: `/Users/williamnguyen/repos/FNDHAAP-VISUAL-ARCHITECTURE.md`
  - Contains: ASCII diagrams, network flow diagrams, topology maps, terraform dependency graphs
  - Sections: E2E topology, connectivity flows, subnet layouts, CI/CD pipeline, DNS layers, issues
  - Best for: Understanding system interactions, debugging network issues, capacity planning

### For Day-to-Day Operations
- **Reference**: `/Users/williamnguyen/repos/FNDHAAP-OPERATIONAL-GUIDE.md`
  - Contains: Checklists, troubleshooting flowcharts, common tasks, quick reference
  - Sections: Adding workspaces, debugging access, onboarding BUs, terraform patterns, git workflow
  - Best for: Implementing changes, troubleshooting, operational decisions

---

## Document Coverage Matrix

| Topic | Summary | Visual | Operational |
|-------|---------|--------|-------------|
| **Infrastructure Design** | ✓ (Section 1) | ✓ (Section 1,2,3) | ✗ |
| **Network Topology** | ✓ (Section 2) | ✓ (Section 3,4) | ✓ (Troubleshooting) |
| **Private Link Implementation** | ✓ (Section 2.1) | ✓ (Section 2) | ✓ (Section 6) |
| **Security Configuration** | ✓ (Section 3) | ✓ (Section 7) | ✓ (SSL, DNS) |
| **Repository Structure** | ✓ (Section 4) | ✓ (Section 5) | ✓ (Section 6) |
| **Terraform Patterns** | ✓ (Section 4) | ✓ (Section 5) | ✓ (Section 6) |
| **CI/CD Workflow** | ✓ (Section 5) | ✓ (Section 6) | ✓ (Section 7) |
| **Adding Workspaces** | — | — | ✓ (Section 1) |
| **Adding Business Units** | ✗ | ✗ | ✓ (Section 3) |
| **Troubleshooting** | ✓ (Section 6) | ✓ (Section 8) | ✓ (Section 2, 10) |
| **Disaster Recovery** | ✗ | ✗ | ✓ (Section 9) |
| **Architecture Decisions** | ✓ (Section 1,8) | ✓ (Section 10) | ✓ (Section 11) |

---

## Key Architectural Insights

### The Three Competing Principles

The platform design balances:
1. **Isolation** - Prevent cross-BU collisions
2. **Reusability** - DRY principle, use modules
3. **Complexity** - Minimize operational overhead

**Decision**: Minimize repos, accept multiple statefiles, use semantic versioning on modules.

### Multi-Tenancy Model

- **By Business Unit** (not by AWS account)
- **Lab → Field promotion** (dev → prod workflow)
- **2 workspaces per BU** × **2 environments** (nonprod/prod)
- **3 availability zones per workspace** (high availability)

**Current**: 3 BUs (Electricity, Gas, Digital) + future expansion to 5 total

### Dual Private Link Architecture

| Component | Type | Purpose | Endpoint |
|-----------|------|---------|----------|
| Backend | Data Plane | Cluster ↔ Control Plane | Nonprod VPC + Prod VPC |
| Frontend | Control Plane | User ↔ Workspace UI | Prod VPC only (for both envs) |

**Design Rationale**: Follows Databricks reference architecture, enables security layer separation.

### Shared VPC Design

- **Not** account isolation per workspace
- **Rather** subnet isolation within Jemena's shared VPCs
- **Rationale**: Reduce operational overhead, leverage existing Direct Connect

**VPC Layout**:
- Nonprod: 10.34.0.0/16 (21 subnets for current 3 BUs)
- Prod: 10.32.0.0/16 (21 subnets for current 3 BUs)

---

## Common Scenarios & Where to Find Answers

| Scenario | Look in | Section |
|----------|---------|---------|
| "Why did they choose isolation-by-BU?" | Summary | 1.1 |
| "How do users access workspaces?" | Visual | 2 |
| "What's the DNS resolution process?" | Visual | 7 |
| "Show me the terraform structure" | Visual | 5 |
| "I need to add a new workspace" | Operational | 1 |
| "User can't access workspace - debug" | Operational | 2 |
| "Onboard a new business unit" | Operational | 3 |
| "Modify a shared RBAC module" | Operational | 4 |
| "Frontend Private Link is down" | Operational | 5 |
| "What's a known DNS issue?" | Summary or Visual | 3.4 or 8 |
| "How do I reference AWS resources in terraform?" | Operational | 6 |
| "What's the git workflow?" | Operational | 7 |
| "Who do I contact for X?" | Summary or Operational | 7 or 8 |

---

## Critical Knowledge for Claude Code

### 1. Architectural Decisions (Section 1 - Summary)

**Key Facts**:
- Isolation by Business Unit, not account
- 2 workspaces per BU (lab for dev, field for prod)
- Shared VPCs in nonprod and prod accounts only
- Dual private links (backend for data, frontend for UI)
- Semantic versioning on shared modules

**Why Matter**:
- Explains why repos have multiple state files
- Explains why infrastructure changes can affect multiple teams
- Explains DNS complexity and workarounds

### 2. Network Topology (Sections 2 & 3 - Both Docs)

**Key Facts**:
- Frontend Private Link used by ALL workspaces (prod VPC only)
- Backend Private Link per environment
- Route 53 PHZs for DNS
- Zscaler and on-prem DNS for routing
- Direct Connect for on-premises connectivity

**Why Matter**:
- Explains why new workspaces need PHZ entries
- Explains why there's DNS flipping issues (known, mitigated)
- Explains why all traffic goes through Zscaler

### 3. Repository Structure (Section 4 - Summary)

**Key Facts**:
```
5 core repos:
├─ core-network-databricks-vpc-components (Private Link, SGs)
├─ app-datahub-nonprod-databricks-aws-infra (S3, IAM)
├─ app-datahub-prod-databricks-aws-infra (S3, IAM)
├─ databricks-unity-catalog (RBAC, catalogs, schemas)
└─ databricks-workspaces (clusters, jobs, resources)

+ 1 supporting repo:
└─ core-network-databricks-workspaces-phz (Route 53 DNS)
```

**Why Matter**:
- Understand cross-repo dependencies
- Know which repo to modify for each type of change
- Understand state file isolation strategy

### 4. Terraform Pattern (Section 5 - Visual & 6 - Operational)

**Key Facts**:
- Each stack directory = one terraform state file
- Modules are reusable, stacks instantiate them
- Remote state data sources for cross-repo references
- Environment injection via `*.auto.tfvars`
- Semantic versioning on shared modules

**Why Matter**:
- Prevent accidental refactoring of multiple stacks
- Understand when to create new module vs. new stack
- Know how to reference AWS resources in Databricks repo

### 5. DNS Complexity (Section 3 & 8 - Both Docs)

**Key Facts**:
- 3 DNS layers: Zscaler → Route 53 → Private Hosted Zones
- 3 known workarounds currently implemented
- All due to technical constraints (endpoint DNS conflict, AD forwarder flipping)
- NOT due to design flaws, but practical mitigations

**Why Matter**:
- Explains why DNS setup is non-trivial
- Know what workarounds exist and why
- Understand impact when debugging access issues

---

## Critical Constraints to Remember

### 1. Firewall Whitelist (CRITICAL)
- RDS metastore: `mdnrak3rme5y1c.c5f38tyb1fdu.ap-southeast2.rds.amazonaws.com:3306`
- Clusters can't function without this
- Contact: David Hunter

### 2. SSL Inspection (CRITICAL)
- All outbound traffic inspected
- Applications need root CA certificate
- Causes silent failures if not distributed

### 3. Private Access Only (SECURITY)
- Workspaces can't be accessed from public internet
- Users must be on corporate network or on-prem with VPN
- Error message: "Cannot access workspace from public network"

### 4. Security Group Rule Limits
- Jemena has limits on SG rules
- Workaround: Combine related subnets in single rule
- Monitor as platform grows

### 5. VPC Headroom
- Current: 2.3% per BU
- 5 BUs planned: ~12% total
- Remaining: ~88% for expansion
- Runway: Multiple years

---

## Where to Find Original Sources

All extracted from these source PDFs (stored in `/Users/williamnguyen/repos/`):

1. **FNDHAAP-Infrastructure Design-161125-033744.pdf**
   - E2E architecture
   - AWS accounts and VPC design
   - Subnet allocations
   - Control plane & data plane connectivity
   - FAQ and discovery notes

2. **FNDHAAP-Databricks Private Link Implementation-161125-034022.pdf**
   - Backend private link details
   - Frontend private link design
   - ENI configurations
   - Implementation references (GitLab repo links)

3. **FNDHAAP-Databricks Workspaces with Front End Private Link-161125-034927.pdf**
   - DNS configuration (Route 53, Zscaler, on-prem)
   - Private hosted zones
   - 3 technical issues and workarounds
   - Workspace address list

4. **FNDHAAP-Git Repo Topology - Data Platform Repos-161125-034602.pdf**
   - Repository map and purposes
   - Isolation vs. reusability vs. complexity tradeoff
   - Module and stack structure
   - CI/CD rules and git workflow
   - Architecture decision rationale

---

## Document Reading Guide

### For Different Roles

**Infrastructure Engineer**
- Read: Summary Sections 2, 3, 4
- Read: Visual Sections 2, 3, 4, 5
- Use: Operational Sections 5, 8, 9

**Databricks Data Engineer**
- Read: Summary Sections 1.2, 1.3, 4.3, 4.4
- Read: Visual Sections 3, 4, 6
- Use: Operational Sections 1, 2, 6

**DevOps/CI-CD Engineer**
- Read: Summary Section 5
- Read: Visual Section 6
- Use: Operational Sections 7, 9

**New Team Member**
- Read: Summary Section 1 (overview)
- Read: Visual Sections 1, 2, 3, 5
- Read: Operational Sections 1, 3, 8 (contacts)
- Reference: This index document

**Security Review**
- Read: Summary Section 3
- Read: Visual Section 7, 8
- Use: Operational Section 2 (DNS issues)

---

## Key Contacts Reference

| Role | Name | Contact Point |
|------|------|---|
| AWS/Network | David Hunter | VPC, firewalls, Direct Connect |
| Databricks Architect | Sampath Jagannathan | Architecture decisions |
| Network/Infrastructure | Vishnu Devarajan | VPC configuration |
| Core Network | Neil Belford | Shared VPC, routing |
| Infrastructure Code | Wee Lih Lee, Nikilesh Chivukula | Terraform repos |

**See**: Summary Section 7 for full contact list

---

## Actionable Integration Checklist

When implementing new features or troubleshooting:

**Network Level**:
- [ ] Verify firewall whitelist for RDS
- [ ] Confirm SSL cert distribution
- [ ] Check Route 53 PHZ entries
- [ ] Validate Zscaler rules

**Terraform Level**:
- [ ] Identify correct repo for change
- [ ] Check if module exists or needs creation
- [ ] Plan semantic versioning if affecting shared modules
- [ ] Verify remote state dependencies

**Deployment Level**:
- [ ] Follow feature branch → MR → approval workflow
- [ ] Wait for pipeline success
- [ ] Test in nonprod before prod
- [ ] Document decision in architecture docs

**See**: Summary Section 9 for full checklist

---

## Document Version & Updates

| Document | Version | Last Updated | Scope |
|----------|---------|---|---|
| FNDHAAP-ARCHITECTURE-SUMMARY.md | 1.0 | 2025-11-16 | Full architecture |
| FNDHAAP-VISUAL-ARCHITECTURE.md | 1.0 | 2025-11-16 | Diagrams & flows |
| FNDHAAP-OPERATIONAL-GUIDE.md | 1.0 | 2025-11-16 | Quick reference |
| FNDHAAP-DOCUMENTATION-INDEX.md | 1.0 | 2025-11-16 | This document |

**How to Update**:
- Extract new information from source PDFs
- Add to appropriate summary section
- Update this index if new sections added
- Commit together with clear message: "Update architecture docs: [what changed]"

---

## Quick Links

**Repository Links** (mentioned in documents):
- Core Network VPC Components: `core-network-databricks-vpc-components`
- Nonprod AWS Infra: `app-datahub-nonprod-databricks-aws-infra`
- Prod AWS Infra: `app-datahub-prod-databricks-aws-infra`
- Unity Catalog: `databricks-unity-catalog`
- Workspaces: `databricks-workspaces`
- Route 53 PHZ: `core-network-databricks-workspaces-phz`

**External References**:
- Databricks PrivateLink: https://docs.databricks.com/en/security/network/private-link/
- AWS PrivateLink: https://docs.aws.amazon.com/vpc/latest/privatelink/
- Terraform Remote State: https://www.terraform.io/language/state/remote-state-data-sources

---

## How to Use These Documents in Claude Code

1. **For Architecture Questions**
   ```
   Question: "Why did they choose isolation-by-BU?"
   Answer: See FNDHAAP-ARCHITECTURE-SUMMARY.md Section 1.1
   ```

2. **For Visual Understanding**
   ```
   Question: "Show me how users access workspaces"
   Answer: See FNDHAAP-VISUAL-ARCHITECTURE.md Section 2
   ```

3. **For Implementation Tasks**
   ```
   Task: "Add a new workspace"
   Answer: See FNDHAAP-OPERATIONAL-GUIDE.md Section 1
   ```

4. **For Debugging**
   ```
   Problem: "User can't access workspace"
   Answer: See FNDHAAP-OPERATIONAL-GUIDE.md Section 2
   ```

5. **For Finding Information**
   ```
   Lost? Start here: FNDHAAP-DOCUMENTATION-INDEX.md
   Then use Document Coverage Matrix (above) to find specific info
   ```

---

## Summary

These three documents provide complete architectural context extracted from the official FNDHAAP design PDFs:

- **FNDHAAP-ARCHITECTURE-SUMMARY.md** - What, why, how, and when
- **FNDHAAP-VISUAL-ARCHITECTURE.md** - Diagrams and visual flows
- **FNDHAAP-OPERATIONAL-GUIDE.md** - Checklists and quick reference

**Total Coverage**: All critical architectural information, security requirements, design decisions, known issues, and operational procedures.

**Use This Index** to navigate quickly to what you need.

