# FNDHAAP Operational Quick Reference Guide

Claude Code resource guide for common architecture-related tasks and decision points.

---

## 1. ADDING A NEW WORKSPACE

### Scenario: Business Unit Needs New Workspace

**Checklist**:

1. **Naming**: Determine the workspace name
   - Pattern: `{bu-name}-{lab|field}-workspace-{nonprod|prod}`
   - Examples: `digital-lab-workspace-nonprod`, `elec-network-field-workspace-prod`
   - Lab workspace: Development/testing environment
   - Field workspace: Production environment with automated pipelines

2. **Network Subnetting** (Contact: David Hunter)
   - Reserve 3 subnets (/24) in appropriate VPC (nonprod or prod)
   - One subnet per AZ (AZ1, AZ2, AZ3)
   - Total: 768 IP addresses (256 × 3 AZs)
   - Example CIDR: 10.34.110.0/24, 10.34.111.0/24, 10.34.112.0/24

3. **DNS Configuration** (Route 53 Private Hosted Zones)
   - Add entry to `core-network-databricks-workspaces-phz` GitLab repo
   - Create Private Hosted Zone for workspace address
   - Create Alias A record pointing to Frontend Private Link endpoint
   - Format:
     ```
     Zone: jemena-{bu}-{lab|field}.cloud.databricks.com
     Alias A record: → Frontend Private Link VPC Endpoint IP
     ```

4. **Terraform Stacks** (databricks-workspaces repo)
   - Create directory: `stacks/{bu}-{lab|field}-workspace-infra`
   - Create directory: `stacks/{bu}-{lab|field}-workspace-resources`
   - Create `*.tf` files calling modules from `modules/`
   - Create `{env}.auto.tfvars` files (nonprod.auto.tfvars, prod.auto.tfvars)
   - Example inputs to modules:
     ```hcl
     workspace_name = "digital-lab-workspace-nonprod"
     databricks_url = "https://dbc-xxxxx.cloud.databricks.com"
     subnet_ids = [...]  # from VPC subnet provisioning
     security_group_id = "..."  # from core-network repo
     ```

5. **Approval & Deployment**
   - Push to feature branch
   - Create MR (Merge Request)
   - Get minimum 1 approval
   - Pipeline must succeed
   - Merge to appropriate branch (main for prod-ready, dev for experimental)

6. **Verification**
   - [ ] Workspace appears in Databricks account
   - [ ] Workspace address resolves to private IP
   - [ ] Access from corporate network works
   - [ ] Access from on-prem servers works (if applicable)
   - [ ] Test cluster provisioning in workspace

---

## 2. DEBUGGING: USER CAN'T ACCESS WORKSPACE

### Troubleshooting Flowchart

```
User cannot access workspace URL
│
├─ "Cannot access workspace from public network" error?
│  └─ YES: Expected! Workspace is private-access only
│     └─ User must access from corporate network or on-prem server
│
├─ No error, but connection times out?
│  └─ Check: Is user on corporate network (with Zscaler)?
│     ├─ NO: User must be on corporate network
│     └─ YES: Continue to next check
│
├─ Check: Zscaler rule configuration
│  └─ Verify: *.cloud.databricks.com is caught and tunneled
│     └─ Contact: Security team
│
├─ Check: On-prem DNS (if accessing from on-prem)
│  └─ Verify: Conditional forwarder for *.cloud.databricks.com
│     └─ Forward destination: Route 53 Inbound Endpoint
│     └─ Contact: Jemena network team
│
├─ Check: Route 53 Private Hosted Zone
│  └─ Verify: Workspace address has PHZ entry
│     └─ Command: Check core-network-databricks-workspaces-phz repo
│     └─ Verify Alias A record points to FEPL endpoint IP
│     └─ Contact: @Wee Lih Lee / @Nikilesh Chivukula
│
├─ Check: Frontend Private Link Endpoint
│  └─ Verify: FEPL deployed in prod VPC
│     └─ AWS Console: Check VPC Endpoints in prod account
│     └─ Expected: One endpoint for all workspaces
│     └─ Contact: David Hunter
│
└─ If all checks pass: Access should work
   └─ If still failing: Contact Databricks Support
```

