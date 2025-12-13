# FNDHAAP Architecture Documentation Summary

## Executive Overview

This document synthesizes key architectural insights from the FNDHAAP (Future Networks Data Hub on AWS Platform) infrastructure design. The platform is a multi-tenant Databricks data platform deployed on Jemena's AWS infrastructure with strict isolation, security, and reusability requirements.

---

## 1. CRITICAL ARCHITECTURAL DECISIONS & PATTERNS

### 1.1 Multi-Tenancy & Business Unit Isolation Model

**Decision**: Isolation-by-business-unit (LOB) design rather than single workspace sets.

**Key Pattern**:
- 2 workspaces per Business Unit: `lab` (development) and `field` (production)
- 4 Business Units (Electricity, Gas, Digital, Corporate) + future expansion planned
- Separate Terraform state files per Business Unit to prevent cascading changes
- Each workspace gets isolated /24 subnets (3 AZs = 256 IPs × 3)

**Why This Matters**:
- Prevents cross-BU blast radius on infrastructure changes
- Allows BU teams autonomy while maintaining platform consistency
- Enables future growth without redesigning core topology

**Infrastructure Footprint**:
- Current: ~2.3% of shared VPC per BU
- Planned (5 BUs): ~12% of shared VPC total
- Subnet allocation designed for growth with headroom

**Critical Dependency**: Must coordinate with Jemena's core-network team for VPC provisioning and routing policies.

### 1.2 Shared VPC Design (Not Account Isolation)

**Decision**: Single shared VPC per environment with multiple workspaces, not separate AWS accounts per workspace.

**Key Pattern**:
- Nonprod workspaces: AWS account `app-datahub-nonprod` (851725449831)
- Prod workspaces: AWS account `app-datahub-prod` (339712836516)
- Both share VPCs with Jemena's core network infrastructure
- Private Link endpoints (backend & frontend) for secure cluster communication

**Why This Matters**:
- Reduces AWS account management overhead
- Enables efficient shared resource utilization (S3, RDS metastore)
- Leverages Jemena's existing network architecture rather than creating isolated silos

**Constraints**:
- Requires security group coordination across workspaces
- Network isolation enforced at subnet level, not account boundary
- DNS and routing configuration becomes critical (see DNS issues section)

### 1.3 Lab → Field Promotion Pipeline

**Decision**: Lab workspace for development/testing, Field workspace for production pipelines.

**Workflow**:
```
Data Product Team Work
  ↓
Lab Workspace (Dev/Testing)
  ↓
Validation & Testing
  ↓
Field Workspace (Auto-run production pipelines)
```

**Why This Matters**:
- Enables safe testing before production automation
- Clear promotion path with governance checkpoints
- Aligns with Databricks best practices for environment separation

**Note**: Previous naming confusion: "field" was previously called "prod" which caused miscommunication.

---

## 2. NETWORK TOPOLOGY & CONNECTIVITY PATTERNS

### 2.1 Dual Private Link Implementation

The platform uses TWO separate Private Link endpoints for different purposes:

#### Backend Private Link (Data Plane - Cluster ↔ Control Plane)
**Purpose**: Secure communication between Databricks clusters and control plane

**Implementation**:
- 2 ENIs (Elastic Network Interfaces) deployed per environment (nonprod/prod)
- One ENI for Secure Compute Cluster (SCC)
- One ENI for Rest API
- Registered in respective Databricks accounts
- Clusters use these ENIs for all control plane communication

**GitLab Source**: `core-network-databricks-vpc-components` repo
- File: `main-npd-vpc-resources.tf` (nonprod)
- Deployed in both nonprod and prod VPCs

**Critical Dependencies**:
- RDS metastore connectivity via private link: `mdnrak3rme5y1c.c5f38tyb1fdu.ap-southeast2.rds.amazonaws.com:3306`
- **MUST be whitelisted by Jemena firewall** in both environments
- Contact: David Hunter for firewall rule implementation

#### Frontend Private Link (User ↔ Workspace)
**Purpose**: Secure user access to workspace UI

**Implementation**:
- Single ENI deployed only in PROD VPC
- Used for both nonprod and prod workspace access
- Simplifies DNS configuration (single FEPL routing point)
- No separate nonprod FEPL (would require separate DNS rules and complexity)

