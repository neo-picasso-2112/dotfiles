# FNDHAAP Visual Architecture Reference

This document provides ASCII diagrams and visual representations of the platform architecture described in the PDFs.

---

## 1. END-TO-END AWS PLATFORM TOPOLOGY

```
JEMENA CORPORATE NETWORK
┌─────────────────────────────────────────────────────────────────────┐
│                                                                       │
│  Users / On-Prem Servers                                            │
│  ↓                                                                    │
│  Zscaler (*.cloud.databricks.com routing)                           │
│  ↓                                                                    │
│  On-Prem DNS (Active Directory Conditional Forwarders)              │
│  ↓                                                                    │
│  AWS Direct Connect (Private Connectivity)                          │
│                                                                       │
└───────────────────┬─────────────────────────────────────────────────┘
                    │
                    │ Direct Connect
                    │
        ┌───────────┴──────────────┐
        │                          │
        ▼                          ▼
┌──────────────────┐      ┌──────────────────┐
│  NONPROD STACK   │      │   PROD STACK     │
│                  │      │                  │
│ AWS Account:     │      │ AWS Account:     │
│ app-datahub-     │      │ app-datahub-prod │
│ nonprod          │      │ (339712836516)   │
│ (851725449831)   │      │                  │
└──────────────────┘      └──────────────────┘
        │                          │
        │                          │
        ▼                          ▼
    ┌─────────────┐          ┌─────────────┐
    │ Shared VPC  │          │ Shared VPC  │
    │ 10.34.0/16  │          │ 10.32.0/16  │
    └─────────────┘          └─────────────┘
        │                          │
        │                          │
        ├─ Backend Private Link    ├─ Backend Private Link
        │  ENI (SCC)               │  ENI (SCC)
        │  ENI (REST)              │  ENI (REST)
        │                          │
        ├─ Frontend Private Link   ├─ (uses prod FEPL)
        │  (not deployed)          │  ENI
        │                          │
        └─ Route 53               └─ Route 53
           Private Hosted            Private Hosted
           Zones (PHZ)              Zones (PHZ)
```

---

## 2. NETWORK CONNECTIVITY FLOW

### User Access to Workspace (Frontend Private Link)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           USER BROWSER REQUEST                          │
│                         https://jemena-digitalfield   │
│                         .cloud.databricks.com           │
└────────────────────────────┬──────────────────────────────────┬─────────┘
                             │                                  │
                    ┌────────▼─────────┐           ┌────────────▼──────────┐
                    │ CORPNET LAPTOP   │           │ ONPREM SERVER        │
                    │ Running Zscaler  │           │ Connected via DNS     │
                    └────────┬─────────┘           └────────────┬──────────┘
                             │                                  │
         ┌───────────────────┴──────────────────┐               │
         │ Zscaler Intercepts                   │               │
         │ *.cloud.databricks.com               │               │
         │ Routes to Zscaler tunnel             │               │
         └───────────────────┬──────────────────┘               │
                             │                                  │
            ┌────────────────▼────────────────┐                 │
            │ Route 53 Inbound Endpoint       │                 │
            │ (conditional forwarder target)  │◄────────────────┘
            │                                 │   DNS Query
            └────────────────┬────────────────┘
                             │
            ┌────────────────▼────────────────┐
            │ Route 53 Private Hosted Zone    │
            │ Lookup:                         │
            │ jemena-digitalfield             │
            │ .cloud.databricks.com           │
            │ → Alias A record                │
            │ → FEPL VPC Endpoint IP          │
            └────────────────┬────────────────┘
                             │
            ┌────────────────▼────────────────┐
            │ PROD VPC                        │
            │ Frontend Private Link           │
            │ VPC Endpoint                    │
            │ (ENI: private IP address)       │
            └────────────────┬────────────────┘
                             │
            ┌────────────────▼────────────────┐
            │ Databricks Control Plane        │
            │ Workspace UI Endpoint           │
            │ Returns HTML/JS/CSS             │
            └────────────────┬────────────────┘
                             │
                    ┌────────▼─────────┐
                    │ BROWSER RENDERS  │
                    │ WORKSPACE UI     │
                    └──────────────────┘
