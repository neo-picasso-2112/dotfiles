---
name: jemena-shared-vpc-navigator
description: Critical guidance for working in Jemena's shared VPC networking model where core-network account (234268347951) owns VPCs, subnets, NAT gateways, Transit Gateway, and VPC endpoints shared to app-datahub accounts via AWS RAM. Prevents common mistakes like attempting to create/modify networking resources, investigating NAT gateways, or modifying security groups owned by Cloud team. Covers Databricks Private Link architecture (Backend vs Frontend), 3 DNS workarounds (AD forwarder flipping, endpoint conflicts, Zscaler CNAME), RDS metastore firewall requirements, and troubleshooting workspace access issues. Use when working with AWS networking, VPCs, subnets, security groups, Private Link, Route 53, DNS, or debugging connectivity issues in app-datahub-prod (339712836516) or app-datahub-nonprod (851725449831) accounts.
---

# Jemena Shared VPC & Networking Navigator

## Purpose

Prevent costly mistakes when working in Jemena's **shared VPC networking model** where:
- **Core-network account (234268347951)** owns ALL VPCs, subnets, NAT gateways, Transit Gateways, VPC endpoints
- **App-datahub accounts (339712836516 prod, 851725449831 nonprod)** consume shared networking via AWS RAM
- Standard AWS assumptions about account ownership **DO NOT APPLY**

This skill encodes:
- What resources you **CANNOT** modify (requires Cloud team coordination)
- What resources you **CAN** modify directly
- Databricks Private Link architecture (dual endpoints, DNS workarounds)
- Troubleshooting decision trees for access issues
- Coordination workflows and SLAs

## When to Use This Skill

**Automatically activate when:**
- Investigating NAT gateways, security groups, or subnets in app-datahub accounts
- Debugging workspace connectivity or user access issues
- Working with Databricks Private Link (Frontend or Backend)
- Troubleshooting DNS resolution for workspaces
- Planning network changes or new workspace deployment
- Cluster startup failures or RDS metastore connectivity errors

**Explicitly use when:**
- User mentions VPC, networking, subnets, security groups, Private Link, Route 53, DNS
- Errors contain "Access Denied" for VPC resources
- Questions about "why can't I create a subnet?" or "where are the NAT gateways?"

---

## Critical Ownership Model (MEMORIZE THIS)

### ⛔ CANNOT Modify - Requires Core-Network Team (David Hunter)

| Resource | Owner Account | Why You Can't Touch It | SLA |
|----------|---------------|------------------------|-----|
| **VPCs** | core-network (234268347951) | Not owned by app-datahub accounts | 5-10 business days |
| **Subnets** | core-network (234268347951) | Shared via AWS RAM, cannot create/delete | 2-5 business days |
| **NAT Gateways** | core-network (234268347951) | Centralized egress via Palo Alto firewalls | N/A (managed centrally) |
| **Transit Gateway** | core-network (234268347951) | Account-level connectivity managed centrally | N/A (managed centrally) |
| **VPC Endpoints** | core-network (234268347951) | Centralized for cost optimization (RDS, KMS, S3, SSM) | 2-5 business days |
| **Route Tables** | core-network (234268347951) | Centrally managed for traffic steering | N/A (managed centrally) |
| **Firewall Rules** | core-security (484357440923) | Palo Alto policies control inter-VPC traffic | 3-7 business days |
| **KMS Keys** | core-security (484357440923) | ALL encryption keys centrally managed | 2-5 business days |

### ✅ CAN Modify - Direct Changes in App-Datahub Accounts

| Resource | Scope | Notes |
|----------|-------|-------|
| **Security Groups** | Within assigned subnets | Can create/modify in app-datahub accounts |
| **S3 Buckets** | Account-level | Independent of VPC, fully manageable |
| **IAM Roles/Policies** | Account-level | Independent of VPC, fully manageable |
| **EC2/RDS/Lambda** | Within assigned subnets | Can deploy in shared subnets |

