# Terraform Patterns Library

Complete terraform pattern examples for Jemena's Databricks platform following 5-layer architecture.

---

## Pattern 1: Remote State Consumption (DRY Principle)

**Use Case:** Passing outputs from Layer 1 (AWS infra) to Layer 2 (Unity Catalog)

### Complete Example

**Layer 1 Output Definition**

**File:** `app-datahub-nonprod-databricks-aws-infra/outputs.tf`

```hcl
output "digital_bu_lab_wks_cloud_resources" {
  description = "Cloud resources for Digital BU lab workspace"
  value = {
    workspace_root_bucket_name = module.digital_bu_lab_wks_cloud_resources.workspace_root_bucket_name
    workspace_root_bucket_arn  = module.digital_bu_lab_wks_cloud_resources.workspace_root_bucket_arn
    cross_account_role_arn     = module.digital_bu_lab_wks_cloud_resources.cross_account_role_arn
    cross_account_role_name    = module.digital_bu_lab_wks_cloud_resources.cross_account_role_name
    security_group_ids         = module.digital_bu_lab_wks_cloud_resources.security_group_ids
    instance_profile_arn       = module.digital_bu_lab_wks_cloud_resources.instance_profile_arn
    kms_key_arn                = module.digital_bu_lab_wks_cloud_resources.kms_key_arn
    kms_key_id                 = module.digital_bu_lab_wks_cloud_resources.kms_key_id
  }
  sensitive = false
}
```

**Layer 2 Remote State Consumption**

**File:** `databricks-unity-catalog/stacks/digital-bu/dependencies.tf`

```hcl
# Define remote state data source
data "terraform_remote_state" "nonprod_aws_infra" {
  backend = "http"
  config = {
    address        = "https://gitlab.jemena.com.au/api/v4/projects/12345/terraform/state/nonprod-aws-infra"
    lock_address   = "https://gitlab.jemena.com.au/api/v4/projects/12345/terraform/state/nonprod-aws-infra/lock"
    unlock_address = "https://gitlab.jemena.com.au/api/v4/projects/12345/terraform/state/nonprod-aws-infra/lock"
    username       = "gitlab-ci-token"
    password       = var.gitlab_token
  }
}

# Consume outputs in locals
locals {
  digital_bu_lab_wks_cloud_resources = data.terraform_remote_state.nonprod_aws_infra.outputs.digital_bu_lab_wks_cloud_resources

  lab_workspace_root_bucket = local.digital_bu_lab_wks_cloud_resources["workspace_root_bucket_name"]
  lab_workspace_xacc_role   = local.digital_bu_lab_wks_cloud_resources["cross_account_role_arn"]
  lab_workspace_sgs         = local.digital_bu_lab_wks_cloud_resources["security_group_ids"]
  lab_workspace_kms_key     = local.digital_bu_lab_wks_cloud_resources["kms_key_arn"]
}
```

**Layer 2 Module Usage**

**File:** `databricks-unity-catalog/stacks/digital-bu/main-workspace-lab.tf`

```hcl
# Use in module calls
module "digital_lab_workspace" {
  source = "../../modules/managed-workspace"

  workspace_name            = "digital-lab-workspace-nonprod"
  aws_region                = "ap-southeast-2"

  # Consume Layer 1 outputs
  storage_configuration_id  = local.lab_workspace_root_bucket
  credentials_id            = local.lab_workspace_xacc_role

  # Network (shared VPC from core-network)
  vpc_id                    = data.aws_vpc.shared_nonprod.id
  subnet_ids                = var.digital_lab_subnet_ids  # From core-network team
  security_group_ids        = local.lab_workspace_sgs

  # Unity Catalog binding
  metastore_id              = local.metastore_id["nonprod"]

  # Tags
  tags = {
    BusinessUnit = "Digital"
    Environment  = "lab"
    ManagedBy    = "Terraform"
  }
}
```

### WHY This Pattern?