```

### Cluster to Control Plane (Backend Private Link)

```
DATABRICKS WORKSPACE (Nonprod)
│
├─ Cluster Node 1
├─ Cluster Node 2
└─ Cluster Node 3
  │
  │ All data plane traffic
  │ (command results, logs, etc.)
  │
  ▼
Backend Private Link ENI #1 (SCC)
├─ Security Group allows outbound to control plane
│
Backend Private Link ENI #2 (REST)
├─ Security Group allows outbound to control plane
│
  │
  │ TCP/443 through AWS PrivateLink
  │ No internet routing
  │
  ▼
Databricks Control Plane
├─ Metadata operations
├─ Job scheduling
├─ Library distribution
└─ Cluster lifecycle management
```

---

## 3. SUBNET & VPC TOPOLOGY

### Nonprod VPC (10.34.0.0/16)

```
10.34.0.0/16 (Nonprod Shared VPC)
│
├─ Tenant 1 (ElecNetwork BU)
│  │
│  ├─ Workspace 1 (Lab)
│  │  ├─ 10.34.81.0/24 (AZ1) - appdatahub-devprivateaz1-02
│  │  ├─ 10.34.82.0/24 (AZ2) - appdatahub-devprivateaz2-02
│  │  └─ 10.34.83.0/24 (AZ3) - appdatahub-devprivateaz3-02
│  │
│  └─ Workspace 2 (Field)
│     ├─ 10.34.84.0/24 (AZ1) - appdatahub-devprivateaz1-03
│     ├─ 10.34.85.0/24 (AZ2) - appdatahub-devprivateaz2-03
│     └─ 10.34.86.0/24 (AZ3) - appdatahub-devprivateaz3-03
│
├─ Tenant 2 (Digital BU)
│  │
│  ├─ Workspace 1 (Lab)
│  │  ├─ 10.34.87.0/24 (AZ1) - appdatahub-devprivateaz1-04
│  │  ├─ 10.34.88.0/24 (AZ2) - appdatahub-devprivateaz2-04
│  │  └─ 10.34.89.0/24 (AZ3) - appdatahub-devprivateaz3-04
│  │
│  └─ Workspace 2 (Field)
│     ├─ 10.34.90.0/24 (AZ1) - appdatahub-devprivateaz1-05
│     ├─ 10.34.91.0/24 (AZ2) - appdatahub-devprivateaz2-05
│     └─ 10.34.92.0/24 (AZ3) - appdatahub-devprivateaz3-05
│
└─ Tenant 3 (Corporate BU)
   │
   ├─ Workspace 1 (Lab)
   │  ├─ 10.34.98.0/24 (AZ1) - appdatahub-devprivateaz1-06
   │  ├─ 10.34.99.0/24 (AZ2) - appdatahub-devprivateaz2-06
   │  └─ 10.34.100.0/24 (AZ3) - appdatahub-devprivateaz3-06
   │
   └─ Workspace 2 (Field)
      ├─ 10.34.101.0/24 (AZ1) - appdatahub-devprivateaz1-07
      ├─ 10.34.102.0/24 (AZ2) - appdatahub-devprivateaz2-07
      └─ 10.34.103.0/24 (AZ3) - appdatahub-devprivateaz3-07

Total: 21 subnets, 5,376 IP addresses
Usage: 1,536 IP addresses (clusters + Databricks infrastructure)
Utilization: 28.6% per workspace pair (room for growth)
```

### Prod VPC (10.32.0.0/16) - Identical Structure

```
10.32.0.0/16 (Prod Shared VPC)
│
├─ Tenant 1 (ElecNetwork BU)
│  ├─ Workspace 1 (Lab): 10.32.82-84/24 (AZ1-3)
│  └─ Workspace 2 (Field): 10.32.85-87/24 (AZ1-3)
│
├─ Tenant 2 (Digital BU)
│  ├─ Workspace 1 (Lab): 10.32.88-90/24 (AZ1-3)
│  └─ Workspace 2 (Field): 10.32.91-93/24 (AZ1-3)
│
└─ Tenant 3 (Corporate BU)
   ├─ Workspace 1 (Lab): 10.32.98-100/24 (AZ1-3)
   └─ Workspace 2 (Field): 10.32.101-103/24 (AZ1-3)