### ⚠️ NEVER Do This

```hcl
# ❌ WRONG - Attempting to create subnet in shared VPC
resource "aws_subnet" "databricks" {
  vpc_id     = "vpc-0ff11056a20a2ce44"  # core-network VPC
  cidr_block = "10.32.150.0/24"
}

# ❌ WRONG - Attempting to create NAT gateway
resource "aws_nat_gateway" "databricks" {
  allocation_id = aws_eip.nat.id
  subnet_id     = data.aws_subnet.public.id
}

# ❌ WRONG - Attempting to modify route table
resource "aws_route_table" "databricks" {
  vpc_id = data.aws_vpc.shared_prod.id
  route { cidr_block = "0.0.0.0/0", nat_gateway_id = "..." }
}
```

### ✅ Correct Pattern - Reference Existing Resources

```hcl
# ✅ CORRECT - Reference existing subnet via data source
data "aws_subnet" "databricks_az1" {
  filter {
    name   = "tag:Name"
    values = ["appdatahub-prodprivateaz1-02"]
  }
}

# ✅ CORRECT - Use hardcoded subnet IDs (documented in one place)
locals {
  digital_lab_subnet_ids = [
    "subnet-039d49c832c613766",  # 10.34.87.0/24 AZ1
    "subnet-04264bb265a9b477f",  # 10.34.88.0/24 AZ2
    "subnet-06c48e0b4be6a9b1c"   # 10.34.89.0/24 AZ3
  ]
}

# ✅ CORRECT - Create security group in app-datahub account
resource "aws_security_group" "databricks_workspace" {
  name        = "databricks-digital-lab-sg"
  description = "Security group for Digital BU Lab workspace"
  vpc_id      = data.aws_vpc.shared_nonprod.id  # Reference shared VPC

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
```

---

## WHY Networking is Constrained

### Traffic Flow: Transit Gateway → Palo Alto Firewalls

**All app-datahub traffic flows:**
App-Datahub → Transit Gateway (core-network) → Palo Alto Firewalls (core-security 484357440923) → Destination

**Impact:**
- ALL inter-VPC traffic inspected by Palo Alto firewalls
- Cross-BU communication requires Security team approval (ServiceNow, 3-7 days)
- No direct internet access (routed through Zscaler)
- RDS metastore access requires firewall whitelist
- SSL inspection requires CA cert distribution to clusters

### AWS RAM Resource Sharing

**How it works:** core-network (234268347951) owns VPCs/subnets/NAT, shares to app-datahub accounts via AWS RAM

**App-Datahub accounts CAN:**
- Use shared subnets (launch EC2/RDS/Lambda)
- Create security groups within shared VPC
- Reference shared VPC ID

**App-Datahub accounts CANNOT:**
- Create/modify subnets, route tables, NAT gateways, VPC CIDRs

**Terraform pattern:**
```hcl
# ✅ CORRECT - Reference via data source
data "aws_subnet" "databricks_az1" {
  id = "subnet-039d49c832c613766"  # Shared via AWS RAM
}

# ❌ WRONG - Cannot create subnet (owned by core-network)
resource "aws_subnet" "databricks" {
  vpc_id     = "vpc-0ff11056a20a2ce44"
  cidr_block = "10.32.150.0/24"
}
```

**Contact:** David Hunter (core-network team), 2-5 day SLA for subnet requests

---

## Databricks Private Link Architecture

### Dual Private Link Pattern (CRITICAL)

**Backend Private Link (BEPL)** - Cluster ↔ Control Plane:
- **Count**: 4 ENIs total (2 per environment: SCC + REST)
- **Nonprod**: 2 ENIs (SCC relay + REST API) in nonprod VPC (10.34.0.0/16)
- **Prod**: 2 ENIs (SCC relay + REST API) in prod VPC (10.32.0.0/16)
- **Private DNS Enabled**: YES (auto-resolves `sydney.privatelink.cloud.databricks.com`)
- **Repo**: `core-network-databricks-vpc-components/main-npd-vpc-resources.tf`

