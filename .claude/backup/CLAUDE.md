- **Git workflow**: Never push directly to `main` or `dev` branches. Always create a feature branch, commit changes there, push the branch, and create a merge/pull request for review.

## Data Platform Architecture

### Platform Overview
Jemena's data platform follows a **5-layer architecture** with strict dependency ordering. Each repository manages a distinct layer, and **state file outputs** from upstream repos are consumed by downstream repos via Terraform remote state.

### Network Architecture WHY

**Shared VPC Model** (owned by core-network account 234268347951):
- **WHY Shared**: One VPC serves multiple application accounts. Reduces TGW attachment costs, simplifies routing, centralizes IP management.
- **Prod VPC**: 10.32.0.0/16 (core-network-shared-prod-vpc)
- **Nonprod VPC**: 10.34.0.0/16 (core-network-shared-nonprod-vpc)
- **DMZ VPC**: 10.36.0.0/16 (core-network-shared-dmz-vpc)

**Centralized Inspection**:
- **WHY**: All inter-VPC traffic MUST traverse Palo Alto firewalls in core-security account (484357440923).
- **Pattern**: Workload → Transit Gateway → core-security-fw-vpc → Palo Alto → destination
- **Impact**: Cross-BU communication requires explicit firewall rules.

**Centralized Endpoints**:
- **WHY**: PrivateLink endpoints (RDS, KMS, S3, SSM) centralized in core-network account prevent per-account duplication.
- **Pattern**: Separate endpoints for prod/nonprod to avoid tromboning through security VPC.

**Subnet Allocation for Databricks**:
- **app-datahub-prod**: 10.32.78.0/27 - 10.32.103.0/24 (3 subnets per workspace across 3 AZs)
- **app-datahub-nonprod**: Equivalent range in 10.34.0.0/16
- **WHY 3 subnets per workspace**: ENI subnet (/27), DB subnet (/27), Private/workload subnet (/24)

**Critical Constraint**: Application accounts (app-datahub-prod, app-datahub-nonprod) do NOT own VPCs. Subnets are shared via AWS RAM. Networking changes require core-network team approval.

### Repository Layers & Purpose

#### Layer 1: AWS Cloud Resources (Foundation)
- **`app-datahub-prod-databricks-aws-infra/`** - Prod AWS account (339712836516) resources
- **`nonprod/app-datahub-nonprod-databricks-aws-infra/`** - Nonprod AWS account (851725449831) resources
- **`core-network-databricks-vpc-components/`** - Shared VPC endpoints, security groups in core-network account

**Purpose**: Provision AWS infrastructure (S3 buckets, IAM roles, KMS keys, security groups) + VPC networking components.

**Critical Pattern**: Each BU has lab (dev/qa) and field (prod) workspace + catalog resources with medallion architecture (landing, bronze, silver, gold).

#### Layer 2: Databricks Account Resources (Unity Catalog)
- **`databricks-unity-catalog/`** - Account-level Databricks resources

**Purpose**: Provision Databricks account-level infrastructure (metastore, catalogs, storage credentials, RBAC groups).

**Dependencies**: Consumes AWS infra state for S3 buckets, IAM roles, VPC endpoints.