```

---

## 4. DATA FLOW: LAB → FIELD PROMOTION

```
Data Product Team
│
│ 1. Develop & Test
│ (notebooks, jobs, schemas)
│
▼
┌──────────────────────────────────────┐
│ LAB WORKSPACE                        │
│ (elec-network-lab-workspace-nonprod) │
│                                      │
│ ├─ Exploratory notebooks             │
│ ├─ Test jobs                         │
│ ├─ Test schemas                      │
│ └─ Test data transformations         │
└──────────────────────────────────────┘
│
│ 2. Code Review & Testing
│
▼ (MR approved, pipeline passes)
│
┌──────────────────────────────────────┐
│ FIELD WORKSPACE (PROD)               │
│ (elec-network-field-workspace-prod)  │
│                                      │
│ ├─ Production jobs (auto-run)        │
│ ├─ Production schemas (read-only)    │
│ ├─ Production data (full dataset)    │
│ └─ Production pipelines (scheduled)  │
└──────────────────────────────────────┘
│
│ 3. Monitoring & Observability
│
▼
Alerts & Dashboards


KEY ADVANTAGES:
✓ Prevents untested code from running on production data
✓ Clear separation between experimental and stable
✓ Enables governance checkpoints
✓ Matches Databricks best practices
```

---

## 5. TERRAFORM ARCHITECTURE

### Repository Dependency Graph

```
┌─────────────────────────────────────────────────────────────────┐
│                      JEMENA CORE NETWORK                         │
│                  (Managed by David Hunter)                       │
│              (Shared VPCs, Direct Connect, etc.)                 │
└──────────┬──────────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────────────────────────┐
│ CORE-NETWORK-DATABRICKS-VPC-COMPONENTS
│ (Private Link ENIs, Security Groups) │
│                                      │
│ ├─ Backend Private Link ENIs         │
│ ├─ Security Group Rules              │
│ ├─ Route 53 Private Hosted Zones    │
│ └─ outputs: eni_ids, sg_ids          │
└──────────────────────────────────────┘
           │
           ├─────────────────────────┬──────────────────────┐
           │                         │                      │
           ▼                         ▼                      ▼
    ┌─────────────────┐     ┌──────────────────┐  ┌──────────────────┐
    │   NONPROD AWS   │     │   PROD AWS       │  │ DATABRICKS-UNITY │
    │   INFRA REPO    │     │   INFRA REPO     │  │ CATALOG REPO     │
    │                 │     │                  │  │                  │
    │ ├─ S3 buckets   │     │ ├─ S3 buckets    │  │ ├─ RBAC modules  │
    │ ├─ IAM roles    │     │ ├─ IAM roles     │  │ ├─ Schemas       │
    │ ├─ Instance     │     │ ├─ Instance      │  │ ├─ Service Prncls│
    │ │   Profiles    │     │ │   Profiles     │  │ └─ Stacks:       │
    │ └─ RDS metastore│     │ └─ RDS metastore │  │   ├─ digital-bu  │
    │   (connection)  │     │   (connection)   │  │   ├─ elec-net-bu │
    │                 │     │                  │  │   └─ org (manual)│
    │ outputs:        │     │ outputs:         │  │                  │
    │ ├─ s3_arns      │     │ ├─ s3_arns       │  │ state files:     │
    │ ├─ role_arns    │     │ ├─ role_arns     │  │ 1 per BU         │
    │ └─ rds_endpoint │     │ └─ rds_endpoint  │  │                  │
    └──────┬──────────┘     └────────┬─────────┘  └────────┬─────────┘
           │                         │                     │
           │   (remote state)        │   (remote state)    │
           │                         │                     │
           └─────────────────┬───────┴─────────────────────┘
                             │
                             │ (terraform data source)
                             ▼
                    ┌─────────────────────┐
                    │ DATABRICKS-WORKSPACES│
                    │ REPO                 │
                    │                      │
                    │ ├─ Modules:          │
                    │ │  ├─ cluster-policy │
                    │ │  ├─ workspaces     │
                    │ │  ├─ long-lived-clstr
                    │ │  └─ sql-warehouses │
                    │ │                    │
                    │ └─ Stacks (1 each):  │
                    │    ├─ digital-lab-ws-infra
                    │    ├─ digital-lab-ws-resources
                    │    ├─ digital-field-ws-infra
                    │    ├─ digital-field-ws-resources
                    │    ├─ elec-net-lab-ws-infra
                    │    ├─ elec-net-lab-ws-resources
                    │    ├─ elec-net-field-ws-infra
                    │    └─ elec-net-field-ws-resources
                    │                      │
                    │ state files:         │
                    │ 1 per stack dir      │
                    └─────────────────────┘
