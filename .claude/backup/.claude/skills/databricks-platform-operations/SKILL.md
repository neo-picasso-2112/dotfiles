---
name: databricks-platform-operations
description: Comprehensive operational guidance for Jemena's Databricks platform following 5-layer architecture (AWS Resources → Unity Catalog → Workspaces → Data Products → Governance Apps). Covers complete runbooks for adding workspaces, onboarding business units, modifying shared modules safely, terraform remote state patterns, GitLab HTTP backend, module vs stack decisions, Unity Catalog design (centralized metastore, catalog-per-BU-per-environment), 3-dimensional RBAC (functional×classification×compliance), metastore binding constraints (permanent, cannot rebind), deployment order WHY (immutable dependencies), state file coupling, blast radius calculations, and troubleshooting permission denied errors. Use when working with terraform, databricks-unity-catalog repo, databricks-workspaces repo, app-datahub-aws-infra repos, adding new workspaces or BUs, RBAC issues, catalog/schema operations, or state file management.
---

# Databricks Platform Operations Expert

## Purpose

Provide **complete operational runbooks** and **terraform patterns** for working in Jemena's multi-account, shared-VPC, 5-layer Databricks platform architecture.

This skill encodes:
- **5-layer deployment order** (immutable, dependency-driven)
- **Operational runbooks** (adding workspaces, onboarding BUs, modifying shared modules)
- **Terraform patterns** (remote state, module vs stack, semantic versioning)
- **Unity Catalog design** (WHY centralized metastore, WHY catalog-per-BU-per-environment)
- **3-dimensional RBAC** (functional × classification × compliance groups)
- **Blast radius constraints** (what breaks if you rename/delete resources)
- **Troubleshooting workflows** (permission denied, catalog not visible, S3 access errors)

---

## When to Use This Skill

**Automatically activate when:**
- Working in databricks-unity-catalog, databricks-workspaces, or app-datahub-aws-infra repos
- Mentions of "add workspace", "new BU", "terraform state", "module vs stack"
- RBAC or permission denied errors
- Questions about metastore, catalogs, schemas, or Unity Catalog
- Terraform apply failures or state file issues

**Explicitly use when:**
- User asks "how do I add a new workspace?"
- User asks "how do I onboard a new business unit?"
- User encounters "Permission Denied" accessing catalogs/schemas
- User asks about terraform patterns or remote state
- User questions deployment order or dependencies
- User wants to modify shared modules

---

## Critical Architecture: 5-Layer Deployment Order

### The Immutable Order (NEVER Violate)

```
Layer 1: AWS Cloud Resources (Foundation)
  ├─ Repos: core-network-databricks-vpc-components
  │         app-datahub-{nonprod|prod}-databricks-aws-infra
  ├─ Outputs: S3 bucket ARNs, IAM role ARNs, KMS key ARNs (referenced from core-security 484357440923), security group IDs
  └─ Dependencies: KMS keys provisioned in core-security account (request from Platform Team)
         ↓
Layer 2: Databricks Account Resources (Unity Catalog)
  ├─ Repo: databricks-unity-catalog
  ├─ Consumes: S3 ARNs, IAM roles, KMS key ARNs from Layer 1
  ├─ Outputs: Metastore ID, catalog IDs, storage credentials, RBAC group IDs
  └─ CRITICAL: Metastore binding is PERMANENT
         ↓
Layer 3: Databricks Workspace Resources
  ├─ Repo: databricks-workspaces
  ├─ Consumes: Catalog IDs, metastore config, S3 buckets, IAM instance profiles
  ├─ Outputs: Workspace IDs, cluster policies, schema definitions
  └─ Pattern: Split into -infra (workspace creation) and -resources (schemas/clusters)
         ↓
Layer 4: Data Products (Application Code)
  ├─ Repos: databricks-app-code-digital-analytics, databricks-app-code-nri
  ├─ Consumes: Workspace configs, catalog schemas, cluster policies
  └─ Deployment: Databricks Asset Bundles (DABs)
         ↓
Layer 5: Governance Applications
  ├─ Repos: datamesh-manager-prod, network-model-ewb-prod
  └─ Infrastructure: ECS Fargate + RDS + cross-account DNS
```

