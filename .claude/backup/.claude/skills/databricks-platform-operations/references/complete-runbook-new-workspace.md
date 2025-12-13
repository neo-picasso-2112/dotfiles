# Complete Runbook: Adding New Workspace for Existing BU

**Time Estimate:** 20-30 minutes across 3 phases
**Prerequisites:** BU already has catalog cloud resources, VPC subnets allocated, GitLab Owner access

---

## Phase 1: AWS Cloud Resources (5-10 min)

**Repository:** `app-datahub-{nonprod|prod}-databricks-aws-infra`

### Step 1: Define Workspace Locals

**File:** `main-<bu>-bu-wks-cloud-resources.tf`

```hcl
locals {
  <bu>_bu_lab_workspace_name = "<bu>-lab-workspace-${var.environment}"
  <bu>_bu_lab_workspace_buckets = {
    "root" = "${var.prefix}-s3-${local.<bu>_bu_lab_workspace_name}-root"
  }
}
```

### Step 2: Call Workspace Cloud Resources Module

```hcl
module "<bu>_bu_lab_wks_cloud_resources" {
  source = "./modules/workspace-cloud-resources"

  environment       = var.environment
  aws_account_id    = var.aws_account_id
  business_unit     = "<bu>"
  workspace_name    = local.<bu>_bu_lab_workspace_name
  buckets           = local.<bu>_bu_lab_workspace_buckets

  # VPC Configuration (from core-network team)
  vpc_id             = data.aws_vpc.shared_nonprod.id
  subnet_ids         = ["subnet-xxxxx", "subnet-yyyyy", "subnet-zzzzz"]  # From David Hunter

  # Security
  kms_key_id         = aws_kms_key.<bu>_bu_key.arn
  external_id        = var.databricks_account_id  # 414351767826

  # Tagging
  tags = merge(
    local.common_tags,
    {
      BusinessUnit  = "<bu>"
      Environment   = "lab"
      ManagedBy     = "Terraform"
      Repository    = "app-datahub-nonprod-databricks-aws-infra"
    }
  )
}
```

### Step 3: Add Outputs

**File:** `outputs.tf`

```hcl
output "<bu>_bu_lab_wks_cloud_resources" {
  description = "Cloud resources for <bu> BU lab workspace"
  value = {
    workspace_root_bucket_name = module.<bu>_bu_lab_wks_cloud_resources.workspace_root_bucket_name
    cross_account_role_arn     = module.<bu>_bu_lab_wks_cloud_resources.cross_account_role_arn
    security_group_ids         = module.<bu>_bu_lab_wks_cloud_resources.security_group_ids
    instance_profile_arn       = module.<bu>_bu_lab_wks_cloud_resources.instance_profile_arn
    kms_key_arn                = module.<bu>_bu_lab_wks_cloud_resources.kms_key_arn
  }
}
```

### Step 4: Deploy

```bash
git checkout -b feature/add-<bu>-lab-workspace
git add main-<bu>-bu-wks-cloud-resources.tf shared-locals.tf outputs.tf
git commit -m "Add <bu> lab workspace cloud resources"
git push origin feature/add-<bu>-lab-workspace
# Create MR → get approval → merge → CI/CD applies
```

**Validation:**
- [ ] S3 root bucket created: `app-datahub-nonprod-s3-<bu>-lab-workspace-nonprod-root`
- [ ] IAM cross-account role created: `<bu>-lab-workspace-nonprod-cross-account-role`
- [ ] Security groups created: `<bu>-lab-workspace-nonprod-sg`
- [ ] Instance profile created: `<bu>-lab-workspace-nonprod-instance-profile`
- [ ] GitLab pipeline shows green checkmark

---

## Phase 2: Unity Catalog Workspace Registration (5-10 min)

**Repository:** `databricks-unity-catalog/stacks/<bu>-bu`

### Step 1: Update Remote State Dependencies

**File:** `dependencies.tf`

```hcl
# Remote state from AWS infra (Layer 1)
data "terraform_remote_state" "nonprod_aws_infra" {
  backend = "http"
  config = {
    address = "https://gitlab.jemena.com.au/api/v4/projects/12345/terraform/state/nonprod-aws-infra"
  }
}
```

### Step 2: Update Workspace Config Locals

**File:** `locals.tf`