```

### Terraform State File Isolation

```
TERRAFORM STATE ISOLATION STRATEGY

Repository: databricks-unity-catalog
├─ stacks/digital-bu/terraform.tfstate
│  └─ Manages: Catalogs, RBAC for Digital BU
│
├─ stacks/elec-network-bu/terraform.tfstate
│  └─ Manages: Catalogs, RBAC for ElecNetwork BU
│
└─ stacks/org/terraform.tfstate (manual deploy, no CI)
   └─ Manages: Account-level metastore config


Repository: databricks-workspaces
├─ stacks/digital-lab-workspace-infra/terraform.tfstate
│  └─ Manages: Workspace infrastructure for digital-lab-workspace-nonprod
│
├─ stacks/digital-lab-workspace-resources/terraform.tfstate
│  └─ Manages: Workspace resources (clusters, jobs, etc.)
│
├─ stacks/digital-field-workspace-infra/terraform.tfstate
│  └─ Manages: Workspace infrastructure for digital-field-workspace-prod
│
├─ stacks/digital-field-workspace-resources/terraform.tfstate
│  └─ Manages: Workspace resources for field workspace
│
├─ stacks/elec-network-lab-workspace-infra/terraform.tfstate
├─ stacks/elec-network-lab-workspace-resources/terraform.tfstate
├─ stacks/elec-network-field-workspace-infra/terraform.tfstate
└─ stacks/elec-network-field-workspace-resources/terraform.tfstate


BENEFIT: Each directory has separate state
├─ ✓ Changes in one workspace don't trigger refresh of others
├─ ✓ Different BUs can deploy independently
├─ ✓ Team autonomy with platform consistency
└─ ✓ Follows standard CI/CD multi-environment pattern
```

---

## 6. CI/CD PIPELINE FLOW

```
Developer
│
│ 1. Feature branch work
│    git checkout -b feature/add-new-cluster
│
▼
┌─────────────────────────────────┐
│ Feature Branch Commits          │
│ (changes to *.tf files)         │
└─────────────────────────────────┘
│
│ 2. Push and create MR
│    git push origin feature/add-new-cluster
│
▼
┌─────────────────────────────────┐
│ GitLab Merge Request            │
│                                 │
│ Status: DRAFT (requires approval)
│                                 │
│ Pipeline starts:                │
│ ├─ terraform init               │
│ ├─ terraform validate           │
│ ├─ terraform plan               │
│ └─ (results shown in MR)        │
└─────────────────────────────────┘
│
│ 3. Code review & approval
│    Minimum 1 approval required
│
▼
┌─────────────────────────────────┐
│ MR Approved                     │
│ Pipeline succeeded              │
│                                 │
│ Merge button enabled            │
└─────────────────────────────────┘
│
│ 4. Merge to main (if on main)
│    OR continues on branch
│
▼
┌─────────────────────────────────┐
│ Post-Merge Pipeline             │
│ (automatic)                     │
│                                 │
│ Based on branch/environment:    │
│ ├─ Load appropriate *.auto.tfvars
│ ├─ terraform apply              │
│ └─ Provision/update resources   │
└─────────────────────────────────┘
│
▼
┌─────────────────────────────────┐
│ AWS / Databricks Resources      │
│ Created or Updated              │
│                                 │
│ ├─ New clusters provisioned     │
│ ├─ IAM roles created            │
│ ├─ Workspaces configured        │
│ └─ etc.                         │
└─────────────────────────────────┘