**Benefits:**
- **DRY Principle**: S3 bucket names, IAM role ARNs defined once in Layer 1
- **Prevents Drift**: Changing bucket name in Layer 1 automatically propagates to Layer 2
- **Audit Trail**: GitLab MRs show exactly which downstream repos consume upstream outputs
- **Type Safety**: Terraform validates output structure at plan time

**Breaking Changes Cascade:**
- Renaming S3 bucket in Layer 1 breaks Layer 2 (Unity Catalog) and Layer 3 (workspaces)
- GitLab MRs show impact via state file dependencies
- Recovery: If upstream state corrupted, downstream repos cannot plan/apply until state restored

---

## Pattern 2: Module vs Stack Decision Tree

### Decision Flow

```
Need to add new Terraform resources?
         │
         ▼
    Is this a pattern
    used by multiple
    BUs/environments?
         │
    ┌────┴────┐
   YES       NO
    │         │
    │         ▼
    │    Is this specific
    │    to one BU/env?
    │         │
    │    ┌────┴────┐
    │   YES       NO
    │    │         │
    ▼    ▼         ▼
CREATE  CREATE   Inline in
MODULE  STACK    existing stack
```

### Example Decision Matrix

| Resource | Reusable? | Specific to BU? | Decision | Location |
|----------|-----------|-----------------|----------|----------|
| **Medallion schemas (landing/bronze/silver/gold)** | YES (all BUs) | NO | Module | `modules/medallion-schemas` |
| **RBAC access groups** | YES (all BUs) | NO | Module | `modules/rbac` |
| **Digital BU workspace** | NO | YES | Stack | `stacks/digital-bu` |
| **One-off security group rule** | NO | YES | Inline | In existing stack |
| **Cluster policy template** | YES (all BUs) | NO | Module | `modules/cluster-policy` |

### Module Example: Medallion Schemas

**File:** `modules/medallion-schemas/main.tf`

```hcl
# Reusable pattern for all BUs
variable "catalog_name" {
  description = "Catalog name (e.g., digital_lab_catalog)"
  type        = string
}

variable "storage_mapper" {
  description = "Map of schema names to S3 bucket names"
  type        = map(string)
}

resource "databricks_schema" "landing" {
  catalog_name = var.catalog_name
  name         = "landing"
  comment      = "Raw data ingestion layer - unprocessed files"

  storage_root = "s3://${var.storage_mapper["landing"]}/landing"

  properties = {
    kind = "landing"
  }
}

resource "databricks_schema" "bronze" {
  catalog_name = var.catalog_name
  name         = "bronze_${var.source_system}"
  comment      = "Bronze layer - raw data with metadata"

  storage_root = "s3://${var.storage_mapper["bronze"]}/bronze"

  properties = {
    kind = "bronze"
  }
}

# ... silver, gold schemas
```

### Stack Example: Digital BU Workspace

**File:** `stacks/digital-bu/main-workspace-lab.tf`

```hcl
# BU-specific instantiation of modules
module "digital_lab_medallion_schemas" {
  source = "../../modules/medallion-schemas"

  providers = {
    databricks = databricks.digital_lab
  }

  # Digital BU specific inputs
  catalog_name     = "digital_lab_catalog"
  source_system    = "salesforce"
  storage_mapper   = local.digital_lab_catalog_storage_mapper

  # Digital BU specific tags
  tags = {
    BusinessUnit = "Digital"
    Environment  = "lab"
    CostCenter   = "CC-12345"
  }
}
```

### Inline Example: One-Off Resource

**File:** `stacks/digital-bu/main-workspace-lab.tf`

```hcl
# One-off security group rule (not reusable)
resource "aws_security_group_rule" "digital_lab_allow_third_party_api" {
  type              = "egress"
  from_port         = 443
  to_port           = 443
  protocol          = "tcp"
  cidr_blocks       = ["52.63.123.45/32"]  # Third-party API specific to Digital BU
  security_group_id = local.digital_lab_workspace_sgs[0]
  description       = "Allow Digital BU to access third-party analytics API"
}
```

---