**Frontend Private Link (FEPL)** - User ↔ Workspace UI:
- **Count**: 1 ENI total (shared across ALL workspaces)
- **Location**: Prod VPC ONLY (10.32.0.0/16)
- **Serves**: BOTH nonprod AND prod workspaces
- **Private DNS Enabled**: NO (due to endpoint conflict with BEPL)
- **IPs**: 10.32.78.59, 10.32.78.86, 10.32.78.16
- **DNS**: Manual Route 53 Private Hosted Zones per workspace
- **Repo**: `core-network-databricks-vpc-components/main-frontend-privatelink.tf`

**WHY Single FEPL?** Simplifies DNS configuration, reduces costs, avoids needing fully qualified names per workspace.

### The 3 DNS Workarounds (Non-Negotiable)

**Workaround #1: Active Directory Conditional Forwarder**
- **Issue**: DNS query results flip inconsistently between private IPs and public IPs
- **Root Cause**: AD forwarder interaction with Databricks DNS updates (under investigation with Microsoft + Databricks)
- **Workaround**: Use wildcard `*.cloud.databricks.com` instead of `sydney.privatelink.cloud.databricks.com`
- **Impact**: ALL Databricks DNS requests sent to Route 53 (less elegant, but 100% consistent)

**Workaround #2: Frontend & Backend Endpoint Conflict**
- **Issue**: Cannot create 2 VPC endpoints with Private DNS names enabled for same DNS name in same VPC
- **Root Cause**: AWS constraint - BEPL and FEPL both want `sydney.privatelink.cloud.databricks.com`
- **Workaround**: FEPL created WITHOUT Private DNS names enabled, manual Route 53 PHZs per workspace
- **Impact**: Must create one PHZ per workspace in `core-network-databricks-workspaces-phz` repo

**Workaround #3: Zscaler CNAME Resolution**
- **Issue**: Zscaler doesn't resolve CNAMEs before applying rules, returns public IPs instead of private
- **Root Cause**: Databricks sets public CNAME: `jemena-digital-field.cloud.databricks.com` → `sydney.privatelink.cloud.databricks.com`
- **Workaround**: Zscaler rule catches `*.cloud.databricks.com` (wildcard)
- **Impact**: All Databricks requests caught by Zscaler, ensures CNAME resolution within Jemena network

---

## Decision Tree: User Can't Access Workspace

```
User attempts to access workspace
         │
         ▼
    [DNS Resolution Check]
    Run: nslookup <workspace-fqdn>
         │
         ├─▶ Returns PUBLIC IPs (3.x.x.x)?
         │      │
         │      └─▶ PROBLEM: Route 53 Private Hosted Zone missing
         │          FIX: Add workspace to core-network-databricks-workspaces-phz repo
         │          REPO: https://gitlab.com/jemena/platforms/core-network-databricks-workspaces-phz
         │          CREATE: Alias A record pointing to FEPL endpoint
         │
         ├─▶ Returns FEPL private IPs (10.32.78.59/86/16)?
         │      │
         │      └─▶ DNS OK → Check network connectivity
         │          │
         │          ├─▶ From laptop?
         │          │      │
         │          │      └─▶ Check Zscaler client running
         │          │          Verify rule catches *.cloud.databricks.com
         │          │          Contact: Security team if rule missing
         │          │
         │          └─▶ From server?
         │                 │
         │                 └─▶ Check on-prem DNS conditional forwarder
         │                     Target: Route 53 Inbound Endpoints
         │                            (10.32.1.130, 10.32.2.194, 10.32.3.190)
         │                     Contact: Core-network team
         │
         └─▶ Returns inconsistent IPs (flips)?
                │
                └─▶ PROBLEM: DNS flipping (Workaround #1 not applied)
                    FIX: Verify conditional forwarder set to *.cloud.databricks.com
                         (NOT sydney.privatelink.cloud.databricks.com)
                    Contact: Core-network team
```