### WHY Deployment Order is Immutable

| Violation | Impact | Example Failure |
|-----------|--------|-----------------|
| Deploy Layer 2 before Layer 1 | Unity Catalog creation fails | "S3 bucket not found: app-datahub-prod-s3-acc-metastore" |
| Deploy Layer 3 before Layer 2 | Workspace binding fails | "Metastore ID not found - cannot bind workspace" |
| Rename S3 bucket in Layer 1 | **BREAKS ALL WORKSPACES** | Metastore backend path hardcoded - requires full platform rebuild |
| Change IAM role ARN in Layer 1 | Clusters fail to start | "AssumeRole failed: invalid external ID" |
| Modify catalog name in Layer 2 | Data product pipelines break | "Catalog 'digital_lab' not found" |

**Recovery Pattern:** If upstream state corrupted, downstream repos CANNOT plan/apply until state restored.

---

## Unity Catalog Design Philosophy (WHY)

### WHY Centralized Metastore?

**Single Prod Metastore for ALL Data Product Teams Across ALL BUs**

**Benefits:**
- Single source of truth for all workspaces across all BUs
- Enables cross-BU data sharing and centralized audit logs
- Avoids metastore-level complexity

**Critical Constraint:**
```
METASTORE BINDING IS PERMANENT
Once a workspace binds to a metastore, it CANNOT be rebound without destroying the workspace.
Renaming app-datahub-{env}-s3-acc-metastore bucket breaks ALL workspace bindings across ALL BUs.
```

### WHY Stage Distinction at Catalog Level (NOT Metastore)?

**Pattern:** `{bu}_{environment}_catalog`

**Examples:**
- `digital_lab_catalog` (Digital BU, development)
- `digital_field_catalog` (Digital BU, production)
- `elec_network_lab_catalog` (Electricity Network BU, development)
- `elec_network_field_catalog` (Electricity Network BU, production)

**Benefits:**
- **Blast Radius Isolation**: Changes to `digital_lab` don't impact `digital_field` or `elec_network_field`
- **Cost Attribution**: S3 bucket tagging enables per-BU-per-environment cost tracking
- **Granular Lab→Field Promotion**: Allows controlled promotion without metastore-level complexity
- **Cross-BU Data Sharing**: Catalogs can be selectively bound to workspaces across BUs with read-only grants

### WHY Separate Nonprod Metastore?

**Platform Team ONLY** (not for data product teams):
- **Purpose**: Platform-level infrastructure changes and feature development isolated from production data
- **Access**: Data product teams do NOT have access to this nonprod metastore
- **Account**: Different Databricks account (851725449831 nonprod)

---

## 3-Dimensional RBAC Model

### The Three Dimensions

**Access = Functional Group ∩ Classification Group ∩ Compliance Group**

**Dimension 1: Functional Group (WHAT THEY DO)**
- Controls which environments (lab vs field) and what actions (read/write/admin)
- Examples: `APP-DataHubDigital-Data-Engineer`, `APP-DataHubDigital-Data-Analyst`

**Dimension 2: Classification Group (DATA SENSITIVITY)**
- Controls what data the individual can see based on sensitivity classification
- Levels: Public, Restricted (Internal), Confidential, Sensitive
- Examples: `APP-DataHubDigital-Internal`, `APP-DataHubDigital-Confidential`

**Dimension 3: Compliance Group (REGULATORY REQUIREMENTS)**
- Controls access to data with special legal requirements
- Types: SOI (Sensitive Operational Information), PII (Personally Identifiable Information)
- Examples: `APP-DataHub-SOI`, `APP-DataHub-PII`

**Group Naming Convention:**
```
Functional: APP-DataHub{BU}-Data-{Persona}
Classification: APP-DataHub{BU}-{Classification}
Compliance: APP-DataHub-{Compliance}  (org-wide, no BU prefix)
```

### Access Group Pattern (Databricks-Native)