### Common Issues & Fixes

| Issue | Symptom | Root Cause | Fix |
|-------|---------|-----------|-----|
| DNS flipping | Alternating access success/failure | AD conditional forwarder interaction | Already mitigated with `*.cloud.databricks.com` wildcard |
| Not on corporate network | Connection times out immediately | User on guest/mobile network | Route through VPN to corporate network |
| Zscaler not configured | Workspace returns public IP | Zscaler rule not updated for workspace | Add workspace address to Zscaler rule |
| PHZ not created | Resolves to public IP | New workspace not added to Route 53 | Create PHZ entry in core-network-databricks-workspaces-phz repo |
| FEPL endpoint missing | Connection refused after DNS lookup | Frontend Private Link not deployed | Verify deployment in prod VPC (should be created once) |

---

## 3. ADDING A NEW BUSINESS UNIT

### Scenario: New Business Unit Joins Platform

**Scope**: Gas BU is new, needs infrastructure

**Step 1: Infrastructure Provisioning** (2-3 weeks)

- [ ] Meet with David Hunter for AWS requirements
- [ ] Provide VPC CIDR requirements:
  ```
  Business Unit: Gas
  Workspaces: 2 (lab + field)
  Subnets needed: 6 (3 AZs × 2 workspaces)
  Approximate CIDR range: /24 per workspace
  Total IP addresses: 1,536 (256 × 6 subnets)
  ```
- [ ] David provisions subnets in nonprod and prod VPCs
- [ ] David creates security groups for data plane isolation

**Step 2: Update Core Network Infrastructure** (1 week)

Repository: `core-network-databricks-vpc-components`

- [ ] Add security group rules for Gas BU subnets
- [ ] Document Private Link ENI IDs for Gas BU
- [ ] Create example for PR:
  ```terraform
  # main-npd-vpc-resources.tf

  # Gas BU - Backend Private Link
  resource "aws_network_interface" "databricks_scc_gas" {
    subnet_id = aws_subnet.databricks_gas_lab_az1.id
    # ... more config
  }

  resource "aws_security_group_rule" "allow_gas_to_pl" {
    security_group_id = aws_security_group.databricks_pl.id
    cidr_blocks = ["10.34.110.0/23", "10.34.112.0/23"]  # gas-lab
    # ... more config
  }
  ```

**Step 3: Create Databricks Account Resources** (2 weeks)

Repository: `databricks-unity-catalog`

- [ ] Create new stack directory: `stacks/gas-bu/`
- [ ] Copy structure from existing BU (e.g., `elec-network-bu/`):
  ```
  stacks/gas-bu/
  ├── catalogs.tf
  ├── rbac.tf
  ├── schemas/
  │   ├── data_engineering/
  │   └── data_science/
  ├── nonprod.auto.tfvars
  └── prod.auto.tfvars
  ```
- [ ] Create RBAC module instance:
  ```hcl
  # stacks/gas-bu/rbac.tf
  module "rbac" {
    source = "../../modules/rbac"

    business_unit = "gas"
    workspace_ids = {
      lab   = databricks_workspace.gas_lab.id
      field = databricks_workspace.gas_field.id
    }
    # ... more config
  }
  ```
- [ ] Create catalog structure for Gas BU

**Step 4: Create Workspace Infrastructure** (2 weeks)

Repository: `databricks-workspaces`

- [ ] Create 4 stack directories:
  ```
  stacks/gas-lab-workspace-infra/
  stacks/gas-lab-workspace-resources/
  stacks/gas-field-workspace-infra/
  stacks/gas-field-workspace-resources/
  ```
- [ ] Each directory contains:
  - `main.tf` - module calls
  - `nonprod.auto.tfvars` or `prod.auto.tfvars`
  - Optional: `outputs.tf`