**Quick Tests:**
```bash
# 1. DNS resolution (from laptop)
nslookup jemena-digital-field.cloud.databricks.com
# Expected: 10.32.78.59, 10.32.78.86, or 10.32.78.16
# If public IPs: PHZ missing

# 2. DNS resolution (from server)
Resolve-DnsName jemena-digital-field.cloud.databricks.com
# Expected: Private IPs via conditional forwarder

# 3. Workspace access (browser)
https://jemena-digital-field.cloud.databricks.com
# Expected: Databricks login page
# If "privacy settings error": DNS routing to public IP
```

---

## Decision Tree: Cluster Won't Start

```
Cluster fails to start
         │
         ▼
    [Check Error Message]
         │
         ├─▶ "Cannot connect to metastore"?
         │      │
         │      └─▶ CRITICAL: RDS metastore firewall whitelist
         │          HOST: mdnrak3rme5y1c.c5f38tyb1fdu.ap-southeast-2.rds.amazonaws.com
         │          PORT: 3306
         │          REQUIRED: Workspace subnets whitelisted
         │          CONTACT: David Hunter (core-network team)
         │          SLA: 2-5 business days
         │
         ├─▶ "Cannot reach control plane"?
         │      │
         │      └─▶ Check Backend Private Link ENIs
         │          VERIFY: BEPL ENIs exist in core-network-databricks-vpc-components
         │          NONPROD: SCC + REST ENIs in nonprod VPC
         │          PROD: SCC + REST ENIs in prod VPC
         │          CONTACT: Core-network team if degraded
         │
         ├─▶ "Init script execution failed"?
         │      │
         │      └─▶ Check init script volume path allowed in metastore
         │          PATH: /Volumes/{catalog}/global/scripts/{script}.sh
         │          FIX: Login to accounts.cloud.databricks.com
         │               → Catalog → Metastore → Allowed JARs/Init Scripts
         │               → Add volume path
         │          VERIFY: Script file exists in volume
         │
         └─▶ "Access Denied" to S3?
                │
                └─▶ Check IAM instance profile permissions
                    VERIFY: Cluster policy has instance_profile_arn
                    VERIFY: IAM role has S3 bucket permissions
                    VERIFY: KMS key policy allows IAM role to decrypt
                    REPO: app-datahub-{nonprod|prod}-databricks-aws-infra
                    FILE: main-{bu}-bu-wks-cloud-resources.tf
```

---

## Common Coordination Workflows

### Requesting New Subnets (2-5 Business Days)

**When:** New workspace or BU onboarding
**Contact:** David Hunter (core-network team)
**Include:** Account ID, VPC, use case, AZs (3), preferred CIDRs (3× /24), required-by date

### Requesting Firewall Whitelist (3-7 Business Days)

**When:** New workspace needs RDS metastore access
**Contact:** Security team via ServiceNow
**CRITICAL:** `mdnrak3rme5y1c.c5f38tyb1fdu.ap-southeast-2.rds.amazonaws.com:3306`
**Include:** Source subnets, destination (RDS endpoint:3306), protocol (TCP), justification

### Adding Workspace DNS (1 Business Day)

**When:** New workspace needs Private Link DNS
**Repository:** `core-network-databricks-workspaces-phz`
**Steps:** Add Route 53 PHZ + Alias A record pointing to FEPL endpoint

**Quick example:**
```hcl
resource "aws_route53_zone" "workspace_phz" {
  name = "jemena-<bu>-<env>.cloud.databricks.com"
  vpc { vpc_id = data.aws_vpc.prod.id }
}

resource "aws_route53_record" "workspace_fepl" {
  zone_id = aws_route53_zone.workspace_phz.zone_id
  name    = "jemena-<bu>-<env>.cloud.databricks.com"
  type    = "A"
  alias {
    name    = data.aws_vpc_endpoint.fepl.dns_entry[0].dns_name
    zone_id = data.aws_vpc_endpoint.fepl.dns_entry[0].hosted_zone_id
  }
}
```