**Pattern:** `{bu}_{environment}_{resource}_{permission}_ag`

**Examples:**
- `digital_lab_ctlg_ro_ag` (catalog read-only)
- `digital_lab_ctlg_rw_ag` (catalog read-write)
- `digital_lab_wks_viewer_ag` (workspace viewer)
- `digital_lab_wks_CI_SP` (CI/CD service principal)

**CRITICAL RULE:**
```
Users are NEVER assigned to Access Groups directly.
Only Service Principals may be assigned to Access Groups directly.
Permissions inherited by Functional Groups when assigned as members of Access Groups.
```

---

## Quick Start: Adding New Workspace

**Time:** 20-30 minutes across 3 layers
**See:** `references/complete-runbook-new-workspace.md` for detailed step-by-step instructions

### High-Level Procedure

1. **Layer 1 (AWS Resources)**: Add workspace cloud resources module in `app-datahub-{env}-databricks-aws-infra`
   - Define workspace name + buckets in locals
   - Call `workspace-cloud-resources` module
   - Add outputs (bucket ARN, IAM role, security groups)

2. **Layer 2 (Unity Catalog)**: Register workspace in `databricks-unity-catalog/stacks/<bu>-bu`
   - Update workspace config with subnets (from core-network team)
   - Call `managed-workspace` module with remote state outputs
   - **CRITICAL**: Record workspace URL from pipeline output

3. **Layer 3 (Workspace Resources)**: Configure workspace in `databricks-workspaces/stacks/<bu>-bu`
   - Define catalog storage mapper (medallion architecture)
   - Call `medallion-schemas` module
   - Apply enhanced grants (RBAC)

4. **Init Scripts (MANDATORY)**: Configure cluster init scripts
   - **CA certificates**: SSL inspection requires Jemena root CA
   - **DNS config**: BEPL endpoint resolution
   - **Metastore connection**: In-memory metastore config
   - **Location**: `/Volumes/{catalog}/global/scripts/`
   - **Without these**: Clusters start but **fail to connect to RDS metastore**

### Validation Checklist

- [ ] AWS resources deployed (S3, IAM, SGs, KMS keys)
- [ ] Workspace created and bound to metastore (PERMANENT binding)
- [ ] Workspace accessible via SSO
- [ ] Catalogs visible, medallion schemas created
- [ ] Init scripts volume path allowed in metastore
- [ ] RDS metastore firewall whitelist includes workspace subnets
- [ ] DNS resolves to FEPL private IPs (not public)

**Full Runbook:** `references/complete-runbook-new-workspace.md`

---

## Terraform Patterns Quick Reference

**See:** `references/terraform-patterns-library.md` for complete examples

### Pattern 1: Remote State Consumption (DRY Principle)

**Use Case:** Pass outputs from Layer 1 (AWS) → Layer 2 (UC) → Layer 3 (Workspaces)

**Key Points:**
- Define `data "terraform_remote_state"` in `dependencies.tf` or `upstream_stacks.tf`
- Consume outputs in locals: `data.terraform_remote_state.<name>.outputs.<output_key>`
- Use GitLab HTTP backend with project ID + state name
- **WHY**: DRY principle, prevents drift, provides audit trail via MRs

**Example:** Layer 2 consuming Layer 1 outputs
```hcl
data "terraform_remote_state" "nonprod_aws_infra" {
  backend = "http"
  config = {
    address = "https://gitlab.jemena.com.au/api/v4/projects/12345/terraform/state/nonprod-aws-infra"
  }
}

locals {
  lab_workspace_root_bucket = data.terraform_remote_state.nonprod_aws_infra.outputs.digital_bu_lab_wks_cloud_resources["workspace_root_bucket_name"]
}
```

### Pattern 2: Module vs Stack Decision

**Decision Tree:**
- **Module**: Reusable across multiple BUs (rbac, medallion-schemas, cluster-policy)
- **Stack**: BU-specific instantiation with one state file (digital-bu, corporate-bu)
- **Inline**: One-off resource in existing stack (specific security group rule)

**Key Rule:** Each stack directory = one terraform state file