**DNS Configuration Layers**:
1. **Route 53 Private Hosted Zones** - Alias A records → FEPL endpoint
2. **Zscaler** - Corporate laptop internet gateway, catches `*.cloud.databricks.com`
3. **On-Prem DNS** - Conditional forwarders on Active Directory domain controllers

**Network Flow Diagram**:
```
User on Jemena Corporate Network
  ↓
Laptop/Server
  ↓ (Zscaler intercepts *.cloud.databricks.com)
  ↓
Route 53 Inbound Endpoint (Conditional Forwarder)
  ↓
Route 53 Private Hosted Zone Lookup
  ↓ (Returns private IP)
  ↓
Frontend Private Link VPC Endpoint
  ↓
Databricks Workspace (Data Plane)
```

### 2.2 Subnet Topology

**Nonprod Subnets** (10.34.0.0/16):
- Tenant 1 (ElecNetwork BU): Workspaces 1-2 = 6 subnets (10.34.81-86/24)
- Tenant 2 (Digital BU): Workspaces 1-2 = 6 subnets (10.34.87-92/24)
- Tenant 3 (Corporate BU): Workspaces 1-2 = 6 subnets (10.34.98-103/24)

**Prod Subnets** (10.32.0.0/16):
- Same structure with 10.32.x.x CIDR blocks

**Subnet Pattern per Workspace**:
- 3 subnets (one per AZ) in /24 = 256 IPs each
- AZ1, AZ2, AZ3 for high availability
- Naming: `appdatahub-{env}privateaz{az}-{workspace_id}`

**Rationale**:
- /24 subnets provide isolation and allow future expansion
- 3 AZs ensure fault tolerance
- Smaller subnets prevent Databricks cluster IP exhaustion

### 2.3 Connectivity to On-Premises & Internet

**AWS Direct Connect**:
- Used for connectivity between AWS and Jemena on-premises data centers
- Routing between prod/nonprod networks managed separately
- Documentation: See Infrastructure Design document for routing details

**Outbound Internet Traffic**:
- All traffic subject to **SSL inspection** through firewalls
- **Requirement**: Root CA certificate must be added to any process making external calls
- Implication: CI/CD runners, Spark libraries downloading packages, etc. need cert injection

**Critical Configuration Point**: SSL inspection is a common integration blocker - applications may fail silently if they don't have proper certificates.

---

## 3. SECURITY CONFIGURATIONS & REQUIREMENTS

### 3.1 Firewall Whitelist Requirements

**Critical**: RDS Metastore connectivity is blocked by default

**Firewall Rule Needed**:
```
Source: Databricks Cluster ENIs
Destination: mdnrak3rme5y1c.c5f38tyb1fdu.ap-southeast2.rds.amazonaws.com
Port: 3306 (MySQL)
Required In: Nonprod AND Prod environments
Contact: David Hunter
```

**Status**: Must be completed before cluster provisioning.

### 3.2 Certificate Distribution

**Requirement**: Root CA certificate for SSL inspection

**Applied To**:
- Spark application dependencies
- Python package installations (pip)
- Any external API calls from notebooks/jobs

**Implementation Pattern**:
- Store certificate in Databricks workspace as secret
- Reference in cluster initialization scripts
- Apply to JVM and Python environments

### 3.3 Private Access Enforcement

**User Access Restriction**:
- Databricks workspaces configured for private access only
- Public internet access returns error
- All access must flow through private link

**Error When Accessing Publicly**:
```
Error: Cannot access workspace from public network
Reason: Private access configured - use private link only
```

### 3.4 DNS Security Workarounds & Known Issues

The platform implements 3 DNS workarounds due to technical constraints:

#### Issue 1: Active Directory Conditional Forwarder Flipping
**Problem**: DNS results flip between correct (private IP) and incorrect (public IP)
- Caused inconsistent workspace access for end users
- Investigation ongoing with Microsoft and Databricks

**Workaround**: Use wildcard `*.cloud.databricks.com` instead of specific `sydney.privatelink.cloud.databricks.com`
- All Databricks traffic goes through Route 53
- Solves flipping issue at cost of some routing optimization

#### Issue 2: Frontend/Backend Endpoint DNS Name Conflict
**Problem**: Both private link endpoints try to use `sydney.privatelink.cloud.databricks.com`
- Cannot create 2 VPC endpoints in same VPC with Private DNS enabled
- Backend endpoint created first (critical for clusters)

