# Coordination Workflows & Templates

Complete templates and workflows for coordinating with core-network, security, and platform teams.

---

## 1. Requesting New Subnets (2-5 Business Days)

**When:** New workspace or new business unit onboarding

**Contact:** David Hunter (core-network team)

**SLA:** 2-5 business days for provisioning + AWS RAM sharing

### Email Template

**Subject:** Subnet Request for app-datahub-{prod|nonprod} - {BU} {Environment} Workspace

**Body:**
```
Hi David,

Requesting 3 × /24 subnets for app-datahub-{prod|nonprod} account in core-network-shared-{prod|nonprod}-vpc:

Account Details:
- AWS Account: app-datahub-prod (339712836516) OR app-datahub-nonprod (851725449831)
- VPC: core-network-shared-prod-vpc (10.32.0.0/16) OR core-network-shared-nonprod-vpc (10.34.0.0/16)

Workspace Details:
- Business Unit: {BU} (e.g., Gas, Digital, Corporate, ElecNetwork, Sparky)
- Environment: {lab|field}
- Use Case: Databricks Workspace for {BU} BU - {lab|field} environment

Network Requirements:
- Availability Zones: ap-southeast-2a, ap-southeast-2b, ap-southeast-2c
- Subnet Size: 3 × /24 CIDR blocks
- Preferred CIDRs: {10.32.X.0/24, 10.32.Y.0/24, 10.32.Z.0/24} (or next available)
- Required by: {date}

Justification:
{Explain business need - e.g., "Onboarding 5th Business Unit to data platform" or "Adding production environment for existing BU"}

Additional Context:
- Current Allocations: {Reference existing BU subnet allocations if applicable}
- Expected IP Usage: ~250-500 IPs per subnet (Databricks cluster nodes + ENIs)

Thanks,
{Your Name}
{Platform Team}
```

### Example 1: New BU Onboarding (Gas BU)

```
Subject: Subnet Request for app-datahub-prod - Gas BU Lab and Field Workspaces

Hi David,

Requesting 6 × /24 subnets (3 for lab + 3 for field) for app-datahub-prod account (339712836516) in core-network-shared-prod-vpc (10.32.0.0/16):

Workspace Details:
- Business Unit: Gas
- Environments: Both lab (dev/qa) and field (production)
- Use Case: Databricks Workspaces for Gas BU data analytics

Network Requirements:
- AZs: ap-southeast-2a, ap-southeast-2b, ap-southeast-2c
- Subnet Size: 6 × /24 CIDR blocks
- Preferred CIDRs:
  - Lab: 10.32.104.0/24, 10.32.105.0/24, 10.32.106.0/24
  - Field: 10.32.107.0/24, 10.32.108.0/24, 10.32.109.0/24
  (or next available in sequence)
- Required by: 2025-12-15

Justification: Onboarding 5th Business Unit to data platform. Gas BU requires isolated workspaces following same multi-tenancy model as existing BUs (Digital, Corporate, ElecNetwork).

Additional Context:
- Current BUs occupy: 10.32.82-103.0/24 (22 subnets for 3 BUs)
- Gas BU allocation: 10.32.104-109.0/24 (6 subnets total)
- Remaining headroom: ~88% for future expansion

Thanks,
Sampath Jagannathan
Platform Lead - Data Platform
```

### Example 2: Adding Field Workspace to Existing BU

```
Subject: Subnet Request for app-datahub-prod - Corporate BU Field Workspace

Hi David,

Requesting 3 × /24 subnets for app-datahub-prod account (339712836516) in core-network-shared-prod-vpc:

Workspace Details:
- Business Unit: Corporate
- Environment: Field (production)
- Use Case: Production Databricks workspace for Corporate BU (lab workspace already exists)

Network Requirements:
- AZs: ap-southeast-2a, ap-southeast-2b, ap-southeast-2c
- Subnet Size: 3 × /24 CIDR blocks
- Preferred CIDRs: 10.32.101.0/24, 10.32.102.0/24, 10.32.103.0/24
  (adjacent to existing lab subnets: 10.32.98-100.0/24)
- Required by: 2025-11-30

Justification: Corporate BU ready to promote data pipelines from lab (dev) to field (production). Requires dedicated production workspace with isolated subnet allocation.

Thanks,
Platform Team
```