## Pattern 3: Semantic Versioning for Shared Modules

**When:** Breaking change to shared module requires coordinated migration across multiple BUs

### Step-by-Step Example: Renaming Variable in Medallion Schemas Module

#### Step 1: Tag Current Stable Version BEFORE Breaking Change

```bash
cd databricks-workspaces
git tag -a modules/medallion-schemas/v1.2.0 -m "Stable: Before catalog_name → catalog_id rename"
git push origin modules/medallion-schemas/v1.2.0
```

#### Step 2: Make Breaking Change to Module

**File:** `modules/medallion-schemas/variables.tf`

```hcl
# BEFORE (v1.2.0)
variable "catalog_name" {
  description = "Catalog name (e.g., digital_lab_catalog)"
  type        = string
}

# AFTER (v2.0.0) - BREAKING CHANGE
variable "catalog_id" {
  description = "Catalog ID from Unity Catalog (e.g., catalog-12345678-abcd-...)"
  type        = string
}
```

**File:** `modules/medallion-schemas/main.tf`

```hcl
# Update all references
resource "databricks_schema" "landing" {
  catalog_name = data.databricks_catalog.target.name  # Use data source instead
  name         = "landing"
  # ... rest of config
}

data "databricks_catalog" "target" {
  catalog_id = var.catalog_id  # NEW variable
}
```

#### Step 3: Tag New Version

```bash
git tag -a modules/medallion-schemas/v2.0.0 -m "BREAKING: Renamed catalog_name to catalog_id, added data source lookup"
git push origin modules/medallion-schemas/v2.0.0
```

#### Step 4: Update ONE Pilot BU to New Version (Test First)

**File:** `stacks/digital-bu/main-workspace-lab.tf`

```hcl
# BEFORE (v1.2.0)
module "digital_lab_medallion_schemas" {
  source = "../../modules/medallion-schemas"  # Uses latest from main branch

  catalog_name     = "digital_lab_catalog"
  storage_mapper   = local.digital_lab_catalog_storage_mapper
}

# AFTER (v2.0.0) - Pin to specific version
module "digital_lab_medallion_schemas" {
  source = "git::https://gitlab.jemena.com.au/platforms/databricks-workspaces.git//modules/medallion-schemas?ref=modules/medallion-schemas/v2.0.0"

  catalog_id       = data.terraform_remote_state.databricks_unity_catalog.outputs.digital_lab_catalog_id  # NEW variable name
  storage_mapper   = local.digital_lab_catalog_storage_mapper
}
```

#### Step 5: Test Pilot BU

```bash
cd stacks/digital-bu
terraform plan
# Verify no unexpected changes
terraform apply
# Test in Digital lab workspace
```

#### Step 6: Migrate Other BUs One-by-One with Approval

**Corporate BU Migration:**

```hcl
# File: stacks/corporate-bu/main-workspace-lab.tf
module "corporate_lab_medallion_schemas" {
  source = "git::https://gitlab.jemena.com.au/platforms/databricks-workspaces.git//modules/medallion-schemas?ref=modules/medallion-schemas/v2.0.0"

  catalog_id       = data.terraform_remote_state.databricks_unity_catalog.outputs.corporate_lab_catalog_id
  storage_mapper   = local.corporate_lab_catalog_storage_mapper
}
```

**ElecNetwork BU Migration:**

```hcl
# File: stacks/elec-network-bu/main-workspace-lab.tf
module "elec_network_lab_medallion_schemas" {
  source = "git::https://gitlab.jemena.com.au/platforms/databricks-workspaces.git//modules/medallion-schemas?ref=modules/medallion-schemas/v2.0.0"

  catalog_id       = data.terraform_remote_state.databricks_unity_catalog.outputs.elec_network_lab_catalog_id
  storage_mapper   = local.elec_network_lab_catalog_storage_mapper
}
```

### Migration Communication Template

**Subject:** [ACTION REQUIRED] Medallion Schemas Module v2.0.0 Migration - Breaking Change

**Body:**