**Workaround Options Evaluated**:
1. ✓ **Selected**: Create frontend endpoint WITHOUT Private DNS names
2. Rejected: Create frontend endpoint in separate VPC (logistics overhead)

**Implementation**:
- Backend endpoint: Private DNS enabled (auto-resolves in VPC)
- Frontend endpoint: Private DNS disabled
- Private Hosted Zones created for each workspace address to direct traffic to frontend endpoint

#### Issue 3: Zscaler CNAME Resolution
**Problem**: Zscaler doesn't resolve CNAMEs properly when pointing to `sydney.privatelink.cloud.databricks.com`
- Configuration caught `sydney.privatelink.cloud.databricks.com` but requests via workspace address returned public IPs
- Caused public internet routing bypass

**Workaround**: Zscaler catches `*.cloud.databricks.com` (wildcard)
- All Databricks traffic routed through Zscaler tunnel
- Ensures corporate network security policy is applied

### 3.5 Private Hosted Zones (Route 53)

**List of Configured Workspaces**:

| Workspace Address | Workspace Name | Environment |
|-------------------|----------------|-------------|
| dbc-fecbb5ff7592.cloud.databricks.com | digital-field-workspace-nonprod | Nonprod |
| dbc-eaba2339eb1e.cloud.databricks.com | digital-lab-workspace-nonprod | Nonprod |
| dbc-94129c9d8f32.cloud.databricks.com | elec-network-field-workspace-nonprod | Nonprod |
| dbc-de6c0ca10e35.cloud.databricks.com | elec-network-lab-workspace-nonprod | Nonprod |
| https://jemena-digitalfield.cloud.databricks.com | digital-field-workspace-prod | Prod |
| https://jemena-digitallab.cloud.databricks.com | digital-lab-workspace-prod | Prod |
| https://jemena-elec-networkfield.cloud.databricks.com | elec-network-field-workspace-prod | Prod |
| https://jemena-elec-networklab.cloud.databricks.com | elec-network-lab-workspace-prod | Prod |

**Management**: Hosted in GitLab repo `core-network-databricks-workspaces-phz`
- Use this repo to add/remove workspace PHZs
- Each PHZ has alias A record pointing to frontend private link endpoint

---

## 4. REPOSITORY STRUCTURE & DEPENDENCIES

### 4.1 Design Principles: The Isolation vs. Reusability Tradeoff

**Competing Principles**:
1. **Isolation** - Prevent cross-BU collisions, changes don't affect other teams
2. **Reusability** - DRY principle, use modules for common patterns
3. **Complexity** - Minimize repos but accept multiple terraform state files

**Decision Made**:
- **Minimize repos** (fewer to manage operationally)
- **Accept one repo → multiple statefiles** (standard CI/CD pattern)
- **Use semantic versioning on shared modules** to maintain compatibility

### 4.2 Repository Map

#### AWS Infrastructure Repos

**Repository**: `core-network-databricks-vpc-components`
- **Purpose**: Shared network infrastructure
- **Components**: Private Link ENIs, Security Groups
- **Environments**: Both nonprod and prod
- **Key File**: `main-npd-vpc-resources.tf` (terraform config)
- **Manages**: Backend private link infrastructure
- **Note**: This is infrastructure-as-code (IaC) with terraform

**Repository**: `app-datahub-nonprod-databricks-aws-infra`
- **Purpose**: Nonprod AWS resources
- **Components**: S3 buckets, Instance Profiles, IAM Roles
- **Environment**: Nonprod only
- **Key Configuration**: IAM permissions for Databricks cluster access
- **Manages**: Data lake storage and access credentials

**Repository**: `app-datahub-prod-databricks-aws-infra`
- **Purpose**: Prod AWS resources
- **Components**: S3 buckets, Instance Profiles, IAM Roles
- **Environment**: Prod only
- **Key Configuration**: IAM permissions for Databricks cluster access
- **Manages**: Production data lake storage and access credentials

**Cross-Repo Dependency Pattern**:
- Databricks repos use terraform remote state data sources to fetch AWS resource ARNs
- Requires GitLab CI runner permissions configured

#### Databricks Infrastructure Repos