- [ ] Example `gas-lab-workspace-infra/main.tf`:
  ```hcl
  module "workspace" {
    source = "../../modules/managed-workspace"

    workspace_name = "gas-lab-workspace-nonprod"
    workspace_config = {
      subnet_ids = [...]
      security_group_id = "..."
    }
  }
  ```

**Step 5: DNS & Network** (1 week)

Repository: `core-network-databricks-workspaces-phz`

- [ ] Add Private Hosted Zones for Gas workspaces:
  ```
  jemena-gas-lab.cloud.databricks.com → FEPL endpoint IP
  jemena-gas-field.cloud.databricks.com → FEPL endpoint IP
  dbc-{ws-id}.cloud.databricks.com → FEPL endpoint IP
  ```
- [ ] Push changes, merge via MR

**Step 6: Testing & Validation** (1 week)

- [ ] Verify workspace URLs resolve to private IPs
- [ ] Test access from corporate network
- [ ] Test access from on-prem servers
- [ ] Create test cluster in lab workspace
- [ ] Run sample notebook
- [ ] Verify cluster logs accessible
- [ ] Test cluster autoscaling

**Step 7: Documentation** (1 week)

- [ ] Add Gas BU to workspace access guide
- [ ] Document new subnets and security groups
- [ ] Update team wiki with onboarding steps
- [ ] Add Gas team members to appropriate AD groups

**Total Timeline**: 4-6 weeks

---

## 4. HANDLING SHARED MODULE CHANGES

### Scenario: RBAC Module Needs Enhancement

**Problem**: New permission level needed for Gas BU + existing BUs

**Approach**: Semantic Versioning

1. **Identify Impact**
   ```
   Module: databricks-unity-catalog/modules/rbac
   Current users: Electricity, Digital, Corporate BUs
   Change: Add new role type "DL_ADMIN" (data lake admin)
   Risk: Could break existing RBAC structure
   ```

2. **Code Strategy**
   ```terraform
   # modules/rbac/main.tf

   variable "additional_roles" {
     type = map(any)
     default = {}  # Allow override without breaking existing users
   }

   locals {
     all_roles = merge(
       {
         "DE_ENGINEER" = {...}
         "DS_ANALYST"  = {...}
       },
       var.additional_roles  # Custom roles can be added
     )
   }
   ```

3. **Version & Tag**
   - Create feature branch: `feature/rbac-dl-admin`
   - Make changes to module
   - Tag commit: `v2.1.0` (minor version bump)
   - Push tag to repo

4. **Update Module Source**
   ```terraform
   # Before (no version):
   module "rbac" {
     source = "../../modules/rbac"
   }

   # After (with version):
   module "rbac" {
     source = "../../modules/rbac"
     # Tag applied: v2.1.0
   }
   ```

5. **Gradual Rollout**
   - Update Gas BU first (new BU, minimal regression risk)
   - Test thoroughly in nonprod
   - Document new role in RBAC design doc
   - Update Electricity, Digital, Corporate BUs in separate MRs
   - Each BU can pin to specific version if needed

6. **Backward Compatibility Check**
   ```hcl
   # Verify existing stacks still work
   # stacks/elec-network-bu/rbac.tf should continue working
   # without changes
   ```

---

## 5. RESPONDING TO INFRASTRUCTURE OUTAGE

### Scenario: Frontend Private Link Endpoint Down

**Timeline**: 15 minutes, 1 hour, escalation

#### Immediate (0-15 minutes)

1. **Impact Assessment**
   ```
   Question: Can users access Databricks workspace?
   Answer: NO - Frontend Private Link is single point of failure

   Question: Can clusters run jobs?
   Answer: YES - Clusters use Backend Private Link (separate endpoint)

   Question: Scope: Nonprod, Prod, or both?
   Answer: Both (single FEPL for both environments)
   ```

2. **Notify Stakeholders**
   - Slack: #data-platform-incidents
   - Message: "Frontend Private Link endpoint degraded. User access blocked."