### Pattern 3: Semantic Versioning for Shared Modules

**When:** Breaking change requires coordinated migration

**Steps:**
1. Tag current stable version BEFORE breaking change
2. Make breaking change to module
3. Tag new version with BREAKING label
4. Update ONE pilot BU (test first)
5. Migrate other BUs with approval

**Full examples:** `references/terraform-patterns-library.md`

---

## Troubleshooting Decision Trees

### Permission Denied: User Can't Access Catalog

```
User reports: "I can't access table X in catalog Y"
         │
         ▼
    Step 1: Verify Workspace Binding
    Does workspace have catalog bound?
    Run: SHOW CATALOGS; (should see catalog Y)
         │
    ┌────┴────┐
   YES       NO
    │         └─▶ Bind catalog to workspace in UC stack
    │
    ▼
    Step 2: Verify Functional Group Membership
    Is user member of correct functional group?
    Check Entra: APP-DataHub{BU}-Data-{Persona}
         │
    ┌────┴────┐
   YES       NO
    │         └─▶ Request group addition via IT Portal
    │
    ▼
    Step 3: Verify Classification Group Membership
    Is user member of required classification group?
    Check Entra: APP-DataHub{BU}-{Classification}
    Match against table's classification level
         │
    ┌────┴────┐
   YES       NO
    │         └─▶ Request elevated clearance (requires approval)
    │
    ▼
    Step 4: Verify Compliance Group (if SOI/PII data)
    Does table contain SOI or PII data?
    Check Entra: APP-DataHub-SOI, APP-DataHub-PII
         │
    ┌────┴────┐
   YES       NO
    │         └─▶ Verify UC grants directly
    │
    ▼
    Step 5: Verify UC Grants
    Run: SHOW GRANTS ON TABLE {catalog}.{schema}.{table};
    Verify access group has SELECT grant
    Verify functional group is parent of access group
         │
         ▼
    If all checks pass → Escalate to Platform Team
```

### S3 Access Denied When Querying Tables

```
Error: "Access Denied: s3://app-datahub-{env}-s3-{bu}-{stage}-{layer}/"
         │
         ▼
    Step 1: Verify IAM Role Trust Policy
    Navigate: AWS Console → IAM → Roles
    Search: {bu}-{stage}-ctlg-uc-data-access
    Verify: Trust policy allows Databricks account (414351767826)
    Verify: External ID matches Databricks account ID
         │
         ▼
    Step 2: Verify IAM Role S3 Permissions
    Check: Role has s3:GetObject, s3:PutObject on bucket
    Example: arn:aws:s3:::app-datahub-nonprod-s3-digital-*/*
         │
         ▼
    Step 3: Verify Storage Credential in Unity Catalog
    Navigate: Workspace UI → Catalog → {bu}_{stage}_catalog → Details
    Verify: Storage Credential ARN matches IAM role ARN
         │
         ▼
    Step 4: Verify KMS Key Policy (if encrypted)
    Check: KMS key policy allows IAM role to decrypt
    Action: kms:Decrypt, kms:Encrypt, kms:GenerateDataKey
         │
         ▼
    If all checks pass → Test query again
```

---

## Blast Radius Reference

### CATASTROPHIC (Requires All BU Approval)

| Change | Impact | Recovery |
|--------|--------|----------|
| Rename metastore S3 bucket | ALL workspaces break across ALL BUs | Metastore recreation + rebind all workspaces (destructive) |
| Delete metastore | ALL catalogs inaccessible | No recovery - must recreate from backups |
| Change Databricks account | ALL workspaces orphaned | No recovery - full platform rebuild |

### HIGH (Requires BU Approval)

| Change | Impact | Recovery |
|--------|--------|----------|
| Rename catalog | All schemas/tables orphaned | Catalog recreation + schema/table migration |
| Delete catalog | All data inaccessible | Recovery from S3 backups |
| Change storage credential | Catalog becomes unreadable | Recreate storage credential, rebind catalog |

### MEDIUM (Requires Platform Team Review)

