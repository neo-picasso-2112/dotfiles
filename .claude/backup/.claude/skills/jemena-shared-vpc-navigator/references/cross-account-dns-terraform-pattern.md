# Cross-Account DNS Terraform Pattern

## Purpose

Complete terraform implementation guide for creating DNS records in core-network account's Private Hosted Zones from application accounts (app-datahub-prod, app-datahub-nonprod).

**When to Use:** Every new application with internal ALB (Data Mesh Manager, Energy Workbench, etc.)

---

## The Problem

- **Route53 Private Hosted Zones** are owned by core-network account (234268347951)
- **Application terraform** runs in app-datahub accounts (339712836516 prod, 851725449831 nonprod)
- **Application needs DNS** record pointing to its ALB

**Without this pattern:** Manual coordination with core-network team for every DNS change

---

## The Solution: Cross-Account AssumeRole

### Step 1: Terraform Provider Alias

Add a second AWS provider that assumes a role in core-network account:

```hcl
# main.tf or providers.tf

provider "aws" {
  alias  = "core_network_r53"
  region = "ap-southeast-2"

  assume_role {
    role_arn = "arn:aws:iam::234268347951:role/core-network-r53-records-role"
  }
}
```

**Key Points:**
- `alias` allows multiple AWS providers in same terraform config
- Role exists in core-network account
- Trust policy allows app-datahub accounts to assume this role
- GitLab OIDC role automatically has permissions to assume this role

---

### Step 2: Create DNS A Record

Create an alias A record pointing to your ALB:

```hcl
# dns.tf

resource "aws_route53_record" "app_dns" {
  provider = aws.core_network_r53  # Use the aliased provider

  zone_id  = var.route53_zone_id   # PHZ ID from core-network
  name     = var.app_dns_name      # e.g., "dmm.prod-vpc.aws.int"
  type     = "A"

  alias {
    name                   = aws_lb.alb.dns_name  # Your ALB in app account
    zone_id                = aws_lb.alb.zone_id
    evaluate_target_health = true
  }
}
```

**Key Points:**
- `provider = aws.core_network_r53` specifies cross-account provider
- `zone_id` is the Private Hosted Zone ID (differs for prod vs nonprod)
- `alias` block points to ALB in YOUR account (app-datahub)
- Alias records don't require TTL

---

### Step 3: Variables Configuration

Define environment-specific variables:

```hcl
# prod.auto.tfvars

route53_zone_id = "Z0230776MG3AOI9WPI6K"  # prod-vpc.aws.int PHZ
app_dns_name    = "dmm.prod-vpc.aws.int"
```

```hcl
# nonprod.auto.tfvars

route53_zone_id = "Z067397015OIIZFMCSI1G"  # nonprod-vpc.aws.int PHZ
app_dns_name    = "dmm.nonprod-vpc.aws.int"
```

---

## Private Hosted Zone IDs

**Production PHZ:**
- Name: `prod-vpc.aws.int`
- Zone ID: `Z0230776MG3AOI9WPI6K`
- VPC: core-network-shared-prod-vpc (vpc-002f643f2c6498c81)

**Nonprod PHZ:**
- Name: `nonprod-vpc.aws.int`
- Zone ID: `Z067397015OIIZFMCSI1G`
- VPC: core-network-shared-nonprod-vpc (vpc-0e5804a6ec5f68f35)

---

## Complete Example (Data Mesh Manager)

```hcl
# providers.tf
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "ap-southeast-2"

  assume_role {
    role_arn = "arn:aws:iam::339712836516:role/gitlab-oidc-prod-role"
  }
}

provider "aws" {
  alias  = "core_network_r53"
  region = "ap-southeast-2"

  assume_role {
    role_arn = "arn:aws:iam::234268347951:role/core-network-r53-records-role"
  }
}

# dns.tf
resource "aws_route53_record" "dmm_prod" {
  provider = aws.core_network_r53

  zone_id = "Z0230776MG3AOI9WPI6K"
  name    = "dmm.prod-vpc.aws.int"
  type    = "A"

  alias {
    name                   = aws_lb.dmm_alb.dns_name
    zone_id                = aws_lb.dmm_alb.zone_id
    evaluate_target_health = true
  }
}

# outputs.tf
output "app_url" {
  value = "https://${aws_route53_record.dmm_prod.name}"
}
```

---

## GitLab CI/CD Integration

The pattern works seamlessly with GitLab OIDC authentication:

```yaml
# .gitlab-ci.yml

apply:
  stage: apply
  script:
    - oidc-session.sh  # Establishes AWS session for app account
    - terraform apply -auto-approve
```

**How it Works:**
1. GitLab OIDC establishes session in app-datahub account
2. App account's terraform provider assumes core-network-r53-records-role
3. DNS record created in core-network PHZ
4. All via temporary credentials (no long-lived secrets)

---

## Trust Relationship