---

## 2. Requesting Firewall Whitelist (3-7 Business Days)

**When:** New workspace requires RDS metastore access

**Contact:** Security team via ServiceNow

**SLA:** 3-7 business days

### ServiceNow Request Template

**Request Type:** Firewall Rule Change

**Category:** AWS Cloud Firewall

**Subject:** Databricks Workspace - RDS Metastore Access for {BU} {Environment}

**Description:**
```
Requesting firewall rule to allow Databricks workspace subnets to access RDS metastore:

SOURCE:
- Account: app-datahub-{prod|nonprod} ({account-id})
- Subnets: {subnet-cidr-1}, {subnet-cidr-2}, {subnet-cidr-3}
- Description: Databricks {BU} {lab|field} workspace cluster subnets

DESTINATION:
- Endpoint: mdnrak3rme5y1c.c5f38tyb1fdu.ap-southeast-2.rds.amazonaws.com
- Port: 3306
- Protocol: TCP
- Direction: Outbound

JUSTIFICATION:
Databricks clusters require Hive metastore connectivity to function. Without this firewall rule, cluster startup will fail with "Cannot connect to metastore" error.

This is a CRITICAL pre-deployment requirement for workspace provisioning.

BUSINESS IMPACT:
- Blocking: Workspace deployment blocked until firewall rule applied
- Users Affected: {Number} data engineers, analysts, scientists in {BU} BU
- Required by: {date}

ADDITIONAL CONTEXT:
- Existing Rules: All other Databricks workspaces already have this rule (reference: {ticket-number})
- Security: RDS endpoint private, within AWS VPC, no public internet exposure
- Compliance: Standard Databricks platform pattern, approved by Platform Lead

Thanks,
{Your Name}
{Platform Team}
```

### Example: Corporate BU Field Workspace

```
Request Type: Firewall Rule Change
Category: AWS Cloud Firewall
Subject: Databricks Workspace - RDS Metastore Access for Corporate Field

Description:
Requesting firewall rule to allow Databricks workspace subnets to access RDS metastore:

SOURCE:
- Account: app-datahub-prod (339712836516)
- Subnets: 10.32.101.0/24, 10.32.102.0/24, 10.32.103.0/24
- Description: Databricks Corporate field workspace cluster subnets

DESTINATION:
- Endpoint: mdnrak3rme5y1c.c5f38tyb1fdu.ap-southeast-2.rds.amazonaws.com
- Port: 3306
- Protocol: TCP
- Direction: Outbound

JUSTIFICATION:
Databricks clusters require Hive metastore connectivity to function. Without this firewall rule, cluster startup will fail with "Cannot connect to metastore" error.

BUSINESS IMPACT:
- Blocking: Workspace deployment blocked until firewall rule applied
- Users Affected: 25 data engineers, analysts in Corporate BU
- Required by: 2025-11-30

ADDITIONAL CONTEXT:
- Existing Rules: Digital BU (INC000123), ElecNetwork BU (INC000456) already whitelisted
- Security: RDS endpoint private, within AWS VPC, TLS encrypted
- Compliance: Standard Databricks platform pattern, approved by Sampath Jagannathan (Platform Lead)

Thanks,
Platform Team - Databricks Workspace Deployment
```

---

## 3. Adding Workspace DNS (1 Business Day)

**When:** New workspace created, needs Private Link DNS resolution

**Repository:** `core-network-databricks-workspaces-phz`

**Contact:** Core-network team OR Platform team with AssumeRole permissions

**SLA:** 1 business day (if platform team has permissions)

### Step-by-Step Procedure

**Step 1: Clone Repository**
```bash
git clone https://gitlab.com/jemena/platforms/core-network-databricks-workspaces-phz
cd core-network-databricks-workspaces-phz
```

**Step 2: Create Feature Branch**
```bash
git checkout -b feature/add-{bu}-{env}-workspace-dns
```

**Step 3: Add Terraform Configuration**

**File:** `main-workspace-phzs.tf`