```hcl
locals {
  workspace_config = {
    nonprod = {
      <bu>_bu_lab = {
        # Network config from core-network team
        subnets     = ["subnet-039d49c832c613766", "subnet-04264bb265a9b477f", "subnet-06c48e0b4be6a9b1c"]

        # Consume outputs from Layer 1
        sgs         = data.terraform_remote_state.nonprod_aws_infra.outputs.<bu>_bu_lab_wks_cloud_resources["security_group_ids"]
        root_bucket = data.terraform_remote_state.nonprod_aws_infra.outputs.<bu>_bu_lab_wks_cloud_resources["workspace_root_bucket_name"]
        xacc_role   = data.terraform_remote_state.nonprod_aws_infra.outputs.<bu>_bu_lab_wks_cloud_resources["cross_account_role_arn"]
      }
    }
  }

  # Metastore ID (pre-existing)
  metastore_id = {
    nonprod = "metastore-12345678-abcd-1234-efgh-123456789012"
    prod    = "metastore-87654321-dcba-4321-hgfe-210987654321"
  }
}
```

### Step 3: Create Workspace Module Call

**File:** `main-workspace-lab.tf`

```hcl
module "<bu>_lab_workspace" {
  source = "../../modules/managed-workspace"

  # Basic config
  workspace_name     = "<bu>-lab-workspace-${var.environment}"
  aws_region         = var.aws_region  # ap-southeast-2

  # Network (shared VPC from core-network)
  vpc_id             = local.target_vpc_id[var.environment]  # core-network VPC
  subnet_ids         = local.workspace_config[var.environment].<bu>_bu_lab.subnets
  security_group_ids = local.workspace_config[var.environment].<bu>_bu_lab.sgs

  # Storage (from Layer 1)
  storage_config_id  = local.workspace_config[var.environment].<bu>_bu_lab.root_bucket
  credentials_id     = local.workspace_config[var.environment].<bu>_bu_lab.xacc_role

  # Unity Catalog binding (PERMANENT - cannot change later)
  metastore_id       = local.metastore_id[var.environment]

  # Private Link (from core-network)
  backend_privatelink_endpoint_id  = data.terraform_remote_state.core_network.outputs.bepl_rest_endpoint_id[var.environment]
  frontend_privatelink_enabled     = true  # Requires PHZ in core-network-databricks-workspaces-phz

  # Tags
  tags = {
    BusinessUnit  = "<bu>"
    Environment   = "lab"
    ManagedBy     = "Terraform"
    Repository    = "databricks-unity-catalog"
    CostCenter    = var.cost_center_<bu>
  }
}
```

### Step 4: Add Outputs

**File:** `outputs.tf`

```hcl
output "<bu>_lab_workspace" {
  description = "<bu> BU lab workspace details"
  value = {
    workspace_id   = module.<bu>_lab_workspace.workspace_id
    workspace_url  = module.<bu>_lab_workspace.workspace_url
    workspace_name = module.<bu>_lab_workspace.workspace_name
  }
  sensitive = false
}
```

### Step 5: Deploy and Record Workspace URL

```bash
git checkout -b feature/add-<bu>-lab-workspace-databricks
git add locals.tf main-workspace-lab.tf dependencies.tf outputs.tf
git commit -m "Add <bu> lab workspace to Unity Catalog"
git push origin feature/add-<bu>-lab-workspace-databricks
# Create MR → get approval → merge → CI/CD applies
```

**CRITICAL: Record workspace URL from GitLab pipeline output logs**

Example output:
```
module.<bu>_lab_workspace.workspace_url = "https://jemena-<bu>-lab.cloud.databricks.com"
```

**Validation:**
- [ ] Workspace created in Databricks account
- [ ] Workspace URL accessible via SSO
- [ ] Workspace bound to correct metastore (check in Databricks UI)
- [ ] Workspace URL recorded for Phase 3

---

## Phase 3: Workspace-Level Resources (10-15 min)

**Repository:** `databricks-workspaces/stacks/<bu>-bu`

### Step 1: Update Remote State Dependencies

**File:** `upstream_stacks.tf`

```hcl
# Layer 1: AWS Infra
data "terraform_remote_state" "nonprod_aws_infra" {
  backend = "http"
  config = {
    address = "https://gitlab.jemena.com.au/api/v4/projects/12345/terraform/state/nonprod-aws-infra"
  }
}

# Layer 2: Unity Catalog
data "terraform_remote_state" "databricks_unity_catalog" {
  backend = "http"
  config = {
    address = "https://gitlab.jemena.com.au/api/v4/projects/67890/terraform/state/<bu>-bu"
  }
}
```

### Step 2: Configure Provider for Workspace

**File:** `providers.tf`