**Repository**: `databricks-unity-catalog`
- **Scope**: Account-level and workspace-agnostic resources
- **Components**:
  - Modules: `rbac`, `schemas`, `service-principals`
  - Stacks: `digital-bu`, `elec-network-bu`, `org`
- **Isolation Level**: Per Business Unit (BU)
- **Key Pattern**: RBAC hierarchy abstracted in modules, instantiated per BU in stacks
- **State Files**: One per BU (digital-bu/, elec-network-bu/)
- **Special Stack**: `org/` has no CI - manual deploy only (account-level config)

**Repository**: `databricks-workspaces`
- **Scope**: Workspace-level and cluster resources
- **Components**:
  - Modules: `cluster-policy`, `long-lived-clusters`, `managed-workspace`, `sql-warehouses`
  - Stacks: Named by workspace (e.g., `digital-lab-workspace-infra`)
- **Isolation Level**: Per workspace
- **Stack Naming Pattern**: `{bu}-{lab|field}-workspace-{infra|resources}`
  - `-infra`: Workspace and cluster infrastructure
  - `-resources`: Workspace-specific resources (schemas, tables, etc.)
- **State Files**: One per stack directory

### 4.3 Directory Structure Deep Dive

```
databricks-unity-catalog/
├── modules/                          # Reusable patterns
│   ├── rbac/                        # RBAC hierarchy for any BU
│   │   ├── main.tf                  # Variables: bu_name, user_mappings, etc.
│   │   └── outputs.tf               # Exports: catalog_names, group_ids, etc.
│   ├── schemas/                     # Schema provisioning module
│   │   └── main.tf                  # Variables: catalog, schema_name, owner, etc.
│   └── service-principals/          # Service principal provisioning
│       └── main.tf                  # For data pipeline identities
│
└── stacks/                          # Instantiations (1 statefile each)
    ├── digital-bu/                  # Digital BU - has CI/CD
    │   ├── catalogs.tf              # Calls catalog module
    │   ├── rbac.tf                  # Calls rbac module (Digital-specific config)
    │   └── schemas/                 # Schemas directory
    │       └── *.tf                 # Schema definitions
    │
    ├── elec-network-bu/             # ElecNetwork BU - has CI/CD
    │   ├── catalogs.tf
    │   ├── rbac.tf
    │   └── schemas/
    │
    └── org/                         # Organization-level - NO CI (manual only)
        └── metastore.tf             # Account-level metastore config

databricks-workspaces/
├── modules/                         # Reusable workspace patterns
│   ├── cluster-policy/              # Standardized cluster policies
│   ├── long-lived-clusters/         # Always-on cluster templates
│   ├── managed-workspace/           # Workspace provisioning
│   └── sql-warehouses/              # SQL warehouse templates
│
└── stacks/                          # One directory per workspace
    ├── digital-lab-workspace-infra/     # Creates workspace + clusters
    ├── digital-lab-workspace-resources/ # Creates workspace resources
    ├── digital-field-workspace-infra/
    ├── digital-field-workspace-resources/
    ├── elec-network-lab-workspace-infra/
    ├── elec-network-lab-workspace-resources/
    ├── elec-network-field-workspace-infra/
    └── elec-network-field-workspace-resources/
```

**Key Insight**: Each directory under `stacks/` has its own terraform statefile (`.tfstate`), enforcing BU/workspace isolation.

### 4.4 State File Isolation Strategy

**Pattern**:
```
Stack Directory                           → Terraform State File
digital-bu/                              → terraform.tfstate (Unity Catalog account-level)
elec-network-bu/                         → terraform.tfstate (Unity Catalog account-level)
digital-lab-workspace-infra/             → terraform.tfstate (Workspace infra)
digital-lab-workspace-resources/         → terraform.tfstate (Workspace resources)
```

**Why**:
- Prevents Terraform from trying to recreate all resources if one stack changes
- Allows different BU teams to deploy independently
- Enables semantic versioning on shared modules while maintaining backwards compatibility

**Dependency Management**:
- Modules define reusable patterns but create nothing
- Stacks call modules via `source = ../modules/rbac` with inputs
- Cross-repo dependencies via terraform remote state data sources
- Example: Databricks repo fetches S3 ARNs from AWS repo's remote state

### 4.5 Environment Injection

**Mechanism**: `.auto.tfvars` files in stack directories