**Full templates:** `references/coordination-workflows.md`

### Requesting KMS Keys (2-5 Business Days)

**When:** New application or workspace needs encryption

⚠️ **CRITICAL:** You CANNOT create KMS keys in app-datahub accounts

**Pattern:** ALL KMS keys provisioned in core-security account (484357440923)
**Contact:** Platform Team (platform-team@jemena.com.au) / David Hunter
**SLA:** 2-5 business days (for applications), included in BU onboarding (for Databricks)

**Complete guide:** `references/centralized-kms-pattern.md`

### Conditional Forwarder for VPN Access (CRITICAL)

**When:** New application with internal ALB (DMM, EWB)
**Contact:** David Hunter (core-network team)
**SLA:** 1-2 business days

**⚠️ CRITICAL:** 30% of applications miss this step → VPN users CANNOT access application

**Without this:** Application works internally but VPN users get DNS failures

**Template:** `references/coordination-workflows.md` lines 7-113

### Cross-Account DNS Terraform Pattern

**When:** Creating DNS records for applications in `*.prod-vpc.aws.int` or `*.nonprod-vpc.aws.int`

**Pattern:** Terraform in app-datahub account assumes role in core-network account to create Route53 records

**Complete guide:** `references/cross-account-dns-terraform-pattern.md`

**Quick snippet:**
```hcl
provider "aws" {
  alias = "core_network_r53"
  assume_role {
    role_arn = "arn:aws:iam::234268347951:role/core-network-r53-records-role"
  }
}

resource "aws_route53_record" "app" {
  provider = aws.core_network_r53
  zone_id  = "Z0230776MG3AOI9WPI6K"  # prod PHZ
  name     = "myapp.prod-vpc.aws.int"
  type     = "A"
  alias {
    name    = aws_lb.alb.dns_name
    zone_id = aws_lb.alb.zone_id
  }
}
```

---

## VPC & CIDR Reference

### VPC Ownership

| VPC Name | CIDR | Account | Purpose |
|----------|------|---------|---------|
| core-network-shared-prod-vpc | 10.32.0.0/16 | core-network (234268347951) | Production workloads |
| core-network-shared-nonprod-vpc | 10.34.0.0/16 | core-network (234268347951) | Development/testing |
| core-network-shared-dmz-vpc | 10.36.0.0/16 | core-network (234268347951) | DMZ resources |

### Subnet Allocation Pattern (Databricks)

**Each workspace requires:** 3 subnets (one per AZ) × /24 CIDR = 768 IPs per workspace

**CRITICAL CLARIFICATION:**
- **VPC Environment (prod/nonprod)** ≠ **Workspace Type (lab/field)**
- **Prod VPC (10.32.0.0/16)** contains BOTH lab AND field workspaces for ALL BUs
- **Nonprod VPC (10.34.0.0/16)** contains BOTH lab AND field workspaces for ALL BUs
- **Lab workspaces** = Development/QA environments (lower change control)
- **Field workspaces** = Production workloads (higher change control)

**Naming Convention:**
```
appdatahub-{vpc-env}privateaz{az}-{counter}

Examples:
- appdatahub-prodprivateaz1-02  (10.32.82.0/24) → Prod VPC, AZ1
- appdatahub-devprivateaz2-04   (10.34.88.0/24) → Nonprod VPC, AZ2

Note: "dev" in subnet name refers to nonprod VPC, NOT lab workspace type
```

**Current Allocations:**

**Prod VPC (10.32.0.0/16) - Contains lab AND field workspaces:**
- ElecNetwork Lab: 10.32.82-84.0/24 (3 subnets × 3 AZs)
- ElecNetwork Field: 10.32.85-87.0/24 (3 subnets × 3 AZs)
- Digital Lab: 10.32.88-90.0/24
- Digital Field: 10.32.91-93.0/24
- Corporate Lab: 10.32.98-100.0/24
- Corporate Field: 10.32.101-103.0/24