The `core-network-r53-records-role` trust policy allows app-datahub accounts:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "AWS": [
          "arn:aws:iam::339712836516:root",
          "arn:aws:iam::851725449831:root"
        ]
      },
      "Action": "sts:AssumeRole"
    }
  ]
}
```

**Key Points:**
- Both prod and nonprod app-datahub accounts can assume the role
- Role permissions limited to Route53 record creation/modification
- No ability to create/delete PHZs (only records)

---

## Common Errors & Fixes

### Error: "AccessDenied: User is not authorized to perform: sts:AssumeRole"

**Cause:** GitLab OIDC role doesn't have permission to assume core-network-r53-records-role

**Fix:** Verify OIDC role has this policy:
```json
{
  "Effect": "Allow",
  "Action": "sts:AssumeRole",
  "Resource": "arn:aws:iam::234268347951:role/core-network-r53-records-role"
}
```

---

### Error: "Route53 hosted zone not found: Z0230776MG3AOI9WPI6K"

**Cause:** Wrong zone ID or provider not using cross-account role

**Fix:**
1. Verify `provider = aws.core_network_r53` is specified on the resource
2. Check zone ID matches environment (prod vs nonprod)
3. Test role assumption: `aws sts assume-role --role-arn arn:aws:iam::234268347951:role/core-network-r53-records-role`

---

### Error: "Invalid alias target"

**Cause:** ALB resource not yet created when DNS record tries to reference it

**Fix:** Add explicit dependency:
```hcl
resource "aws_route53_record" "app_dns" {
  provider = aws.core_network_r53

  depends_on = [aws_lb.alb]  # Ensure ALB created first

  # ... rest of config
}
```

---

### Error: "Provider configuration not present"

**Cause:** Provider alias referenced before it's defined

**Fix:** Ensure provider block comes before any resources using it (in providers.tf)

---

## VPN Access Requirement

**CRITICAL:** DNS record in Route53 is NOT enough for VPN users to access the application.

**Additional Step Required:** Request conditional forwarder from core-network team

**Why:** VPN users' laptops use corporate AD DNS servers, which don't automatically query Route53

**See:** `coordination-workflows.md` lines 7-113 for conditional forwarder request template

**Timeline:**
- Route53 record: Immediate (terraform apply)
- Conditional forwarder: 1-2 business days (manual request)

---

## Verification Steps

### Step 1: Verify DNS Record Created

```bash
# From AWS CLI (using core-network role)
aws route53 list-resource-record-sets \
  --hosted-zone-id Z0230776MG3AOI9WPI6K \
  --query "ResourceRecordSets[?Name=='dmm.prod-vpc.aws.int.']"
```

### Step 2: Test DNS Resolution (Internal)

```bash
# From EC2 instance in same VPC
nslookup dmm.prod-vpc.aws.int

# Expected: Returns ALB private IPs (10.32.x.x)
```

### Step 3: Test Application Access (Internal)

```bash
# From EC2 instance
curl -I https://dmm.prod-vpc.aws.int

# Expected: HTTP/2 200 or 302 redirect
```

### Step 4: Test VPN Access (After Conditional Forwarder)

```bash
# From VPN-connected laptop
nslookup dmm.prod-vpc.aws.int

# Expected: Returns ALB private IPs via corporate DNS
```

---

## Real-World Examples

### Data Mesh Manager (Production)
- **Repository:** `datamesh-manager-prod`
- **File:** `dns.tf`
- **DNS:** `dmm.prod-vpc.aws.int`
- **PHZ:** Z0230776MG3AOI9WPI6K
- **ALB:** `dmm-alb-prod` (internal)

### Energy Workbench (Nonprod)
- **Repository:** `network-model-ewb-nonprod`
- **File:** `dns.tf`
- **DNS:** `ewb.nonprod-vpc.aws.int`
- **PHZ:** Z067397015OIIZFMCSI1G
- **ALB:** `ewb-alb-nonprod` (internal)

---

## Decision Tree: When to Use This Pattern

```
Need DNS for new application?
         │
         ▼
    Is application external-facing?
         │
    ├─ YES → Use public Route53 zone (different pattern)
    │
    └─ NO → Internal application
         │
         ▼
    Does it have an ALB?
         │
    ├─ YES → Use this cross-account DNS pattern
    │         Create A record alias to ALB
    │
    └─ NO → Use CNAME or different pattern
         (e.g., ECS service discovery, direct IP)
```

---

## Related Patterns

**For Databricks Workspaces:**
- See `core-network-databricks-workspaces-phz` repository
- Workspace DNS follows similar pattern but different zone

**For External Applications:**
- Public Route53 zones managed differently
- Involves ACM certificates for public TLS
- Not covered in this pattern

---

## Contact for Issues

**Trust Policy Changes:**
- Contact: Platform Team (Sampath Jagannathan)
- Slack: #datahub-platform

**PHZ Issues:**
- Contact: Core-Network Team (David Hunter)
- Email: david.hunter@jemena.com.au

**Conditional Forwarder:**
- Contact: Core-Network Team (David Hunter)
- SLA: 1-2 business days