PROTECTION RULES:
✗ Direct push to main BLOCKED
✗ Cannot merge without approval
✗ Pipeline must SUCCEED
✓ Subsequent commits revoke approvals (re-review required)
```

---

## 7. PRIVATE LINK DNS RESOLUTION LAYERS

```
REQUEST FLOW: Corporate Laptop Access to Workspace

USER TYPES: https://jemena-digitalfield.cloud.databricks.com

   ▼

LAYER 1: ZSCALER (Client-side)
┌─────────────────────────────────────────┐
│ Zscaler Rule:                           │
│ IF hostname = *.cloud.databricks.com    │
│ THEN route through Zscaler tunnel       │
│ (corporate network security)            │
│                                         │
│ ├─ PASS: traffic through Zscaler       │
│ └─ All other traffic: internet gateway  │
└─────────────────────────────────────────┘

   ▼

LAYER 2: ON-PREM DNS (Active Directory)
┌─────────────────────────────────────────┐
│ Conditional Forwarder Rule:             │
│ IF query = *.cloud.databricks.com       │
│ THEN forward to Route 53 Inbound EP     │
│                                         │
│ Workaround for DNS flipping issue:     │
│ (previously: sydney.privatelink.cloud.  │
│  databricks.com caused flipping)        │
└─────────────────────────────────────────┘

   ▼

LAYER 3: AWS ROUTE 53 (Inbound Endpoint)
┌─────────────────────────────────────────┐
│ Receives DNS query for:                 │
│ jemena-digitalfield.cloud.databricks.com
│                                         │
│ Lookup in Private Hosted Zone           │
│ (database of workspace → endpoint IPs)  │
│                                         │
│ Returns: Private IP of FEPL VPC EP      │
│ Example: 10.32.x.y (private address)    │
└─────────────────────────────────────────┘

   ▼

LAYER 4: PRIVATE LINK ENDPOINT
┌─────────────────────────────────────────┐
│ Frontend Private Link VPC Endpoint      │
│ (deployed in Prod VPC only)             │
│                                         │
│ Receives connection on private IP       │
│ Routes to Databricks control plane      │
│ Enables workspace UI access             │
└─────────────────────────────────────────┘

   ▼

RESULT: User accesses workspace through:
─ Secure private link (no internet)
─ Corporate network security (Zscaler)
─ Internal DNS resolution (Route 53)
─ Private IP routing (10.32.x.y)
```

---

## 8. KNOWN ISSUES & WORKAROUNDS VISUAL

```
ISSUE 1: DNS FLIPPING
┌─────────────────────────────────────────────────────────┐
│ Problem:                                                │
│ AD Conditional Forwarder ← Route 53 updates flipping   │
│                                                         │
│ Symptom: User gets private IP, then public IP          │
│          (alternating on each request)                 │
│                                                         │
│ Root Cause: DNS update conflict between Databricks    │
│            and Microsoft Active Directory             │
│                                                         │
│ Status: Under investigation with Microsoft + DB       │
│                                                         │
│ Workaround Implemented:                                │
│ ┌─────────────────────────────────────────────────────┐
│ │ Use wildcard: *.cloud.databricks.com                │
│ │ Instead of: sydney.privatelink.cloud.databricks.com │
│ │ Result: ALL Databricks traffic routed via Route 53  │
│ │ Impact: Functional but less elegant DNS solution    │
│ └─────────────────────────────────────────────────────┘
└─────────────────────────────────────────────────────────┘