**Nonprod VPC (10.34.0.0/16) - Contains lab AND field workspaces:**
- ElecNetwork Lab: 10.34.81-83.0/24 (platform testing only)
- ElecNetwork Field: 10.34.84-86.0/24 (platform testing only)
- Digital Lab: 10.34.87-89.0/24
- Digital Field: 10.34.90-92.0/24
- Corporate Lab: 10.34.98-100.0/24
- Corporate Field: 10.34.101-103.0/24

**Why This Matters:**
- Nonprod VPC workspaces used for **platform infrastructure changes** (not business user workloads)
- Business users work in **Prod VPC** workspaces (both lab and field)
- Lab→Field promotion happens **within same VPC** (e.g., Digital Lab 10.32.88.0/24 → Digital Field 10.32.91.0/24)

---

## Quick Reference: Workspace DNS Flow

**Laptop Access:**
```
User Browser → Zscaler (*.cloud.databricks.com)
  → ZPA Appliances (AWS) → Route 53 PHZ
  → FEPL private IPs → Workspace
```

**Server Access:**
```
Server → On-Prem DNS (.net.int) → Conditional Forwarder
  → Route 53 Inbound Endpoints (10.32.1.130/2.194/3.190)
  → Route 53 PHZ → FEPL private IPs → Workspace
```

**Cluster Communication:**
```
Cluster → BEPL ENIs (SCC + REST)
  → Databricks Control Plane → RDS Metastore
```

---

## VPN Access Pattern

### How Data Platform Engineers Access AWS Resources

**Corporate VPN Users (Working remotely):**
```
Corporate Laptop → VPN Connection → On-Prem Network (.net.int domain)
  → Active Directory DNS Servers → Conditional Forwarders
  → Route 53 Inbound Endpoints (10.32.1.130, 10.32.2.194, 10.32.3.190)
  → Route 53 Private Hosted Zones → FEPL IPs → Workspace
```

**Office Users (Zscaler):**
```
Corporate Laptop → Zscaler Client → *.cloud.databricks.com rule
  → Route 53 → FEPL IPs → Workspace
```

**Troubleshooting VPN Access:**
- Verify VPN connection established (test: ping internal .net.int server)
- Test DNS resolution: `nslookup jemena-<workspace>.cloud.databricks.com`
- If returns public IPs (3.x.x.x): Conditional forwarder misconfigured on corporate DNS
- If timeout: VPN routing issue or firewall blocking Route 53 endpoints
- Contact: Core-network team (David Hunter) for conditional forwarder issues

**Full VPN architecture:** See `references/vpn-dns-architecture.md`

---

## For More Details

See reference files in `references/` folder:
- `vpn-dns-architecture.md` - VPN access architecture and DNS flow (NEW)
- `route53-resolver-rules.md` - Route 53 resolver configuration details (NEW)
- `networking-architecture-detailed.md` - Complete network topology, routing, diagrams
- `privatelink-troubleshooting-guide.md` - Comprehensive troubleshooting procedures
- `coordination-workflows.md` - Complete templates and contact matrix

See original PDFs:
- `references/Databricks-AWS-E2E-Infrastructure-Design.pdf` - Infrastructure design details
- `references/Shared-VPC-Architecture-and-Subnet-Allocation-Guide.pdf` - Shared VPC architecture
- `references/databricks-privatelink-implementation-guide.pdf` - Private Link technical details
- `references/databricks-frontend-privatelink-dns-configuration.pdf` - DNS configuration

---

**Critical Contacts:**
- **Core-Network Team (VPC/Subnets/Routing):** David Hunter
- **Security Team (Firewall Rules):** Via ServiceNow
- **Platform Team (Workspace Issues):** Digital Analytics Team via #datahub-platform Slack

**Emergency Escalation:**
- Production workspace outage: Immediate escalation to Platform Lead + On-call Engineer
- Network connectivity down >2 hours: Escalate to Platform Lead + Core-Network Team