```hcl
terraform {
  required_providers {
    databricks = {
      source  = "databricks/databricks"
      version = "~> 1.54.0"
    }
  }
}

provider "databricks" {
  alias = "<bu>_lab"

  host  = data.terraform_remote_state.databricks_unity_catalog.outputs.<bu>_lab_workspace["workspace_url"]
  token = var.databricks_service_principal_token  # From GitLab CI/CD variables

  # OAuth M2M (recommended for production)
  # client_id     = var.databricks_sp_client_id
  # client_secret = var.databricks_sp_client_secret
}
```

### Step 3: Define Catalog Storage Mapper

**File:** `locals.tf`

```hcl
locals {
  # Consume catalog S3 buckets from Layer 1 remote state
  bu_lab_catalog_s3_buckets = data.terraform_remote_state.nonprod_aws_infra.outputs.<bu>_bu_lab_ctlg_cloud_resources["catalog_buckets"]

  # Map schemas to S3 buckets (medallion architecture)
  bu_lab_catalog_storage_mapper = {
    "landing"               = local.bu_lab_catalog_s3_buckets["landing"].name
    "bronze_<source_system>" = local.bu_lab_catalog_s3_buckets["bronze"].name
    "silver"                = local.bu_lab_catalog_s3_buckets["silver"].name
    "gold"                  = local.bu_lab_catalog_s3_buckets["gold"].name
  }
}
```

### Step 4: Create Medallion Schemas

**File:** `main-medallion-schemas.tf`

```hcl
module "<bu>_lab_medallion_schemas" {
  source = "../../modules/medallion-schemas"

  providers = {
    databricks = databricks.<bu>_lab
  }

  # Catalog (from Layer 2)
  catalog_name     = "<bu>_lab_catalog"

  # Storage mapping (from Layer 1)
  storage_mapper   = local.bu_lab_catalog_storage_mapper

  # External locations (from Layer 2)
  external_locations = {
    landing = data.terraform_remote_state.databricks_unity_catalog.outputs.<bu>_lab_external_locations["landing"]
    bronze  = data.terraform_remote_state.databricks_unity_catalog.outputs.<bu>_lab_external_locations["bronze"]
    silver  = data.terraform_remote_state.databricks_unity_catalog.outputs.<bu>_lab_external_locations["silver"]
    gold    = data.terraform_remote_state.databricks_unity_catalog.outputs.<bu>_lab_external_locations["gold"]
  }

  # Volumes (optional)
  create_volumes   = true
  volume_path      = "/Volumes/<bu>_lab_catalog/global/scripts"

  # Tags
  tags = {
    BusinessUnit = "<bu>"
    Environment  = "lab"
  }
}
```

### Step 5: Configure Enhanced Grants (RBAC)

**File:** `main-enhanced-grants.tf`

```hcl
module "<bu>_lab_enhanced_grants" {
  source = "../../modules/enhanced-grants"

  providers = {
    databricks = databricks.<bu>_lab
  }

  catalog_name = "<bu>_lab_catalog"

  # Access groups (from Layer 2)
  access_groups = {
    catalog_ro = data.terraform_remote_state.databricks_unity_catalog.outputs.<bu>_lab_access_groups["ctlg_ro_ag"]
    catalog_rw = data.terraform_remote_state.databricks_unity_catalog.outputs.<bu>_lab_access_groups["ctlg_rw_ag"]
    workspace_viewer = data.terraform_remote_state.databricks_unity_catalog.outputs.<bu>_lab_access_groups["wks_viewer_ag"]
  }

  # Schema-level grants
  schema_grants = {
    landing = ["catalog_rw"]
    bronze  = ["catalog_rw"]
    silver  = ["catalog_rw", "catalog_ro"]
    gold    = ["catalog_ro"]
  }
}
```

### Step 6: Configure Cluster Policy (Optional)

**File:** `main-cluster-policy.tf`

```hcl
resource "databricks_cluster_policy" "<bu>_lab_general_purpose" {
  provider = databricks.<bu>_lab

  name = "<bu>-lab-general-purpose-policy"

  definition = jsonencode({
    "aws_attributes.instance_profile_arn" : {
      "type" : "fixed",
      "value" : data.terraform_remote_state.nonprod_aws_infra.outputs.<bu>_bu_lab_wks_cloud_resources["instance_profile_arn"]
    },
    "node_type_id" : {
      "type" : "allowlist",
      "values" : ["i3.xlarge", "i3.2xlarge", "m5d.large", "m5d.xlarge"]
    },
    "driver_node_type_id" : {
      "type" : "allowlist",
      "values" : ["i3.xlarge", "m5d.large"]
    },
    "spark_version" : {
      "type" : "regex",
      "pattern" : "^1[3-9]\\.[0-9]+-scala.*"
    },
    "init_scripts" : {
      "type" : "fixed",
      "value" : [
        {
          "volumes" : {
            "destination" : "/Volumes/<bu>_lab_catalog/global/scripts/ca_cert_install.sh"
          }
        },
        {
          "volumes" : {
            "destination" : "/Volumes/<bu>_lab_catalog/global/scripts/dns_config.sh"
          }
        }
      ]
    }
  })
}
```