```hcl
# Private Hosted Zone for {BU} {Environment} workspace
resource "aws_route53_zone" "{bu}_{env}" {
  name = "jemena-{bu}-{env}.cloud.databricks.com"

  vpc {
    vpc_id = data.aws_vpc.prod.id  # FEPL is in prod VPC only
  }

  tags = {
    Name         = "jemena-{bu}-{env}-databricks-workspace-phz"
    BusinessUnit = "{BU}"
    Environment  = "{env}"
    ManagedBy    = "Terraform"
    Repository   = "core-network-databricks-workspaces-phz"
  }
}

# Alias A record pointing to FEPL endpoint
resource "aws_route53_record" "{bu}_{env}_fepl" {
  zone_id = aws_route53_zone.{bu}_{env}.zone_id
  name    = "jemena-{bu}-{env}.cloud.databricks.com"
  type    = "A"

  alias {
    name                   = data.aws_vpc_endpoint.fepl.dns_entry[0].dns_name
    zone_id                = data.aws_vpc_endpoint.fepl.dns_entry[0].hosted_zone_id
    evaluate_target_health = false
  }
}
```

**Step 4: Commit and Push**
```bash
git add main-workspace-phzs.tf
git commit -m "Add DNS for {bu} {env} workspace"
git push origin feature/add-{bu}-{env}-workspace-dns
```

**Step 5: Create Merge Request**
- Navigate to GitLab repository
- Create MR from feature branch → main
- Add description: "Add Private Hosted Zone for {BU} {env} workspace (FEPL DNS resolution)"
- Request review from core-network team or platform lead
- Wait for approval

**Step 6: Merge and Deploy**
- After approval, merge MR
- GitLab CI/CD pipeline automatically applies terraform
- Verify pipeline success (green checkmark)

**Step 7: Validate DNS Resolution**
```bash
# From laptop (requires Zscaler)
nslookup jemena-{bu}-{env}.cloud.databricks.com
# Expected: 10.32.78.59, 10.32.78.86, or 10.32.78.16

# From server (requires conditional forwarder)
Resolve-DnsName jemena-{bu}-{env}.cloud.databricks.com
# Expected: Private FEPL IPs via Route 53
```

### Complete Example: Gas BU Lab Workspace

**File:** `main-workspace-phzs.tf`

```hcl
# Gas BU Lab Workspace DNS
resource "aws_route53_zone" "gas_lab" {
  name = "jemena-gas-lab.cloud.databricks.com"

  vpc {
    vpc_id = data.aws_vpc.prod.id  # vpc-0ff11056a20a2ce44
  }

  tags = {
    Name         = "jemena-gas-lab-databricks-workspace-phz"
    BusinessUnit = "Gas"
    Environment  = "lab"
    ManagedBy    = "Terraform"
    Repository   = "core-network-databricks-workspaces-phz"
  }
}

resource "aws_route53_record" "gas_lab_fepl" {
  zone_id = aws_route53_zone.gas_lab.zone_id
  name    = "jemena-gas-lab.cloud.databricks.com"
  type    = "A"

  alias {
    name                   = data.aws_vpc_endpoint.fepl.dns_entry[0].dns_name
    zone_id                = data.aws_vpc_endpoint.fepl.dns_entry[0].hosted_zone_id
    evaluate_target_health = false
  }
}
```

**Git Workflow:**
```bash
git checkout -b feature/add-gas-lab-workspace-dns
git add main-workspace-phzs.tf
git commit -m "Add DNS for Gas lab workspace"
git push origin feature/add-gas-lab-workspace-dns
# Create MR → get approval → merge → CI/CD applies
```

**Validation:**
```bash
nslookup jemena-gas-lab.cloud.databricks.com
# Expected output:
# Name:    jemena-gas-lab.cloud.databricks.com
# Address: 10.32.78.59
# Address: 10.32.78.86
# Address: 10.32.78.16
```

---

## 4. SSL Certificate Distribution (CRITICAL for Cluster Function)

**When:** New workspace deployed, clusters need SSL inspection certificates

**Contact:** Platform team

**SLA:** Immediate (part of workspace setup)