ISSUE 2: PRIVATE LINK ENDPOINT DNS CONFLICT
┌─────────────────────────────────────────────────────────┐
│ Problem:                                                │
│ Cannot create 2 VPC endpoints with private DNS        │
│ Both want: sydney.privatelink.cloud.databricks.com    │
│                                                         │
│ Context:                                               │
│ ├─ Backend endpoint (for clusters): Created first     │
│ ├─ Frontend endpoint (for users): Can't use same DNS  │
│ └─ Must be in SAME VPC per requirements              │
│                                                         │
│ Option A (Not taken): Separate VPC for frontend       │
│   Problem: Complex routing, Zscaler integration       │
│                                                         │
│ Option B (✓ Implemented): Frontend in same VPC        │
│   ├─ Disable Private DNS on frontend endpoint         │
│   ├─ Use Route 53 PHZs for DNS routing                │
│   └─ Backend endpoint: Private DNS enabled            │
│                                                         │
│ Workaround Implemented:                                │
│ ┌─────────────────────────────────────────────────────┐
│ │ 1. Backend EP: Private DNS ON                        │
│ │    Auto-resolves sydney.privatelink... in VPC       │
│ │                                                     │
│ │ 2. Frontend EP: Private DNS OFF                      │
│ │    Requires Route 53 PHZ manual lookup               │
│ │                                                     │
│ │ 3. Route 53 PHZ: Alias A records                     │
│ │    jemena-digitalfield.cloud.databricks.com         │
│ │    → Points to Frontend EP IP                       │
│ │                                                     │
│ │ Result: Functional but requires external DNS setup  │
│ └─────────────────────────────────────────────────────┘
└─────────────────────────────────────────────────────────┘

ISSUE 3: ZSCALER CNAME RESOLUTION
┌─────────────────────────────────────────────────────────┐
│ Problem:                                                │
│ Zscaler doesn't properly proxy CNAME records           │
│                                                         │
│ Scenario:                                              │
│ ├─ Zscaler rule: Catch sydney.privatelink...          │
│ ├─ Workspace address: jemena-digitalfield.cdb.com     │
│ ├─ DNS response: CNAME to sydney.privatelink...       │
│ ├─ Zscaler: Doesn't follow CNAME, returns public IP   │
│ └─ Result: User bypasses corporate network security   │
│                                                         │
│ Workaround Implemented:                                │
│ ┌─────────────────────────────────────────────────────┐
│ │ Change Zscaler rule:                                │
│ │ FROM: sydney.privatelink.cloud.databricks.com       │
│ │ TO:   *.cloud.databricks.com (wildcard)             │
│ │                                                     │
│ │ Result:                                             │
│ │ ✓ All Databricks traffic routed through Zscaler    │
│ │ ✓ CNAME issue bypassed                              │
│ │ ✓ Corporate security policy enforced                │
│ │ ✗ Loss of routing optimization                       │
│ └─────────────────────────────────────────────────────┘
└─────────────────────────────────────────────────────────┘
```

---

## 9. GROWTH TRAJECTORY & CAPACITY PLANNING

```
CURRENT STATE (Nov 2024):
├─ 3 Business Units deployed (Electricity, Gas, Digital)
├─ 1 Shared VPC per environment (nonprod, prod)
├─ 2 workspaces per BU = 6 workspaces total
├─ 21 subnets per environment (3 AZs × 7 workspaces)
├─ Subnets used: 18 subnets × 2 envs = 36 subnets
└─ VPC utilization: ~2.3% per BU

FUTURE PLANNED GROWTH:
├─ 5 Business Units total (current 3 + Corporate)
├─ Additional future BU slots ($future)
├─ Same workspace pattern: 2 per BU
└─ Same subnet allocation: 3 AZs

SUBNET HEADROOM CALCULATION:
├─ Nonprod VPC: 10.34.0.0/16 = 256 subnets available
│  Current: 21 subnets (8.2% utilized)
│  Reserved for 5 BUs: ~35 subnets (13.7%)
│  Future expansion: 221 subnets available (86.3%)
│
└─ Prod VPC: 10.32.0.0/16 = 256 subnets available
   (Same calculation as nonprod)