### Step 7: Deploy

```bash
git checkout -b feature/add-<bu>-lab-workspace-resources
git add upstream_stacks.tf providers.tf locals.tf main-*.tf
git commit -m "Add <bu> lab workspace resources (schemas, grants, policies)"
git push origin feature/add-<bu>-lab-workspace-resources
# Create MR → get approval → merge → CI/CD applies
```

**Validation:**
- [ ] Schemas created in workspace (landing, bronze, silver, gold)
- [ ] External locations bound to schemas
- [ ] Volumes created (if enabled)
- [ ] Enhanced grants applied (check SHOW GRANTS ON SCHEMA)
- [ ] Cluster policy created (check Compute → Policies)

---

## Phase 4: DNS Configuration (Core-Network Team)

**Repository:** `core-network-databricks-workspaces-phz`
**Responsibility:** Core-network team OR Platform team with AssumeRole permissions

### Step 1: Add Private Hosted Zone

**File:** `main-workspace-phzs.tf`

```hcl
resource "aws_route53_zone" "<bu>_lab" {
  name = "jemena-<bu>-lab.cloud.databricks.com"

  vpc {
    vpc_id = data.aws_vpc.prod.id  # FEPL is in prod VPC
  }

  tags = {
    Name         = "jemena-<bu>-lab-databricks-workspace-phz"
    BusinessUnit = "<bu>"
    Environment  = "lab"
    ManagedBy    = "Terraform"
  }
}
```

### Step 2: Add Alias A Record to FEPL

```hcl
resource "aws_route53_record" "<bu>_lab_fepl" {
  zone_id = aws_route53_zone.<bu>_lab.zone_id
  name    = "jemena-<bu>-lab.cloud.databricks.com"
  type    = "A"

  alias {
    name                   = data.aws_vpc_endpoint.fepl.dns_entry[0].dns_name
    zone_id                = data.aws_vpc_endpoint.fepl.dns_entry[0].hosted_zone_id
    evaluate_target_health = false
  }
}
```

### Step 3: Deploy

```bash
git checkout -b feature/add-<bu>-lab-workspace-dns
git add main-workspace-phzs.tf
git commit -m "Add DNS for <bu> lab workspace"
git push origin feature/add-<bu>-lab-workspace-dns
# Create MR → get approval → merge → CI/CD applies
```

**Validation:**
- [ ] DNS resolution returns FEPL private IPs:
  ```bash
  nslookup jemena-<bu>-lab.cloud.databricks.com
  # Expected: 10.32.78.59, 10.32.78.86, or 10.32.78.16
  ```
- [ ] Workspace URL accessible via browser (SSO login)

---

## Phase 5: Post-Deployment Validation

### Validation Checklist

**AWS Resources (Layer 1):**
- [ ] S3 root bucket created and encrypted with KMS
- [ ] IAM cross-account role created with trust policy for Databricks (414351767826)
- [ ] Security groups created with correct egress rules
- [ ] Instance profile created and attached to IAM role
- [ ] KMS key policy allows Databricks account and instance profile

**Unity Catalog (Layer 2):**
- [ ] Workspace created in Databricks account (check accounts.cloud.databricks.com)
- [ ] Workspace bound to correct metastore (nonprod or prod)
- [ ] Catalog visible in workspace (check Data → Catalogs)
- [ ] Storage credentials configured correctly
- [ ] RBAC access groups created

**Workspace Resources (Layer 3):**
- [ ] Medallion schemas created (landing, bronze, silver, gold)
- [ ] External locations bound to schemas
- [ ] Volumes created (if applicable)
- [ ] Enhanced grants applied (users can see catalogs/schemas)
- [ ] Cluster policy configured with init scripts

**Networking:**
- [ ] DNS resolves to FEPL private IPs (not public)
- [ ] Workspace URL accessible via SSO
- [ ] RDS metastore firewall whitelist includes workspace subnets

**GitLab CI/CD:**
- [ ] Service principal credentials configured in GitLab group variables
- [ ] CI/CD pipelines can authenticate to workspace

