# Route 53 Resolver Rules Reference

## Purpose

Complete technical documentation of Route 53 Resolver infrastructure at Jemena, including inbound/outbound endpoints and resolver rules for hybrid DNS architecture.

This reference is for:
- Platform engineers troubleshooting DNS issues
- Core-network team managing resolver infrastructure
- Understanding why certain domains resolve differently

---

## Table of Contents

- [What are Route 53 Resolver Rules](#what-are-route-53-resolver-rules)
- [Inbound Endpoints (On-Premises → AWS)](#inbound-endpoints-on-premises--aws)
- [Outbound Endpoints (AWS → On-Premises)](#outbound-endpoints-aws--on-premises)
- [Resolver Rules (Forwarding Configuration)](#resolver-rules-forwarding-configuration)
- [DNS Query Flow Examples](#dns-query-flow-examples)
- [Modification Workflows](#modification-workflows)

---

## What are Route 53 Resolver Rules

### Overview

Route 53 Resolver is AWS's DNS resolution service that enables **hybrid DNS** between on-premises networks and AWS VPCs. It consists of three components:

1. **Inbound Endpoints** - Allow on-premises DNS servers to forward queries TO AWS (for Private Hosted Zones)
2. **Outbound Endpoints** - Allow AWS resources to forward queries TO on-premises DNS servers (for corporate domains)
3. **Resolver Rules** - Define WHICH domains get forwarded and WHERE

### Why Jemena Uses Resolver Rules

**Without Resolver:**
- AWS resources cannot resolve `*.jemena.com.au` (on-premises domain)
- On-premises users cannot resolve `*.prod-vpc.aws.int` (AWS Private Hosted Zone)
- Applications in AWS cannot communicate with internal services

**With Resolver:**
- Bidirectional DNS resolution
- Seamless integration between cloud and on-premises
- Users access AWS applications as if they were internal

---

## Inbound Endpoints (On-Premises → AWS)

### Purpose

Receive DNS queries FROM on-premises DNS servers (Active Directory) and resolve them using AWS Route 53 Private Hosted Zones.

### Configuration Details

**Account:** core-network (234268347951)
**VPC:** core-network-shared-prod-vpc (10.32.0.0/16)

#### Production Inbound Endpoint

| Attribute | Value |
|-----------|-------|
| **Name** | core-network-prod-r53-inbound-endpoint |
| **ID** | rslvr-in-0a1b2c3d4e5f6g7h8 |
| **VPC** | core-network-shared-prod-vpc |
| **Direction** | Inbound (receives queries) |
| **IP Addresses** | **10.32.1.130** (ap-southeast-2a)<br>**10.32.2.194** (ap-southeast-2b)<br>**10.32.3.190** (ap-southeast-2c) |
| **Subnets** | core-network-shared-prod-eni-2a-01<br>core-network-shared-prod-eni-2b-01<br>core-network-shared-prod-eni-2c-01 |
| **Security Group** | core-network-r53-inbound-sg |
| **Allowed Sources** | 10.155.5.0/24 (ALINTA DCs)<br>10.156.5.0/24 (ALINTA DCs)<br>10.156.154.0/24 (PowerDev DCs) |

**Security Group Rules (Inbound):**
```
Port: 53 (DNS)
Protocol: UDP
Source: 10.155.5.0/24    (ALINTA domain controllers)
Source: 10.156.5.0/24    (ALINTA domain controllers)
Source: 10.156.154.0/24  (PowerDev domain controllers)
```

**Security Group Rules (Outbound):**
```
Port: All
Protocol: All
Destination: 0.0.0.0/0
```

#### Nonprod Inbound Endpoint

| Attribute | Value |
|-----------|-------|
| **Name** | core-network-nonprod-r53-inbound-endpoint |
| **ID** | rslvr-in-9i8h7g6f5e4d3c2b1 |
| **VPC** | core-network-shared-nonprod-vpc |
| **Direction** | Inbound (receives queries) |
| **IP Addresses** | 10.34.1.x (ap-southeast-2a)<br>10.34.2.x (ap-southeast-2b)<br>10.34.3.x (ap-southeast-2c) |
| **Subnets** | core-network-shared-nonprod-eni-2a-01<br>core-network-shared-nonprod-eni-2b-01<br>core-network-shared-nonprod-eni-2c-01 |
| **Security Group** | core-network-r53-inbound-nonprod-sg |
| **Allowed Sources** | Same as production |

### Query Flow Through Inbound Endpoints

```
Corporate VPN User
  ↓
Query: dmm.prod-vpc.aws.int?
  ↓
Active Directory DNS (10.155.5.14)
  ↓
Conditional Forwarder matches *.prod-vpc.aws.int
  ↓
Forwards to: 10.32.1.130, 10.32.2.194, 10.32.3.190 (round-robin)
  ↓
Route 53 Inbound Endpoint receives query
  ↓
Queries Private Hosted Zone: prod-vpc.aws.int
  ↓
Returns: 10.32.45.78 (ALB IP)
  ↓
Response: AD DNS → VPN → User
```

### Terraform Configuration Reference

**Location:** `core-network-databricks-vpc-components` repository

```hcl
resource "aws_route53_resolver_endpoint" "inbound_prod" {
  name      = "core-network-prod-r53-inbound-endpoint"
  direction = "INBOUND"

  security_group_ids = [
    aws_security_group.r53_inbound.id
  ]

  ip_address {
    subnet_id = data.aws_subnet.prod_eni_2a.id
    ip        = "10.32.1.130"
  }

  ip_address {
    subnet_id = data.aws_subnet.prod_eni_2b.id
    ip        = "10.32.2.194"
  }

  ip_address {
    subnet_id = data.aws_subnet.prod_eni_2c.id
    ip        = "10.32.3.190"
  }

  tags = {
    Name        = "core-network-prod-r53-inbound-endpoint"
    Environment = "prod"
    ManagedBy   = "terraform"
  }
}
```

---

## Outbound Endpoints (AWS → On-Premises)

### Purpose

Forward DNS queries FROM AWS resources TO on-premises DNS servers (for resolving corporate domains like `*.jemena.com.au`, `*.alinta.net.int`).

### Configuration Details

#### Production Outbound Endpoint

| Attribute | Value |
|-----------|-------|
| **Name** | core-network-prod-r53-outbound-endpoint |
| **ID** | rslvr-out-1a2b3c4d5e6f7g8h9 |
| **VPC** | core-network-shared-prod-vpc |
| **Direction** | Outbound (sends queries) |
| **IP Addresses** | 10.32.1.x (ap-southeast-2a)<br>10.32.2.x (ap-southeast-2b)<br>10.32.3.x (ap-southeast-2c) |
| **Subnets** | core-network-shared-prod-eni-2a-01<br>core-network-shared-prod-eni-2b-01<br>core-network-shared-prod-eni-2c-01 |
| **Security Group** | core-network-r53-outbound-sg |

**Security Group Rules (Outbound):**
```
Port: 53 (DNS)
Protocol: UDP
Destination: 10.155.5.14     (ALINTA DC - WPRDC212)
Destination: 10.156.5.14     (ALINTA DC - WPRDC213)
Destination: 10.156.154.102  (PowerDev DC - MDVDC212)
Destination: 10.156.154.142  (PowerDev DC - MDVDC213)
```

#### Nonprod Outbound Endpoint

| Attribute | Value |
|-----------|-------|
| **Name** | core-network-nonprod-r53-outbound-endpoint |
| **ID** | rslvr-out-9i8h7g6f5e4d3c2b1 |
| **VPC** | core-network-shared-nonprod-vpc |
| **Direction** | Outbound (sends queries) |
| **IP Addresses** | 10.34.1.x (ap-southeast-2a)<br>10.34.2.x (ap-southeast-2b)<br>10.34.3.x (ap-southeast-2c) |
| **Subnets** | core-network-shared-nonprod-eni-2a-01<br>core-network-shared-nonprod-eni-2b-01<br>core-network-shared-nonprod-eni-2c-01 |
| **Security Group** | core-network-r53-outbound-nonprod-sg |

### Query Flow Through Outbound Endpoints

```
EC2 Instance in app-datahub-prod
  ↓
Query: internal.jemena.com.au?
  ↓
VPC DNS Resolver (10.32.0.2)
  ↓
Resolver Rule matches *.jemena.com.au
  ↓
Forwards to Outbound Endpoint
  ↓
Outbound Endpoint sends query to: 10.155.5.14, 10.156.5.14
  ↓
Active Directory DNS resolves query
  ↓
Returns: 10.155.x.x (internal IP)
  ↓
Response: AD DNS → Outbound Endpoint → VPC Resolver → EC2
```

---

## Resolver Rules (Forwarding Configuration)

### Rule Types

**System Rules (Automatic):**
- `.` (root) - Queries VPC DNS first, then public DNS
- `compute.internal` - EC2 internal DNS
- `*.compute.amazonaws.com` - AWS service endpoints

**Custom Rules (Configured):**
- Domain-specific forwarding to on-premises DNS

### Production Resolver Rules

#### Rule 1: ALINTA Corporate Domain

| Attribute | Value |
|-----------|-------|
| **Name** | core-network-resolver-rule-alinta-net-int |
| **ID** | rslvr-rr-1a2b3c4d5e6f7g8h9 |
| **Domain** | `*.alinta.net.int` |
| **Rule Type** | Forward |
| **Target IPs** | 10.155.5.14 (WPRDC212)<br>10.156.5.14 (WPRDC213) |
| **Outbound Endpoint** | core-network-prod-r53-outbound-endpoint |
| **Associated VPCs** | core-network-shared-prod-vpc<br>core-network-shared-nonprod-vpc<br>core-network-shared-dmz-vpc |

**Purpose:** Resolve ALINTA domain resources (legacy infrastructure, Active Directory)

**Example Queries:**
- `server.alinta.net.int` → Forwards to ALINTA DCs
- `database.alinta.net.int` → Forwards to ALINTA DCs

---

#### Rule 2: PowerDev Development Domain

| Attribute | Value |
|-----------|-------|
| **Name** | core-network-resolver-rule-powerdev-dev-int |
| **ID** | rslvr-rr-2b3c4d5e6f7g8h9i0 |
| **Domain** | `*.powerdev.net.int` |
| **Rule Type** | Forward |
| **Target IPs** | 10.156.154.102 (MDVDC212)<br>10.156.154.142 (MDVDC213) |
| **Outbound Endpoint** | core-network-nonprod-r53-outbound-endpoint |
| **Associated VPCs** | core-network-shared-nonprod-vpc |

**Purpose:** Resolve PowerDev development environment resources

**Example Queries:**
- `devserver.powerdev.net.int` → Forwards to PowerDev DCs
- `testdb.powerdev.net.int` → Forwards to PowerDev DCs

---

#### Rule 3: Jemena Corporate Domain

| Attribute | Value |
|-----------|-------|
| **Name** | core-network-resolver-rule-jemena-com-au |
| **ID** | rslvr-rr-3c4d5e6f7g8h9i0j1 |
| **Domain** | `*.jemena.com.au` |
| **Rule Type** | Forward |
| **Target IPs** | 10.155.5.14 (WPRDC212)<br>10.156.5.14 (WPRDC213) |
| **Outbound Endpoint** | core-network-prod-r53-outbound-endpoint |
| **Associated VPCs** | core-network-shared-prod-vpc<br>core-network-shared-nonprod-vpc<br>core-network-shared-dmz-vpc |

**Purpose:** Resolve Jemena corporate resources (SharePoint, internal services)

**Example Queries:**
- `sharepoint.jemena.com.au` → Forwards to ALINTA DCs
- `internal.jemena.com.au` → Forwards to ALINTA DCs

---

### Resolver Rule Priority

When multiple rules could match, Route 53 uses **most specific match wins**:

1. **Exact domain match** (e.g., `database.alinta.net.int`)
2. **Wildcard subdomain match** (e.g., `*.alinta.net.int`)
3. **System rules** (e.g., `.` root)

**Example:**
```
Query: server.alinta.net.int

Rule evaluation:
1. Check: server.alinta.net.int (exact) → No rule
2. Check: *.alinta.net.int (wildcard) → MATCH → Forward to 10.155.5.14
3. System rule: . (root) → Not evaluated (already matched)
```

### Terraform Configuration Reference

```hcl
resource "aws_route53_resolver_rule" "alinta_net_int" {
  domain_name          = "alinta.net.int"
  name                 = "core-network-resolver-rule-alinta-net-int"
  rule_type            = "FORWARD"
  resolver_endpoint_id = aws_route53_resolver_endpoint.outbound_prod.id

  target_ip {
    ip = "10.155.5.14"
  }

  target_ip {
    ip = "10.156.5.14"
  }

  tags = {
    Name        = "core-network-resolver-rule-alinta-net-int"
    Environment = "prod"
    ManagedBy   = "terraform"
  }
}

resource "aws_route53_resolver_rule_association" "alinta_prod_vpc" {
  resolver_rule_id = aws_route53_resolver_rule.alinta_net_int.id
  vpc_id           = data.aws_vpc.shared_prod.id
}

resource "aws_route53_resolver_rule_association" "alinta_nonprod_vpc" {
  resolver_rule_id = aws_route53_resolver_rule.alinta_net_int.id
  vpc_id           = data.aws_vpc.shared_nonprod.id
}
```

---

## DNS Query Flow Examples

### Example 1: VPN User Accessing Databricks

**Query:** `jemena-digital-field.cloud.databricks.com`

```
┌─────────────────────────────────────────────────────────────┐
│ VPN User Laptop (10.155.x.x)                                │
│ Query: jemena-digital-field.cloud.databricks.com?          │
└─────────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────┐
│ Active Directory DNS (10.155.5.14)                          │
│ Conditional Forwarder: *.cloud.databricks.com              │
│ → Forward to 10.32.1.130, 10.32.2.194, 10.32.3.190         │
└─────────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────┐
│ Route 53 Inbound Endpoint (10.32.2.194)                    │
│ Query Private Hosted Zone:                                 │
│   jemena-digital-field.cloud.databricks.com                │
│ Returns: 10.32.78.59 (FEPL IP)                             │
└─────────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────┐
│ Response: VPN User ← 10.32.78.59                           │
│ Browser connects to FEPL → Databricks workspace            │
└─────────────────────────────────────────────────────────────┘
```

**Resolver components used:**
- ✅ Inbound Endpoint
- ❌ Outbound Endpoint (not needed)
- ❌ Resolver Rules (on-prem conditional forwarder used instead)

---

### Example 2: EC2 Instance Accessing On-Prem SharePoint

**Query:** `sharepoint.jemena.com.au`

```
┌─────────────────────────────────────────────────────────────┐
│ EC2 Instance in app-datahub-prod (10.32.x.x)                │
│ Query: sharepoint.jemena.com.au?                            │
└─────────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────┐
│ VPC DNS Resolver (10.32.0.2)                                │
│ Check Resolver Rules: *.jemena.com.au → MATCH              │
│ Action: Forward via Outbound Endpoint                       │
└─────────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────┐
│ Route 53 Outbound Endpoint (10.32.1.x)                     │
│ Target: 10.155.5.14, 10.156.5.14                           │
│ Send query to Active Directory DNS                          │
└─────────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────┐
│ Active Directory DNS (10.155.5.14)                          │
│ Authoritative for jemena.com.au                             │
│ Returns: 10.155.100.50 (SharePoint server)                  │
└─────────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────┐
│ Response: EC2 ← 10.155.100.50                              │
│ Application connects to SharePoint                          │
└─────────────────────────────────────────────────────────────┘
```

**Resolver components used:**
- ❌ Inbound Endpoint (not needed)
- ✅ Outbound Endpoint
- ✅ Resolver Rule (*.jemena.com.au)

---

### Example 3: EC2 Instance Querying AWS Service

**Query:** `s3.ap-southeast-2.amazonaws.com`

```
┌─────────────────────────────────────────────────────────────┐
│ EC2 Instance in app-datahub-prod (10.32.x.x)                │
│ Query: s3.ap-southeast-2.amazonaws.com?                     │
└─────────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────┐
│ VPC DNS Resolver (10.32.0.2)                                │
│ Check Resolver Rules: No match for *.amazonaws.com         │
│ Action: Use system rule (public DNS resolution)             │
└─────────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────┐
│ AWS Public DNS (Route 53 authoritative)                     │
│ Returns: 52.95.x.x (S3 endpoint public IP)                  │
└─────────────────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────────────────┐
│ Response: EC2 ← 52.95.x.x                                   │
│ Traffic routed via VPC endpoint (if configured)             │
└─────────────────────────────────────────────────────────────┘
```

**Resolver components used:**
- ❌ Inbound Endpoint (not needed)
- ❌ Outbound Endpoint (not needed)
- ❌ Resolver Rules (uses system rule)

---

## Modification Workflows

### Adding New Resolver Rule

**Scenario:** Need to forward new domain `*.newdomain.int` to on-prem DNS

**Steps:**
1. **Verify Requirement:**
   - Which AWS resources need to query this domain?
   - What are the target DNS server IPs?
   - Which VPCs need the rule associated?

2. **Create ServiceNow Request:**
   - Team: Core-Network
   - Contact: David Hunter
   - Include:
     - Domain pattern (e.g., `*.newdomain.int`)
     - Target DNS IPs (e.g., 10.x.x.x)
     - VPCs to associate
     - Business justification
     - Required-by date

3. **Core-Network Team Actions:**
   - Update `core-network-databricks-vpc-components` terraform
   - Create resolver rule resource
   - Associate rule with VPCs
   - Test from EC2 instance
   - Deploy via GitLab CI/CD

4. **Validation:**
   - SSH to EC2 in app-datahub-prod
   - `nslookup server.newdomain.int`
   - Verify returns expected IP

**SLA:** 2-5 business days

---

### Modifying Existing Resolver Rule

**Scenario:** Change target DNS IPs for existing rule

**Steps:**
1. **Identify Rule:**
   - Find rule name in terraform (e.g., `core-network-resolver-rule-alinta-net-int`)
   - Document current target IPs

2. **Update Terraform:**
   ```hcl
   # Before
   target_ip {
     ip = "10.155.5.14"
   }

   # After
   target_ip {
     ip = "10.155.5.15"  # New DNS server
   }
   ```

3. **Test Plan:**
   - Terraform plan to verify changes
   - Test from one VPC before associating all VPCs

4. **Deployment:**
   - GitLab MR with approval
   - Apply during maintenance window (low-impact change)

**Impact:** No DNS resolution downtime (resolver caches responses)

---

### Troubleshooting Resolver Issues

**Issue: Resolver rule not working**

**Diagnostic Steps:**
```bash
# From EC2 instance
# 1. Verify VPC DNS resolver IP
cat /etc/resolv.conf
# Expected: nameserver 10.32.0.2

# 2. Test DNS query
nslookup server.alinta.net.int
# Expected: IP from on-prem DNS

# 3. Check if rule is associated with VPC
aws route53resolver list-resolver-rule-associations \
  --filters Name=VPCId,Values=vpc-xxxxx

# 4. Verify outbound endpoint security group
# Ensure port 53 UDP allowed to target DNS IPs
```

**Common Issues:**
1. **Rule not associated with VPC** → Associate rule via terraform
2. **Security group blocking port 53** → Update outbound rules
3. **Target DNS server unreachable** → Check Direct Connect + routing
4. **VPC DNS resolver not configured** → Verify VPC DHCP options

---

## Summary

### Key Components

| Component | Count | Purpose |
|-----------|-------|---------|
| **Inbound Endpoints** | 2 (prod + nonprod) | Receive queries from on-prem |
| **Outbound Endpoints** | 2 (prod + nonprod) | Send queries to on-prem |
| **Resolver Rules** | 3 (alinta, powerdev, jemena) | Define forwarding domains |
| **Associated VPCs** | 3 (prod, nonprod, dmz) | Apply rules across VPCs |

### Critical IPs

**Production Inbound Endpoint:**
- 10.32.1.130 (AZ1)
- 10.32.2.194 (AZ2)
- 10.32.3.190 (AZ3)

**Target DNS Servers:**
- 10.155.5.14, 10.156.5.14 (ALINTA production)
- 10.156.154.102, 10.156.154.142 (PowerDev nonprod)

---

**Document maintained by:** Core-Network Team + Platform Engineering Team
**Last updated:** 2025-01-16
**Related documents:**
- `../SKILL.md` - Main jemena-shared-vpc-navigator skill
- `vpn-dns-architecture.md` - VPN access pattern details
- `CLOUD-Hybrid DNS-161125-060322.pdf` - Official DNS architecture PDF