```
Hi Platform Team,

We've released a breaking change to the medallion-schemas module (v2.0.0):

CHANGE: Renamed `catalog_name` (string) → `catalog_id` (string, requires catalog ID instead of name)

WHY: Enables data source lookup for catalog properties, prevents hardcoded names

MIGRATION STATUS:
✅ Digital BU: Migrated and tested (2025-11-18)
⏳ Corporate BU: Scheduled for 2025-11-20
⏳ ElecNetwork BU: Scheduled for 2025-11-22

ACTION REQUIRED:
- Review migration MR for your BU: [GitLab MR link]
- Approve MR by [deadline]
- Test in lab environment after deployment

ROLLBACK PLAN:
- If issues occur, revert to v1.2.0 by updating module source ref
- No data loss - only module invocation changes

SUPPORT:
- Platform Lead: @Sampath Jagannathan
- Slack: #datahub-platform

Thanks,
Platform Team
```

---

## Pattern 4: GitLab HTTP Backend Configuration

**Use Case:** Store terraform state in GitLab projects with locking support

### Backend Configuration

**File:** `backend.tf` (in each stack directory)

```hcl
terraform {
  backend "http" {
    address        = "https://gitlab.jemena.com.au/api/v4/projects/12345/terraform/state/digital-bu-nonprod"
    lock_address   = "https://gitlab.jemena.com.au/api/v4/projects/12345/terraform/state/digital-bu-nonprod/lock"
    unlock_address = "https://gitlab.jemena.com.au/api/v4/projects/12345/terraform/state/digital-bu-nonprod/lock"
    lock_method    = "POST"
    unlock_method  = "DELETE"
    username       = "gitlab-ci-token"
    password       = var.gitlab_token
  }
}
```

### Finding Project IDs

```bash
# List all projects in group
curl --header "PRIVATE-TOKEN: <your-token>" \
  "https://gitlab.jemena.com.au/api/v4/groups/platforms/projects"

# Find specific project
curl --header "PRIVATE-TOKEN: <your-token>" \
  "https://gitlab.jemena.com.au/api/v4/projects?search=databricks-unity-catalog"
```

### State File Naming Convention

```
Format: {bu}-bu-{environment}

Examples:
- digital-bu-nonprod
- digital-bu-prod
- corporate-bu-nonprod
- elec-network-bu-prod
```

---

## Pattern 5: Cross-Layer Dependencies with Conditional Logic

**Use Case:** Consume different state files depending on environment

### Environment-Aware Remote State

**File:** `databricks-workspaces/stacks/digital-bu/upstream_stacks.tf`

```hcl
locals {
  # Map environment to AWS account
  aws_account_project_id = {
    nonprod = "12345"  # app-datahub-nonprod-databricks-aws-infra
    prod    = "67890"  # app-datahub-prod-databricks-aws-infra
  }

  # Map environment to state file name
  aws_infra_state_name = {
    nonprod = "nonprod-aws-infra"
    prod    = "prod-aws-infra"
  }
}

# Dynamically consume correct state based on environment
data "terraform_remote_state" "aws_infra" {
  backend = "http"
  config = {
    address = "https://gitlab.jemena.com.au/api/v4/projects/${local.aws_account_project_id[var.environment]}/terraform/state/${local.aws_infra_state_name[var.environment]}"
    # ... lock addresses
  }
}

# Use in locals
locals {
  digital_lab_wks_cloud_resources = var.environment == "nonprod" ?
    data.terraform_remote_state.aws_infra.outputs.digital_bu_lab_wks_cloud_resources :
    null

  digital_field_wks_cloud_resources = var.environment == "prod" ?
    data.terraform_remote_state.aws_infra.outputs.digital_bu_field_wks_cloud_resources :
    null
}
```

### Environment Injection via *.auto.tfvars

**File:** `databricks-workspaces/stacks/digital-bu/nonprod.auto.tfvars`