**Example**:
```hcl
# digital-bu/prod.auto.tfvars
environment = "prod"
workspace_url = "https://jemena-digitalfield.cloud.databricks.com"
```

**CI/CD Pattern**:
- Branch naming determines environment
- Pipeline dynamically selects appropriate `.auto.tfvars` file
- Values injected before terraform apply

---

## 5. CI/CD & DEPLOYMENT RULES

### 5.1 Git Workflow Policies

**Main Branch Protection**:
- ✗ Direct push to `main` is **DENIED**
- Only modification via Merge Request (MR)
- Minimum 1 approval required before merge
- Pipeline must succeed before merge eligible

**Approval Handling**:
- Subsequent commits on MR revoke previous approvals
- Forces re-review after changes
- Prevents stale approvals

**Implication for Contributors**:
- All changes must go through feature branches → MR → approval → merge
- No emergency bypass for main branch
- Encourages code review before production deployment

### 5.2 CI/CD Considerations

**GitLab Remote State Access**:
- CI runners need permissions to read remote terraform states
- Used when Databricks repos consume AWS repo outputs (S3 ARNs, IAM roles)
- Requires GitLab CI token configuration with appropriate scope

**Separate CI for Each Stack**:
- Each stack directory can have independent CI pipeline
- Prevents cascading failures across workspaces/BUs

---

## 6. CRITICAL CONSTRAINTS & GOTCHAS

### 6.1 Must-Know Infrastructure Requirements

| Requirement | Status | Owner | Impact |
|-------------|--------|-------|--------|
| Firewall whitelist for RDS | **CRITICAL** | David Hunter | Clusters won't connect to metastore without this |
| SSL cert distribution | **CRITICAL** | Databricks team | External calls fail silently without cert |
| Route 53 Private Hosted Zones | **REQUIRED** | Team | Workspace DNS won't resolve to private link |
| Zscaler configuration | **REQUIRED** | Security team | Users get public IP routes, bypassing security |
| Frontend Private Link deployment | **REQUIRED** | Networking team | User workspace access fails without FEPL |

### 6.2 Known Operational Issues & Workarounds

1. **DNS Resolution Flipping**
   - What: Route 53 returns alternating public/private IPs
   - Why: Active Directory conditional forwarder interaction with Databricks DNS updates
   - Workaround: Use wildcard `*.cloud.databricks.com` instead of specific hostname
   - Status: Under investigation with Microsoft + Databricks

2. **Private Link Endpoint DNS Conflict**
   - What: Cannot have 2 Private Link endpoints with Private DNS in same VPC
   - Why: Both try to claim `sydney.privatelink.cloud.databricks.com`
   - Workaround: Frontend endpoint has Private DNS disabled; Route 53 PHZs handle DNS
   - Impact: Adds Route 53 configuration overhead

3. **Zscaler CNAME Not Resolving**
   - What: Zscaler doesn't properly proxy CNAME-based workspace addresses
   - Why: Zscaler CNAME resolution limitation
   - Workaround: Catch all `*.cloud.databricks.com` traffic (not just specific CNAME)
   - Impact: All Databricks traffic routed through Zscaler (expected behavior anyway)

### 6.3 Growth & Expansion Notes

**Future Business Units (3 + already 3 = 6 total)**:
- 5th BU planned as `$future`
- Each BU needs: 2 workspaces × 3 AZs = 6 subnets
- VPC growth tracking: Currently 2.3% per BU, 5 BUs = ~12% total
- Remaining headroom: ~88% for future expansion or other services

**Workspace Naming Convention** (for future BUs):
```
{bu-name}-lab-workspace-{nonprod|prod}
{bu-name}-field-workspace-{nonprod|prod}
```

---

## 7. KEY CONTACTS & DEPENDENCIES

| Role | Name | Domain | Contact Point |
|------|------|--------|---|
| AWS/Network Lead | David Hunter | AWS account provisioning, firewall rules | Firewall whitelist for RDS |
| Databricks Architect | Sampath Jagannathan | Architecture decisions, workspace design | Design approval |
| Network/Infrastructure | @Vishnu Devarajan | Network topology, VPC configuration | VPC provisioning |
| Core Network Team | Neil Belford | Shared VPC, Direct Connect | VPC and routing |
| Infrastructure Code Owner | @Wee Lih Lee / @Nikilesh Chivukula | Terraform repo management | Repo structure questions |