CAPACITY AT 5 BUs:
├─ Subnets: 35 subnets (13.7% of VPC range)
├─ IP addresses: ~5,120 IPs per environment
├─ Remaining headroom: 245 subnets
├─ VPC footprint: ~12% (current estimate)
└─ Runway: Multiple years before needing expansion

BOTTLENECK ANALYSIS:
1. Subnet availability: Excellent (86% remaining)
2. IP address pool: Good (1500+ per BU)
3. Security group rules: MODERATE (Jemena SG limits)
   └─ Mitigation: Combine related subnet CIDR blocks
4. Route table entries: Good (AWS allows 100+)
5. AWS service limits: None expected in near term
```

---

## 10. ARCHITECTURE DECISION RECORD (ADR)

### ADR-001: Isolation-by-Business-Unit Over Account-per-Workspace

**Status**: ACCEPTED (July 2024)

**Context**:
- Jemena has multiple business units (Electricity, Gas, Digital, Corporate)
- Need to prevent cross-team infrastructure changes
- Operational team size constraints
- AWS account management overhead

**Decision**:
Use workspace isolation by Business Unit + environment, not account-per-workspace.

**Rationale**:
- Reduces AWS account management (2 accounts vs 10+)
- Enables Jemena's shared VPC strategy
- Terraform state file isolation handles cross-BU protection
- Each BU gets network isolation at subnet level

**Consequences**:
- ✓ Operational simplicity
- ✓ Shared network resources
- ✗ Requires careful security group management
- ✗ Shared VPC requires Jemena coordination

---

### ADR-002: Dual Private Link (Backend + Frontend Separate)

**Status**: ACCEPTED (July 2024)

**Context**:
- Databricks best practice: Separate data plane (backend) from control plane (frontend)
- Security requirement: User access through private link
- Cluster data must not flow through user access path

**Decision**:
Deploy two separate Private Link endpoints:
- Backend: For cluster ↔ control plane (data plane)
- Frontend: For user ↔ workspace UI (control plane)

**Rationale**:
- ✓ Follows Databricks reference architecture
- ✓ Enables network security layer separation
- ✓ Prevents data exfiltration through user path
- ✗ Requires additional DNS configuration (see Issues section)

**Consequences**:
- Need private link for each type of traffic
- DNS resolution complexity (workarounds needed)
- Additional networking configuration overhead

---

### ADR-003: Shared VPC Design Over Account Isolation

**Status**: ACCEPTED (July 2024)

**Context**:
- Jemena has existing shared VPC with Direct Connect
- Accounts: nonprod (app-datahub-nonprod) and prod (app-datahub-prod)
- Multiple workspaces must fit in existing network

**Decision**:
Use Jemena's shared VPCs (one per environment) rather than isolated accounts per workspace.

**Rationale**:
- ✓ Aligns with Jemena's network architecture
- ✓ Reduces AWS account overhead
- ✓ Single Direct Connect serves all workspaces
- ✗ Requires coordination with core-network team
- ✗ Adds DNS/routing complexity

**Consequences**:
- Must coordinate VPC requirements with David Hunter
- Network isolation at subnet level, not account boundary
- DNS and routing become critical configuration

---

## 11. DOCUMENT HISTORY

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2025-11-16 | Initial visual architecture extraction |
| - | - | - |

---

## 12. RELATED DOCUMENTATION

- `/Users/williamnguyen/repos/FNDHAAP-ARCHITECTURE-SUMMARY.md` - Full architectural details
- FNDHAAP-Infrastructure Design PDF - Network topology details
- FNDHAAP-Databricks Private Link Implementation PDF - Connectivity implementation
- FNDHAAP-Databricks Workspaces with Front End Private Link PDF - DNS workarounds
- FNDHAAP-Git Repo Topology PDF - Repository structure and CI/CD