```hcl
environment = "nonprod"
aws_account_id = "851725449831"
aws_region = "ap-southeast-2"

# Nonprod-specific configs
databricks_account_id = "nonprod-databricks-account-id"
metastore_id = "metastore-12345678-abcd-1234-efgh-123456789012"
```

**File:** `databricks-workspaces/stacks/digital-bu/prod.auto.tfvars`

```hcl
environment = "prod"
aws_account_id = "339712836516"
aws_region = "ap-southeast-2"

# Prod-specific configs
databricks_account_id = "prod-databricks-account-id"
metastore_id = "metastore-87654321-dcba-4321-hgfe-210987654321"
```

---

## Pattern 6: Module Outputs for State Exposure

**Use Case:** Expose module outputs for downstream consumption

### Module Output Definition

**File:** `modules/workspace-cloud-resources/outputs.tf`

```hcl
output "workspace_root_bucket_name" {
  description = "S3 bucket name for workspace root storage"
  value       = aws_s3_bucket.workspace_root.bucket
}

output "workspace_root_bucket_arn" {
  description = "S3 bucket ARN for IAM policies"
  value       = aws_s3_bucket.workspace_root.arn
}

output "cross_account_role_arn" {
  description = "IAM role ARN for Databricks cross-account access"
  value       = aws_iam_role.cross_account.arn
}

output "security_group_ids" {
  description = "List of security group IDs for workspace"
  value       = [aws_security_group.workspace.id]
}

output "instance_profile_arn" {
  description = "Instance profile ARN for cluster IAM"
  value       = aws_iam_instance_profile.cluster.arn
}

output "kms_key_arn" {
  description = "KMS key ARN for encryption"
  value       = aws_kms_key.workspace.arn
}
```

### Stack Output Passthrough

**File:** `app-datahub-nonprod-databricks-aws-infra/outputs.tf`

```hcl
# Pass through module outputs as structured map
output "digital_bu_lab_wks_cloud_resources" {
  description = "All cloud resources for Digital BU lab workspace"
  value = {
    workspace_root_bucket_name = module.digital_bu_lab_wks_cloud_resources.workspace_root_bucket_name
    workspace_root_bucket_arn  = module.digital_bu_lab_wks_cloud_resources.workspace_root_bucket_arn
    cross_account_role_arn     = module.digital_bu_lab_wks_cloud_resources.cross_account_role_arn
    security_group_ids         = module.digital_bu_lab_wks_cloud_resources.security_group_ids
    instance_profile_arn       = module.digital_bu_lab_wks_cloud_resources.instance_profile_arn
    kms_key_arn                = module.digital_bu_lab_wks_cloud_resources.kms_key_arn
  }
  sensitive = false
}
```

---

## Pattern 7: Terraform Workspaces vs Stack Directories

**Jemena Pattern:** One terraform state per stack directory (NOT using terraform workspaces)

### WHY NOT Terraform Workspaces?

**Terraform Workspaces Pattern (NOT USED):**
```bash
# Single directory, multiple state files via workspaces
cd stacks/digital-bu
terraform workspace new nonprod
terraform workspace new prod
terraform workspace select nonprod
terraform apply
```

**Problems:**
- Easy to accidentally apply to wrong workspace
- State files share same backend configuration
- Difficult to see which workspace you're in
- Risky for production vs nonprod separation

### Jemena Pattern: Stack Directories (USED)

**Directory Structure:**
```
databricks-unity-catalog/
├─ stacks/
│  ├─ digital-bu/           # One state file per stack
│  │  ├─ backend.tf         # Unique GitLab project + state name
│  │  ├─ main.tf
│  │  ├─ nonprod.auto.tfvars  # Environment injection
│  │  └─ prod.auto.tfvars
│  ├─ corporate-bu/         # Separate state file
│  │  ├─ backend.tf
│  │  ├─ main.tf
│  │  └─ *.auto.tfvars
│  └─ elec-network-bu/      # Separate state file
│     ├─ backend.tf
│     ├─ main.tf
│     └─ *.auto.tfvars
```