### Quick Smoke Tests

**Test 1: Catalog Visibility**
```sql
-- Login to workspace, run in SQL editor
SHOW CATALOGS;
-- Expected: <bu>_lab_catalog visible

USE CATALOG <bu>_lab_catalog;
SHOW SCHEMAS;
-- Expected: landing, bronze_*, silver, gold
```

**Test 2: External Location Access**
```sql
-- Check external location configuration
DESCRIBE EXTERNAL LOCATION <bu>_lab_landing_external_location;
-- Expected: S3 path, storage credential, readable
```

**Test 3: Cluster Creation**
```python
# Create cluster using policy
# Compute → Create Cluster → Select "<bu>-lab-general-purpose-policy"
# Cluster should start successfully and connect to metastore
```

**Test 4: Init Scripts Execution**
```bash
# From cluster driver node (after cluster starts)
cat /databricks/init_scripts/output/ca_cert_install.sh.out
cat /databricks/init_scripts/output/dns_config.sh.out
# Expected: No errors, certificates installed, DNS configured
```

---

## Troubleshooting Common Issues

### Issue 1: Workspace Binding Fails

**Error:** "Metastore ID not found - cannot bind workspace"

**Cause:** Layer 2 (Unity Catalog) not deployed before workspace creation

**Fix:**
```bash
cd databricks-unity-catalog/stacks/<bu>-bu
terraform plan  # Verify metastore exists
terraform output metastore_id
# If metastore missing → deploy Layer 2 first
```

### Issue 2: DNS Resolution Returns Public IPs

**Error:** `nslookup jemena-<bu>-lab.cloud.databricks.com` returns 3.x.x.x IPs

**Cause:** Private Hosted Zone not created in core-network-databricks-workspaces-phz repo

**Fix:**
```bash
cd core-network-databricks-workspaces-phz
# Add PHZ configuration (see Phase 4)
terraform apply
# Wait 2-3 minutes for DNS propagation
nslookup jemena-<bu>-lab.cloud.databricks.com  # Retry
```

### Issue 3: Cluster Can't Connect to Metastore

**Error:** "Cannot connect to metastore: mdnrak3rme5y1c.c5f38tyb1fdu.ap-southeast-2.rds.amazonaws.com:3306"

**Cause:** RDS metastore firewall not whitelisting workspace subnets

**Fix:**
Contact David Hunter (core-network team) to add firewall rule:
- Source: Workspace subnets (10.32.x.x/24 or 10.34.x.x/24)
- Destination: mdnrak3rme5y1c.c5f38tyb1fdu.ap-southeast-2.rds.amazonaws.com:3306
- Protocol: TCP
- SLA: 2-5 business days

### Issue 4: Users Can't See Catalog

**Error:** "Permission Denied: User cannot access catalog <bu>_lab_catalog"

**Cause:** User not member of required Entra groups

**Fix:**
1. Verify functional group: `APP-DataHub<BU>-Data-Engineer` (or Analyst, Scientist)
2. Verify classification group: `APP-DataHub<BU>-Internal` (or Confidential)
3. Verify access group membership in Unity Catalog (catalog_ro_ag or catalog_rw_ag contains functional group)
4. If missing → Request group addition via IT Portal

---

## Rollback Procedure

If deployment fails and you need to rollback:

### Rollback Layer 3 (Workspace Resources)

```bash
cd databricks-workspaces/stacks/<bu>-bu
git revert <commit-sha>
git push origin main
# CI/CD will destroy workspace resources
```

### Rollback Layer 2 (Unity Catalog)

**WARNING:** Destroying workspace is DESTRUCTIVE and requires approval

```bash
cd databricks-unity-catalog/stacks/<bu>-bu
terraform destroy -target=module.<bu>_lab_workspace
# Only if absolutely necessary - workspace binding is permanent
```

### Rollback Layer 1 (AWS Resources)

```bash
cd app-datahub-nonprod-databricks-aws-infra
git revert <commit-sha>
git push origin main
# CI/CD will destroy AWS resources (S3, IAM, SGs)
```

**CRITICAL:** Always rollback in reverse layer order (3 → 2 → 1)

---

## Contacts

**Platform Team:**
- Platform Lead: @Sampath Jagannathan
- DevOps Lead: @Jay Jiang
- Data Platform Slack: #datahub-platform

**Core-Network Team:**
- Network Lead: David Hunter (VPC/subnets/firewall)

**Security Team:**
- Firewall requests: Via ServiceNow

**Governance:**
- RBAC/Classification: @Harika Kareddy