### Requirement

**Why:** Zscaler performs SSL inspection on all outbound HTTPS traffic. Clusters require Jemena root CA certificate to trust intercepted connections.

**Without this:** Clusters fail to download packages from PyPI, Maven Central, Conda, etc.

### Distribution Method

**Via Init Scripts in Unity Catalog Volumes:**

**File:** `/Volumes/{catalog}/global/scripts/ca_cert_install.sh`

```bash
#!/bin/bash
# Install Jemena root CA certificate for SSL inspection

set -e

CA_CERT_URL="https://internal-pki.jemena.com.au/certs/jemena-root-ca.crt"
CERT_DEST="/usr/local/share/ca-certificates/jemena-root-ca.crt"

# Download CA certificate
curl -o "${CERT_DEST}" "${CA_CERT_URL}"

# Update CA trust store
update-ca-certificates

echo "Jemena root CA certificate installed successfully"
```

**Cluster Policy Configuration:**
```hcl
resource "databricks_cluster_policy" "bu_general_purpose" {
  name = "{bu}-{env}-general-purpose-policy"

  definition = jsonencode({
    "init_scripts": {
      "type": "fixed",
      "value": [
        {
          "volumes": {
            "destination": "/Volumes/{bu}_{env}_catalog/global/scripts/ca_cert_install.sh"
          }
        }
      ]
    }
  })
}
```

---

## 5. Requesting VPC Endpoint Creation (5-10 Business Days)

**When:** New AWS service requires private connectivity (e.g., Secrets Manager, ECR, SageMaker)

**Contact:** David Hunter (core-network team)

**SLA:** 5-10 business days (requires approval + architecture review)

### Email Template

**Subject:** VPC Endpoint Request - {Service Name} for Databricks Platform

**Body:**
```
Hi David,

Requesting VPC endpoint creation for {Service Name} in core-network-shared-{prod|nonprod}-vpc:

Service Details:
- Service: {AWS Service Name} (e.g., com.amazonaws.ap-southeast-2.secretsmanager)
- Type: Interface Endpoint (PrivateLink)
- VPC: core-network-shared-{prod|nonprod}-vpc ({10.32.0.0/16 | 10.34.0.0/16})

Network Requirements:
- Subnets: {Private subnets in 3 AZs}
- Security Group: Allow HTTPS (443) from app-datahub subnets
- Private DNS: Enabled (recommended)

Use Case:
{Explain why this service is needed - e.g., "Databricks clusters need to retrieve secrets from AWS Secrets Manager without internet egress"}

Justification:
- Security: Avoid internet exposure for sensitive operations
- Cost: Reduce NAT Gateway data transfer costs
- Compliance: Meet internal policy for private connectivity

Required by: {date}

Thanks,
{Your Name}
```

---

## Contact Directory

| Need | Team | Contact | Method | SLA |
|------|------|---------|--------|-----|
| **Subnets** | Core-Network | David Hunter | Email | 2-5 days |
| **Firewall Rules** | Security | Via ServiceNow | ServiceNow | 3-7 days |
| **Workspace DNS** | Core-Network | David Hunter OR Platform Team | GitLab MR | 1 day |
| **VPC Endpoints** | Core-Network | David Hunter | Email | 5-10 days |
| **AWS Account Issues** | Cloud Team | David Hunter | Email | 1-2 days |
| **Databricks Platform** | Platform Team | Sampath Jagannathan | Slack #datahub-platform | Same day |
| **Terraform Issues** | DevOps | Jay Jiang | Slack #datahub-platform | Same day |

---

## Escalation Paths

### P1: Production Workspace Outage
- **Immediate:** Platform Lead (Sampath Jagannathan) + On-call Engineer
- **Within 30 min:** Core-Network Team (David Hunter) if network-related
- **Within 1 hour:** Security Team if firewall-related

### P2: Deployment Blocked (Pre-Production)
- **Within 4 hours:** Platform Lead
- **Within 1 day:** Core-Network Team or Security Team (depending on blocker)

### P3: Enhancement Requests
- **Within 1 week:** Platform Team via Slack
- **Normal SLA:** Follow contact directory above