**Benefits:**
- Explicit directory = explicit state file
- Blast radius isolation (changes to Digital BU don't affect Corporate BU)
- Clear separation in GitLab CI/CD pipelines
- Easy to see which stack you're working on

---

## Pattern 8: Data Sources for Cross-Account Resource References

**Use Case:** Reference resources in core-network account from app-datahub account

### VPC Data Source

**File:** `app-datahub-nonprod-databricks-aws-infra/data.tf`

```hcl
# Reference shared VPC (owned by core-network account)
data "aws_vpc" "shared_nonprod" {
  filter {
    name   = "tag:Name"
    values = ["core-network-shared-nonprod-vpc"]
  }
}

# Reference VPC CIDR for security group rules
data "aws_vpc" "shared_nonprod_cidr" {
  id = data.aws_vpc.shared_nonprod.id
}

# Use in locals
locals {
  shared_vpc_id   = data.aws_vpc.shared_nonprod.id
  shared_vpc_cidr = data.aws_vpc.shared_nonprod.cidr_block  # 10.34.0.0/16
}
```

### Subnet Data Source (Shared via AWS RAM)

```hcl
# Reference subnet by ID (provided by core-network team)
data "aws_subnet" "databricks_az1" {
  id = "subnet-039d49c832c613766"
}

# OR reference by tag
data "aws_subnet" "databricks_az1_by_tag" {
  filter {
    name   = "tag:Name"
    values = ["appdatahub-devprivateaz1-02"]
  }
}

# Use in workspace module
module "digital_bu_lab_wks_cloud_resources" {
  source = "./modules/workspace-cloud-resources"

  subnet_ids = [
    data.aws_subnet.databricks_az1.id,
    data.aws_subnet.databricks_az2.id,
    data.aws_subnet.databricks_az3.id
  ]
}
```

### VPC Endpoint Data Source (Private Link)

```hcl
# Reference FEPL endpoint (created in core-network account)
data "aws_vpc_endpoint" "fepl" {
  filter {
    name   = "tag:Name"
    values = ["databricks-fepl-prod"]
  }
}

# Use DNS entries for Route 53 alias records
locals {
  fepl_dns_name    = data.aws_vpc_endpoint.fepl.dns_entry[0].dns_name
  fepl_hosted_zone = data.aws_vpc_endpoint.fepl.dns_entry[0].hosted_zone_id
}
```

---

## Pattern 9: Authentication Methods (GitLab CI/CD)

**Use Case:** Understanding authentication patterns across different terraform providers

### Overview

Jemena's platform uses **different authentication methods** depending on the target platform (AWS vs Databricks). Understanding which method is used helps with troubleshooting CI/CD pipeline failures.

### Authentication by Provider

#### AWS Provider Authentication (Layer 1 Repos)

**Repositories:**
- `app-datahub-prod-databricks-aws-infra`
- `app-datahub-nonprod-databricks-aws-infra`
- `core-network-databricks-vpc-components`
- `datamesh-manager-prod`
- `network-model-ewb-prod`

**Method:** GitLab OIDC (OpenID Connect) - Keyless AWS authentication

**How it works:**
```yaml
# .gitlab-ci.yml
id_tokens:
  GITLAB_OIDC_TOKEN:
    aud: https://gitlab.com

image: registry.gitlab.com/jemena/container-registry/tf-aws-oidc-gitlab:stable

before_script:
  - oidc-session.sh  # Exchanges GitLab JWT for temporary AWS credentials
```

**Credentials:** Temporary (1-hour session tokens), no static AWS keys stored

---

#### Databricks Provider Authentication (Layer 2-3 Repos)

**Repositories:**
- `databricks-unity-catalog`
- `databricks-workspaces`
- `databricks-app-code-digital-analytics` (DABs deployment)
- `databricks-app-code-nri` (DABs deployment)

**Method:** Databricks Service Principal OAuth (M2M)

**How it works:**
```yaml
# .gitlab-ci.yml (Unity Catalog example)
id_tokens:
  GITLAB_OIDC_TOKEN:
    aud: https://gitlab.com  # Used for GitLab HTTP backend only

image: hashicorp/terraform:latest

variables:
  DATABRICKS_HOST: "https://accounts.cloud.databricks.com"
  DATABRICKS_ACCOUNT_ID: "12345678-abcd-1234-abcd-1234567890ab"
  DATABRICKS_CLIENT_ID: "${DATABRICKS_SERVICE_PRINCIPAL_CLIENT_ID}"     # GitLab variable
  DATABRICKS_CLIENT_SECRET: "${DATABRICKS_SERVICE_PRINCIPAL_SECRET}"    # GitLab variable
```

**Credentials:** Static service principal credentials stored in GitLab group variables

**WHY NOT AWS OIDC:** Databricks provider doesn't support AWS authentication - it uses Databricks-native OAuth

---

#### GitLab HTTP Backend Authentication (All Repos)

**Method:** GitLab CI token (`gitlab-ci-token`)

**How it works:**
```hcl
# backend.tf
terraform {
  backend "http" {
    address        = "https://gitlab.jemena.com.au/api/v4/projects/12345/terraform/state/stack-name"
    lock_address   = "https://gitlab.jemena.com.au/api/v4/projects/12345/terraform/state/stack-name/lock"
    unlock_address = "https://gitlab.jemena.com.au/api/v4/projects/12345/terraform/state/stack-name/lock"
    username       = "gitlab-ci-token"
    password       = var.gitlab_token  # CI_JOB_TOKEN from GitLab
  }
}
```

**Credentials:** Ephemeral job token (auto-generated per pipeline run)

---

### Authentication Pattern Summary

| Layer | Target Platform | Provider | Auth Method | Credential Storage |
|-------|----------------|----------|-------------|-------------------|
| **Layer 1** | AWS | aws | GitLab OIDC | None (keyless) |
| **Layer 2** | Databricks Account | databricks | Service Principal OAuth | GitLab variables (static) |
| **Layer 3** | Databricks Workspaces | databricks | Service Principal OAuth | GitLab variables (static) |
| **Layer 4** | Databricks Jobs (DABs) | databricks (CLI) | Service Principal OAuth | GitLab variables (static) |
| **All Layers** | Terraform State | http (GitLab) | gitlab-ci-token | Auto-generated per job |

### Key Takeaways

1. **AWS resources (S3, IAM, KMS):** Use OIDC (keyless authentication)
2. **Databricks resources (catalogs, workspaces, schemas):** Use static service principal credentials
3. **Terraform state (all repos):** Use ephemeral GitLab job tokens
4. **OIDC token declaration in Databricks repos:** Used for GitLab HTTP backend authentication, NOT for Databricks provider

### Troubleshooting Authentication Issues

**Issue: AWS provider fails with "Access Denied"**
- **Likely cause:** OIDC session setup failed, `oidc-session.sh` not run
- **Check:** Pipeline logs for `oidc-session.sh` execution
- **Verify:** Custom container image being used (`tf-aws-oidc-gitlab:stable`)

**Issue: Databricks provider fails with "Authentication failed"**
- **Likely cause:** Service principal credentials expired or incorrect
- **Check:** GitLab group variables: `DATABRICKS_CLIENT_ID`, `DATABRICKS_CLIENT_SECRET`
- **Verify:** Service principal exists in Databricks account and has correct permissions

**Issue: Terraform state backend fails with "Unauthorized"**
- **Likely cause:** CI_JOB_TOKEN doesn't have access to project
- **Check:** Project membership, access tokens, repository visibility
- **Verify:** `username = "gitlab-ci-token"` and `password = var.gitlab_token` in backend config

---

## References

- Terraform Remote State Data Sources: https://www.terraform.io/language/state/remote-state-data
- Semantic Versioning: https://semver.org/
- GitLab Terraform HTTP Backend: https://docs.gitlab.com/ee/user/infrastructure/iac/terraform_state.html
- AWS RAM Resource Sharing: https://docs.aws.amazon.com/ram/latest/userguide/what-is.html