3. **Verify Endpoint Status**
   ```bash
   aws ec2 describe-vpc-endpoints \
     --vpc-endpoint-ids vpce-xxxxx \
     --region ap-southeast2 \
     --query 'VpcEndpoints[0].State'
   ```

4. **Check AWS Health Dashboard**
   - https://health.aws.amazon.com/
   - Filter: ap-southeast-2 region
   - Look for DEC2, VPC, or PrivateLink events

#### Medium Term (15-60 minutes)

5. **If AWS Issue**
   - Wait for AWS to resolve
   - Update incident status every 15 minutes
   - No action needed on our side

6. **If Our Configuration Issue**
   ```bash
   # Check endpoint configuration
   aws ec2 describe-vpc-endpoints \
     --vpc-endpoint-ids vpce-xxxxx \
     --region ap-southeast2

   # Check security groups
   aws ec2 describe-security-groups \
     --group-ids sg-xxxxx \
     --region ap-southeast2

   # Check network ACLs
   aws ec2 describe-network-acls \
     --region ap-southeast2
   ```

7. **Workaround (if long outage expected)**
   - Redirect users to public workspace access (temporary, less secure)
   - Update Zscaler rules to allow public access temporarily
   - Update Route 53 to return public IP temporarily
   - **Important**: Document this as temporary
   - **Important**: Re-enable private access after restoration

#### Escalation (>1 hour)

8. **Engage AWS Support**
   - Create critical support case
   - Reference Frontend Private Link endpoint ID
   - Provide cloudtrail logs and timing info

9. **Engage Databricks Support**
   - Reference workspace IDs
   - Provide private link endpoint details
   - Ask if there are known issues

10. **Document Post-Incident**
    - Timeline of outage
    - Root cause
    - Permanent fix
    - Prevention measures for future

---

## 6. COMMON TERRAFORM PATTERNS

### Pattern 1: Reference AWS Resource ARN from Remote State

```hcl
# In databricks-workspaces repo
# Need S3 bucket ARN from app-datahub-nonprod-databricks-aws-infra repo

data "terraform_remote_state" "aws_infra" {
  backend = "remote"
  config = {
    organization = "jemena"
    workspaces = {
      name = "app-datahub-nonprod-databricks-aws-infra"
    }
  }
}

# Now reference the S3 bucket ARN
locals {
  s3_bucket_arn = data.terraform_remote_state.aws_infra.outputs.s3_bucket_arn
}

resource "databricks_mount" "data_lake" {
  mount_point = "/mnt/data-lake"
  uri         = "s3a://${local.s3_bucket_arn}"
  # ... more config
}
```

### Pattern 2: Environment-Based Configuration

```hcl
# In stacks/{bu}/nonprod.auto.tfvars
environment = "nonprod"
workspace_url = "https://dbc-xxxxx.cloud.databricks.com"
cluster_max_workers = 5

# In stacks/{bu}/prod.auto.tfvars
environment = "prod"
workspace_url = "https://jemena-{bu}-field.cloud.databricks.com"
cluster_max_workers = 20  # Higher in prod
```

### Pattern 3: Module Variable Defaults

```hcl
# In modules/rbac/main.tf
variable "business_unit" {
  type = string
  description = "Business unit name (e.g., 'digital', 'gas')"
}

variable "roles" {
  type = map(object({
    permissions = list(string)
    description = string
  }))
  default = {
    "DE_ENGINEER" = {
      permissions = ["read", "write", "execute"]
      description = "Data engineer role"
    }
  }
}

# Stacks can override or extend defaults
module "rbac" {
  source = "../../modules/rbac"

  business_unit = "gas"
  roles = merge(
    var.roles,
    {
      "DL_ADMIN" = {
        permissions = ["admin"]
        description = "Data lake admin"
      }
    }
  )
}
```

---

## 7. GIT WORKFLOW QUICK REFERENCE

### Standard Feature Development