| Change | Impact | Recovery |
|--------|--------|----------|
| Modify shared module | Multiple BUs affected | Rollback to previous version, coordinated migration |
| Delete RBAC group | All users in group lose permissions | Recreate group + reassign users |
| Rename S3 bucket (catalog) | External locations break | Update all external locations, terraform apply |

### LOW (Can Proceed with Testing)

| Change | Impact | Recovery |
|--------|--------|----------|
| Modify workspace config | Single workspace affected | Terraform apply to revert |
| Update cluster policy | Clusters using policy affected | Update policy, restart clusters |
| Add/remove schema | Single catalog affected | Easy to recreate |

---

## Quick Reference: Repository → Resource Mapping

| Resource Type | Repository | Layer |
|---------------|------------|-------|
| **S3 Buckets** | app-datahub-{env}-databricks-aws-infra | 1 |
| **IAM Roles** | app-datahub-{env}-databricks-aws-infra | 1 |
| **KMS Keys** | core-security (484357440923) - Referenced in app-datahub-{env}-databricks-aws-infra | 0 (Prerequisite) |
| **Security Groups (workspace)** | app-datahub-{env}-databricks-aws-infra | 1 |
| **Security Groups (Private Link)** | core-network-databricks-vpc-components | 1 |
| **VPC Endpoints (Private Link)** | core-network-databricks-vpc-components | 1 |
| **Route 53 PHZs** | core-network-databricks-workspaces-phz | 1 |
| **Metastore** | databricks-unity-catalog/stacks/org | 2 (MANUAL DEPLOY ONLY) |
| **Catalogs** | databricks-unity-catalog/stacks/{bu}-bu | 2 |
| **Storage Credentials** | databricks-unity-catalog/stacks/{bu}-bu | 2 |
| **RBAC Groups** | databricks-unity-catalog/stacks/{bu}-bu | 2 |
| **Workspaces** | databricks-unity-catalog/stacks/{bu}-bu | 2 |
| **Schemas** | databricks-workspaces/stacks/{bu}-{env}-workspace-resources | 3 |
| **Cluster Policies** | databricks-workspaces/stacks/{bu}-{env}-workspace-resources | 3 |
| **SQL Warehouses** | databricks-workspaces/stacks/{bu}-{env}-workspace-resources | 3 |

---

## For More Details

See reference files in `references/` folder:
- `FNDHAAP-OPERATIONAL-GUIDE.md` - **CRITICAL**: Disaster recovery, adding new BU (7-phase timeline), git workflows, monitoring checklists
- `complete-runbook-new-workspace.md` - Step-by-step workspace deployment procedure
- `terraform-patterns-library.md` - Comprehensive terraform pattern examples

**Cross-skill reference:**
- **Centralized KMS Pattern**: See `jemena-shared-vpc-navigator/references/centralized-kms-pattern.md` - ALL KMS keys provisioned in core-security account (484357440923)

See original PDFs:
- `references/Databricks-Platform-Infrastructure-Deployment-Operations-Guide.pdf` - Complete operational procedures
- `references/data-platform-repository-architecture.pdf` - Repository structure and dependencies
- `references/Jemena-Databricks-Unity-Catalog-Design.pdf` - UC architecture and design decisions
- `references/Jemena-Databricks-RBAC-Groups-Reference.pdf` - RBAC technical implementation

---

**Critical Contacts:**
- **Platform Team (Workspace/Terraform Issues):** Digital Analytics Team via #datahub-platform Slack
- **Platform Lead (Architecture Decisions):** @Sampath Jagannathan
- **DevOps Lead (CI/CD/State Files):** @Jay Jiang
- **Core-Network Team (VPC/Subnets):** David Hunter
- **Data Governance (RBAC/Classification):** @Harika Kareddy

**Emergency Escalation:**
- **Production workspace outage:** Immediate escalation to Platform Lead + On-call Engineer
- **Terraform state corruption:** Immediate escalation to DevOps Lead + Platform Lead (CRITICAL)
- **Metastore issues:** Immediate escalation to Platform Lead + All BU Leads (CATASTROPHIC)