**Unity Catalog Design Philosophy**:
- **WHY Centralized Metastore**: Single source of truth for all workspaces across all BUs. Enables cross-BU data sharing and centralized audit logs.
- **WHY Stage Distinction at Catalog Level** (NOT metastore): Allows granular lab→field promotion without metastore-level complexity.
- **WHY Catalog-per-BU-per-Environment**: Blast radius isolation (changes to digital_lab don't impact corporate_field). Cost attribution via S3 bucket tagging.
- **WHY Shared Metastore S3 Backend**: Renaming `app-datahub-{env}-s3-acc-metastore` bucket breaks ALL workspace bindings across ALL BUs.

**Stacks**: Organized by BU (`digital-bu/`, `corporate-bu/`, `elec-network-bu/`) with prod/nonprod separation.

#### Layer 3: Databricks Workspace Resources
- **`databricks-workspaces/`** - Workspace-level Databricks resources

**Purpose**: Configure workspace-specific resources (schemas, clusters, grants, SQL warehouses, instance profiles).

**Dependencies**: Consumes state from AWS infra (S3, IAM, KMS) + Unity Catalog (catalog IDs, metastore, storage credentials).

**Critical Patterns**:
- **Medallion schemas**: landing → bronze → silver → gold with volumes and external locations
- **Init scripts MANDATORY**: Clusters require CA certs, DNS config (BEPL), in-memory metastore. Without these, clusters fail to connect to internal systems.
- **Service Principal OAuth M2M**: CI/CD auth pattern (not password-based)
- **Enhanced grants**: RBAC on schemas/tables based on persona groups (engineers, analysts, scientists, viewers)

#### Layer 4: Data Products (Application Code)
- **`databricks-app-code-digital-analytics/`** - Digital Analytics data product
- **`databricks-app-code-nri/`** - Network Reliability & Intelligence data product

**Purpose**: Implement data pipelines, dbt models, and Databricks jobs deployed via **Databricks Asset Bundles (DABs)**.

**Dependencies**: Requires provisioned workspaces from Layer 3.

**Deployment Pattern**:
- **lab target**: Development mode (auto-prefixed with `[dev username]`, schedules disabled)
- **field target**: Production mode (scheduled jobs, alerts, full governance)
- Deployed via GitLab CI/CD using `databricks bundle deploy -t <target>`

#### Layer 5: Governance Applications
- **`datamesh-manager-prod/`** - Data Mesh Manager (DMM) governance platform
- **`network-model-ewb-prod/`** - Energy Workbench network modeling application

**Purpose**: Provide governance, metadata management, and domain-specific applications.

**Infrastructure**: ECS Fargate services with ALB, RDS PostgreSQL, cross-account DNS via AssumeRole.

### Deployment Order WHY

**NEVER deploy out of order. Dependencies MUST be satisfied first.**

```
1. AWS Cloud Resources (app-datahub-*-databricks-aws-infra)
       ↓ (outputs: S3 buckets, IAM roles, KMS keys, security groups)
2. Unity Catalog (databricks-unity-catalog)
       ↓ (outputs: metastore ID, catalog IDs, storage credentials)
3. Workspaces (databricks-workspaces)
       ↓ (outputs: workspace configs, cluster policies, schemas)
4. Data Products (databricks-app-code-*)
       ↓ (deployed as DABs to workspaces)
5. Governance Apps (datamesh-manager-*, network-model-*)
```

**WHY Deployment Order is Immutable**:
- **Metastore binding**: Once a workspace binds to a metastore (Layer 2), it CANNOT be rebound without destroying the workspace.
- **IAM role ARNs**: Workspace creation requires cross-account role ARN from Layer 1. If role doesn't exist, workspace creation fails.
- **Catalog storage**: External locations require S3 buckets + storage credentials. If bucket doesn't exist, catalog creation fails.
- **Blast Radius**: Deploying Layer 3 before Layer 2 = workspaces fail to bind. Deploying Layer 2 before Layer 1 = "S3 bucket not found" errors.

### State File Coupling WHY

**GitLab HTTP Backend Pattern**:
- All state stored in GitLab projects (identified by project IDs in `backend.tf`)
- Output consumption via `terraform_remote_state` in `dependencies.tf` or `upstream_stacks.tf`
- **WHY This Coupling**: DRY principle - resource names/ARNs defined once, consumed downstream. Prevents drift from hardcoded values.

**Breaking Changes Cascade**:
- Renaming S3 bucket in Layer 1 breaks Layer 2 (UC) and Layer 3 (workspaces)
- Audit trail: GitLab MRs show exactly which downstream repos need updates
- Recovery: If upstream state corrupted, downstream repos cannot plan/apply until state restored

### Environment Patterns

#### Nonprod AWS Account (851725449831)
- **Purpose**: Platform testing and development **before** production deployment
- **Workspaces**: digital-lab, corporate-lab, elec-network-lab, sparky-lab (dev/qa environments)
- **Users**: Platform engineers only (no business users)
- **Pattern**: Changes tested here first, then promoted to prod
- **Unique Resources**: Athena cross-account queries, Sparky BU (testing only)

#### Prod AWS Account (339712836516)
- **Purpose**: Production workloads with business users
- **Workspaces**: digital-field, corporate-field, elec-network-field (production environments)
- **Users**: Data engineers, analysts, scientists actively building pipelines
- **Pattern**: Changes deployed only after nonprod validation

**Critical Insight**: When modifying platform infrastructure (AWS resources, Unity Catalog, workspaces), **ALWAYS deploy to nonprod first**, validate, then deploy to prod. Data product code (dbt, jobs) follows same pattern (lab → field).

### Security Patterns

#### Encryption
- **KMS Keys**: Separate customer-managed keys per BU (digital, corporate, elec-network) + shared metastore key
- **S3 Encryption**: All buckets encrypted with KMS (SSE-KMS)
- **TLS**: ALBs enforce TLS 1.3 (`ELBSecurityPolicy-TLS13-1-2-2021-06`)

#### IAM & Cross-Account Access
- **External ID Validation**: All cross-account assume roles use Databricks account ID as external ID
- **Least Privilege**: IAM policies scoped to specific resources (bucket ARNs, VPC constraints)
- **Instance Profiles**: Workspace clusters attach profiles for S3/catalog access
- **Service Principal Auth**: CI/CD uses SP OAuth tokens (stored in GitLab secrets)

#### Secrets Management
- **AWS Secrets Manager**: Database credentials, OAuth tokens, certificates
- **GitLab Group Variables**: Service principal credentials (synced from Databricks)
- **Parameter Store**: Application configs (`/service/network-model-ewb/*`)

#### Network Security
- **Security Groups**: Explicit egress rules for Databricks control plane, databases, APIs
- **VPC Endpoints**: Private connectivity (REST, SCC relay, FEPL) for Databricks
- **Cross-Account DNS**: Route53 private hosted zones managed via AssumeRole to core-network account

### Key Architectural Insights

1. **Core Network Dependency**: `core-network-databricks-vpc-components` is foundational for ALL private connectivity. Changes here cascade to all workspaces.

2. **Data Layer Separation**: `network-model-datastores` separates data persistence from compute (allows independent scaling/upgrades).

3. **Module Reusability**: Shared modules (`bucket`, `workspace-cloud-resources`, `catalog-cloud-resources`, `medallion-schemas`, `enhanced-grants`) enforce consistency.

4. **Multi-BU Isolation**: Business units (Digital, Corporate, Elec-Network) have isolated workspaces and catalogs with selective cross-BU read-only bindings.

5. **CI/CD Governance**: GitLab pipelines enforce terraform plan → governance checks (Checkov, OPA) → manual approval → apply.

## Using MCP servers
- Documentation memory bank lives under the `docs/` folder.
  - Each repo mirrors its name under `docs/<repository-name>`; from the repo root, `cd docs/<repository-name>`. For example, `docs/app-datahub-prod-databricks-aws-infra`).
  - If a mirror folder is missing, inspect `docs/` for the closest match or ask for clarification before proceeding.
- Generate diagrams with the `aws-diagram` MCP tool.
  - Supply the current repository as `workspace_dir`, store the output in `docs/generated-diagrams/<descriptive-name>.png`, and then use `open` on that path to review the image.
- Choose Cost Explorer MCP when you need lightweight analytics or forecasts, want to minimize IAM blast radius, and expect to work only with Cost Explorer data (e.g., finance teams triaging monthly deltas, engineers checking one service’s spike).
- Choose Billing & Cost Management MCP when you need an end-to-end FinOps cockpit—budgets, anomaly hunting, optimization recommendations, Free Tier tracking, savings-plans guidance, Storage Lens queries—or when you’d otherwise have to orchestrate several MCP servers for the same analysis pipeline.