```bash
# 1. Create feature branch
git checkout -b feature/add-new-cluster-policy
git branch --set-upstream-to=origin/main

# 2. Make changes to terraform files
# Edit: stacks/digital-bu/cluster_policies.tf
# Edit: modules/cluster-policy/main.tf

# 3. Commit with concise message (per CLAUDE.md)
git add stacks/digital-bu/cluster_policies.tf modules/cluster-policy/main.tf
git commit -m "Add GPU cluster policy for ML workloads"

# 4. Push to remote
git push origin feature/add-new-cluster-policy

# 5. Create Merge Request (MR) in GitLab
# - Title: Add GPU cluster policy for ML workloads
# - Description: Explain why this is needed
# - Assign reviewer(s)

# 6. Wait for:
# - Minimum 1 approval
# - Pipeline to succeed

# 7. Merge (click button in GitLab)

# 8. Verify deployment
# In prod: MR merge triggers pipeline → terraform apply

# 9. Clean up local branch
git checkout main
git pull origin main
git branch -d feature/add-new-cluster-policy
```

### Revert Failed Deployment

```bash
# If deployment broke production:

# 1. Create hotfix branch
git checkout -b hotfix/revert-broken-cluster-policy

# 2. Revert the commit
git revert <commit-hash>
# (Don't use git reset --hard, use revert for tracked history)

# 3. Commit and push
git add -A
git commit -m "Revert GPU cluster policy that caused failures"
git push origin hotfix/revert-broken-cluster-policy

# 4. Create MR with URGENT tag
# - Title: [URGENT] Revert GPU cluster policy
# - Mark for immediate review

# 5. Once merged, monitor:
git log --oneline -5  # Verify revert is in history
```

---

## 8. KEY CONTACTS QUICK REFERENCE

| Need | Contact | Channel | Urgency |
|------|---------|---------|---------|
| AWS VPC/network issues | David Hunter | Slack or email | P1 |
| Firewall whitelist changes | David Hunter | Slack or email | P1 |
| Databricks design decisions | Sampath Jagannathan | Slack or email | P2 |
| Route 53 PHZ updates | @Wee Lih Lee / @Nikilesh Chivukula | MR review | P2 |
| Terraform repo governance | @Wee Lih Lee / @Nikilesh Chivukula | MR review | P2 |
| Security/Zscaler issues | Security team | Jemena IT | P1 |
| On-prem DNS issues | Jemena network team | Jemena IT | P1 |
| Databricks cluster issues | Databricks Support | Support portal | Varies |
| SSL certificate distribution | DevOps team | MR review | P2 |

---

## 9. DISASTER RECOVERY PROCEDURES

### Lost Terraform State File

**Severity**: CRITICAL

```bash
# DO NOT PANIC. State files are backed up in GitLab CI artifacts.

# 1. Check GitLab CI artifacts
# Go to: https://gitlab.com/jemena/projects/.../-/pipelines
# Find last successful terraform apply
# Download: terraform.tfstate artifact

# 2. Restore state file
cd stacks/digital-bu/
mv terraform.tfstate terraform.tfstate.corrupt
# Download artifact and place as terraform.tfstate

# 3. Verify state is valid
terraform show
# Should display all resources without errors

# 4. Test with terraform plan (read-only)
terraform plan
# Should show: "No changes. Infrastructure is up-to-date."

# 5. If plan shows differences, investigate
# This means state was out of sync with actual infrastructure
```

### Workspace Accidentally Deleted

**Severity**: HIGH

```bash
# If Databricks workspace was deleted in Terraform but actually exists:

# 1. Import existing workspace into state
terraform import databricks_workspace.digital_lab \
  <workspace-id-from-databricks-ui>

# 2. Verify import worked
terraform state show databricks_workspace.digital_lab

# 3. Commit state file
git add .terraform.lock.hcl  # Don't commit .tfstate files directly
git commit -m "Re-import accidentally deleted workspace"

# If workspace is actually deleted:
# 1. Recreate with terraform apply
# 2. Restore from Databricks backup (if available)
# 3. Notify affected teams
```