---

## 8. QUICK REFERENCE: WHY, HOW, WHAT, WHEN

### WHY Architectural Choices Were Made

| Decision | Why |
|----------|-----|
| Business Unit Isolation | Prevent cross-BU blast radius, enable autonomous team development |
| Shared VPC (not account isolation) | Reduce AWS account overhead, leverage Jemena's existing network |
| Lab → Field promotion | Safe testing before production, clear governance checkpoint |
| Dual Private Link (backend + frontend) | Backend for cluster data plane, frontend for user UI access |
| Semantic versioning on modules | Maintain reusability while protecting backwards compatibility |
| One repo, multiple statefiles | Operational simplicity, standard CI/CD pattern |

### HOW Components Connect & Depend

| Component A | → | Component B | Mechanism |
|-------------|---|-------------|-----------|
| Cluster | → | Control Plane | Backend Private Link ENI |
| User/Client | → | Workspace UI | Frontend Private Link ENI |
| On-Prem Server | → | Workspace | Route 53 → Conditional Forwarder → Private Hosted Zone |
| Databricks Repo | → | AWS Repo | Terraform remote state data source |
| CI/CD Pipeline | → | Terraform State | GitLab runner with token permissions |
| SSL Client | → | External Service | Root CA certificate (injected at runtime) |

### WHAT Are Critical Constraints

| Constraint | Impact | Mitigation |
|-----------|--------|-----------|
| RDS Metastore firewall rule | Clusters can't authenticate to metadata | Whitelist from David Hunter |
| DNS flipping issue | Intermittent workspace access failures | Use `*.cloud.databricks.com` wildcard |
| Private Link endpoint DNS conflict | Can't use preferred DNS setup | Use Route 53 PHZs + workaround |
| SSL inspection on all traffic | External calls fail without cert | Distribute root CA cert |
| VPC subnet exhaustion | Only 1536 IPs per BU available | Monitor growth, expansion planned for future |

### WHEN To Apply Specific Patterns

| When | What Pattern | Why |
|------|-------------|-----|
| Creating new BU | Use `{bu-name}-lab` and `{bu-name}-field` workspace pair | Established naming convention |
| Adding workspace to platform | Add entry to Route 53 PHZ repo, add workspace stack to databricks-workspaces | Ensures proper DNS and infra provisioning |
| Modifying shared module (RBAC, schemas) | Test changes in lab workspace of test BU first, use semantic versioning | Prevent regression in other BUs |
| Promoting data product | Develop in lab workspace, test, then deploy production jobs to field workspace | Governance checkpoint pattern |
| Deploying to prod | Use prod.auto.tfvars, require additional approval | Environment separation |
| Adding new AWS resource type | Create in appropriate `-aws-infra` repo, reference via remote state in Databricks repo | Maintain infrastructure layering |

---

## 9. ACTIONABLE INTEGRATION CHECKLIST

Use this when onboarding new teams or adding features:

- [ ] **Network**: Confirm RDS metastore firewall rule is whitelisted
- [ ] **Security**: Distribute root CA certificate for SSL inspection
- [ ] **DNS**: Verify workspace address in Route 53 Private Hosted Zones
- [ ] **DNS**: Confirm Zscaler rule includes `*.cloud.databricks.com`
- [ ] **DNS**: Check on-prem AD conditional forwarder pointing to Route 53
- [ ] **Terraform**: Verify CI runner has GitLab token with remote state read permissions
- [ ] **Databricks**: Create new workspace following naming convention
- [ ] **Databricks**: Create stack directories in databricks-workspaces for `{ws}-infra` and `{ws}-resources`
- [ ] **Git**: Follow MR workflow with approval requirement
- [ ] **Testing**: Validate connectivity from corporate network via private link
- [ ] **Testing**: Validate connectivity from on-prem servers via private link
- [ ] **Documentation**: Update this document with any new patterns discovered

---

## 10. DOCUMENT METADATA

| Attribute | Value |
|-----------|-------|
| Created | 2025-11-16 |
| Source PDFs | 4 documents from FNDHAAP project |
| Platform Version | As of November 2024 |
| Scope | Databricks infrastructure on AWS for Jemena |
| Status | Active deployment |
| Last Updated | 2025-11-16 |