---

## 10. MONITORING & OBSERVABILITY CHECKLIST

### Daily Checks

- [ ] **Databricks Workspaces**: All 6+ workspaces accessible from corporate network
- [ ] **Clusters**: No unexpected cluster terminations overnight
- [ ] **Private Link**: FEPL endpoint healthy (AWS console)
- [ ] **DNS**: PHZ records resolving correctly
  ```bash
  nslookup jemena-digitalfield.cloud.databricks.com
  # Should return private IP (10.32.x.x)
  ```

### Weekly Checks

- [ ] **Terraform State**: No drift detected
  ```bash
  terraform plan  # Should show "No changes"
  ```
- [ ] **Security Groups**: No unexpected rule changes
- [ ] **VPC Flow Logs**: Check for blocked traffic
- [ ] **IAM Permissions**: No unused or overly-permissive roles

### Monthly Checks

- [ ] **Capacity Planning**: Monitor subnet IP usage
- [ ] **Cost Analysis**: No unexpected AWS bill spikes
- [ ] **Terraform Versions**: Check for updates
- [ ] **Databricks Releases**: New features or deprecations

---

## 11. ARCHITECTURE DECISION CHECKLIST

When designing new features, ask:

- [ ] **Isolation**: Does this change affect other BUs?
  - If yes: Use separate terraform state file
- [ ] **Reusability**: Can this be abstracted as a module?
  - If yes: Create module with semantic versioning
- [ ] **Network**: Does this need private link?
  - If yes: Coordinate with David Hunter
- [ ] **DNS**: Does this need Route 53 configuration?
  - If yes: Add to core-network-databricks-workspaces-phz repo
- [ ] **Security**: Is this subject to SSL inspection?
  - If yes: Plan certificate distribution
- [ ] **Approval**: Does this need security review?
  - If yes: Assign security team as MR reviewer
- [ ] **Testing**: Can this be tested in nonprod first?
  - If yes: Plan nonprod validation before prod deployment
- [ ] **Documentation**: Is this pattern documented for future use?
  - If yes: Update architecture documentation

---

## 12. TROUBLESHOOTING FLOWCHARTS

### Cluster Won't Start

```
Cluster fails to start
│
├─ Check CloudTrail for errors
│  └─ Error: "Security group rule limit exceeded"
│     └─ Solution: Consolidate subnets in security group rules
│
├─ Check RDS metastore connectivity
│  └─ Error: "Cannot connect to metastore"
│     └─ Solution: Verify firewall whitelist (David Hunter)
│
├─ Check instance profile permissions
│  └─ Error: "Access denied to S3"
│     └─ Solution: Verify IAM role has S3 permissions
│
└─ Check cluster configuration
   └─ Error: "Invalid subnet"
      └─ Solution: Verify subnet exists and is assigned to workspace
```

### Terraform Apply Fails

```
Terraform apply fails
│
├─ Check GitLab token permissions
│  └─ Error: "Cannot read remote state"
│     └─ Solution: Verify CI runner token has remote state read access
│
├─ Check Databricks token expiration
│  └─ Error: "Invalid authentication"
│     └─ Solution: Refresh Databricks token in GitLab variables
│
├─ Check variable values
│  └─ Error: "Invalid value for subnet_id"
│     └─ Solution: Verify *.auto.tfvars has correct subnet IDs
│
└─ Check resource conflicts
   └─ Error: "Resource already exists"
      └─ Solution: Run terraform import to reconcile state
```

---

## Final Checklist for Deployment

Before pushing to main branch:

- [ ] Changed files only: `*.tf`, `*.tfvars` (not state files)
- [ ] Terraform validates: `terraform validate` passes
- [ ] No AWS credentials in code: `grep -r "AKIA" .`
- [ ] MR title is concise (1-2 lines)
- [ ] MR description explains WHY, not just WHAT
- [ ] Reviewer assigned
- [ ] Ready for automated deployment (no manual steps)

