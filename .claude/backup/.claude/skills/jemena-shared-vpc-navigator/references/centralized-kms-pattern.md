# Centralized KMS Key Management Pattern

## Purpose

Document Jemena's centralized KMS key management pattern where ALL encryption keys are provisioned in the core-security account (484357440923) and shared cross-account to application accounts.

**Critical Understanding:** Application teams CANNOT create KMS keys - they must request them from the Platform Team.

---

## The Pattern: 100% Centralized

### Account Ownership

**ALL KMS keys are created in:**
- **Account**: 484357440923 (core-security)
- **Region**: ap-southeast-2
- **Management**: Platform Team / David Hunter

**Application accounts REFERENCE keys:**
- app-datahub-prod (339712836516)
- app-datahub-nonprod (851725449831)

---

## Why This Pattern?

1. **Central Governance**: Platform team controls all encryption keys across all environments
2. **Security**: Keys cannot be deleted or rotated by application teams
3. **Compliance**: Centralized audit trail for ALL encryption operations
4. **Key Rotation**: Platform team can rotate keys without app team involvement
5. **Consistency**: Same pattern across Databricks platform AND applications (DMM, EWB)

---

## Evidence Across Platform

### Databricks Platform Keys

**Digital BU:**
- ARN: `arn:aws:kms:ap-southeast-2:484357440923:key/59716705-1cfb-4a54-9a5e-cb71fa51c368`
- File: `app-datahub-prod-databricks-aws-infra/prod.auto.tfvars`
- Usage: Workspace buckets, catalog storage, cluster encryption

**Corporate BU:**
- Pattern: Same core-security account
- Variable: `var.corporate_kms_key_arn`

**Elec-Network BU:**
- Pattern: Same core-security account
- Variable: `var.elec_network_kms_key_arn`

**Shared Metastore:**
- Pattern: Same core-security account
- Variable: `var.shared_metastore_kms_arn`

### Application Keys

**Data Mesh Manager Prod:**
- ARN: `arn:aws:kms:ap-southeast-2:484357440923:key/14fe3e9e-8485-4ee8-9bf0-5ae8beafaa8e`
- Alias: `app-datahub-prod-datamesh-manager-kms-key`
- File: `datamesh-manager-prod/prod.auto.tfvars:14`
- Usage: RDS encryption, ECS logs, Secrets Manager

**Data Mesh Manager Nonprod:**
- ARN: `arn:aws:kms:ap-southeast-2:484357440923:key/efc68366-58ec-4fc0-b423-fed6de15570f`
- File: `datamesh-manager-nonprod/nonprod.auto.tfvars:15`
- Usage: RDS encryption, ECS logs, Secrets Manager

**Energy Workbench / Datastores:**
- ARN: `arn:aws:kms:ap-southeast-2:484357440923:alias/app-datahub-prod-ewb-kms-key`
- File: `network-model-ewb-prod/variables.tf:23`
- Usage: S3 model cache, RDS Aurora, SSM parameters

---

## How to Request a KMS Key

### For New Applications

**When:** New application deployment requires encryption (RDS, S3, Secrets Manager, ECS logs)

**Contact:** Platform Team / David Hunter
- Email: platform-team@jemena.com.au
- Slack: #datahub-platform

**Request Template:**
```
Subject: Request [Prod|Nonprod] KMS Key for [Application Name]

Account: [339712836516 (prod) or 851725449831 (nonprod)]
VPC: [vpc-id]
Application: [name]
Purpose: Encrypt [RDS, ECS logs, Secrets Manager, S3]

Required Permissions:
- Allow [application account root] to use key
- Grant operations: Decrypt, Encrypt, GenerateDataKey, CreateGrant, DescribeKey
- Allow [specify AWS services]: rds.amazonaws.com, logs.amazonaws.com, etc.

Required by: [date]
```

### For New Databricks Workspace

**When:** Adding new business unit or workspace

**Contact:** Platform Team (Sampath Jagannathan)
- Slack: #datahub-platform

**Note:** KMS keys for Databricks workspaces are provisioned as part of BU onboarding (see `databricks-platform-operations` skill: Adding New BU - 7-phase timeline)

---

## Terraform Usage Pattern

### Step 1: Key ARN Provided by Platform Team

After platform team creates the key, they provide the ARN:
```
arn:aws:kms:ap-southeast-2:484357440923:key/[key-id]
```

### Step 2: Add to tfvars

```hcl
# prod.auto.tfvars
kms_key_arn = "arn:aws:kms:ap-southeast-2:484357440923:key/14fe3e9e-..."
```

### Step 3: Reference as Data Source

```hcl
# data-aws-kms-key.tf
data "aws_kms_key" "app_key" {
  key_id = var.kms_key_arn
}
```

### Step 4: Use in Resources

```hcl
# RDS
resource "aws_db_instance" "main" {
  kms_key_id = data.aws_kms_key.app_key.arn
  # ...
}

# S3
resource "aws_s3_bucket_server_side_encryption_configuration" "main" {
  bucket = aws_s3_bucket.main.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = data.aws_kms_key.app_key.arn
    }
  }
}

# CloudWatch Logs
resource "aws_cloudwatch_log_group" "ecs" {
  kms_key_id = data.aws_kms_key.app_key.arn
  # ...
}
```

### Step 5: IAM Permissions

Grant your application IAM roles permission to use the key:

```hcl
# IAM policy for ECS task role
data "aws_iam_policy_document" "ecs_task" {
  statement {
    effect = "Allow"
    actions = [
      "kms:Decrypt",
      "kms:Encrypt",
      "kms:GenerateDataKey",
      "kms:DescribeKey"
    ]
    resources = [data.aws_kms_key.app_key.arn]
  }
}
```

---

## Cross-Account Trust Model

### How It Works

```
Core-Security Account (484357440923)
  │
  └─→ KMS Key (customer-managed)
      │
      ├─→ Key Policy GRANTS access to:
      │   arn:aws:iam::[app-account-id]:root
      │
      │   Allowed Operations:
      │   - Decrypt
      │   - Encrypt
      │   - GenerateDataKey
      │   - CreateGrant (for RDS/ECS services)
      │   - DescribeKey
      │
      └─→ Service-Specific GRANTS:
          - rds.ap-southeast-2.amazonaws.com
          - logs.ap-southeast-2.amazonaws.com
```

### Key Policy Example

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "Allow app account to use key",
      "Effect": "Allow",
      "Principal": {
        "AWS": "arn:aws:iam::339712836516:root"
      },
      "Action": [
        "kms:Decrypt",
        "kms:Encrypt",
        "kms:GenerateDataKey",
        "kms:CreateGrant",
        "kms:DescribeKey"
      ],
      "Resource": "*"
    },
    {
      "Sid": "Allow RDS to use key",
      "Effect": "Allow",
      "Principal": {
        "Service": "rds.amazonaws.com"
      },
      "Action": [
        "kms:Decrypt",
        "kms:CreateGrant"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "kms:ViaService": "rds.ap-southeast-2.amazonaws.com"
        }
      }
    }
  ]
}
```

---

## What You CANNOT Do

❌ Create KMS keys in app-datahub accounts
❌ Delete KMS keys (even if you're the creator)
❌ Modify key policies
❌ Rotate keys manually
❌ Create KMS key aliases in app accounts

**All of these actions are managed by the Platform Team in the core-security account.**

---

## What You CAN Do

✅ Reference existing KMS keys via ARN
✅ Use keys for encryption (RDS, S3, Secrets Manager, CloudWatch)
✅ Grant IAM permissions to use keys
✅ Request new keys from Platform Team
✅ Verify key access via AWS CLI: `aws kms describe-key --key-id [arn]`

---

## Troubleshooting

### Error: "AccessDenied: User is not authorized to perform: kms:Decrypt"

**Cause:** IAM role lacks permission to use the KMS key

**Fix:**
1. Verify IAM policy includes `kms:Decrypt` on the key ARN
2. Check key policy in core-security account grants access to your app account root
3. Verify key ARN is correct in your terraform

**Test:**
```bash
aws kms decrypt --key-id [arn] --ciphertext-blob [test-value]
```

---

### Error: "KMS key not found"

**Cause:** Key ARN incorrect or doesn't exist

**Fix:**
1. Verify ARN format: `arn:aws:kms:ap-southeast-2:484357440923:key/[uuid]`
2. Check with Platform Team if key exists
3. Ensure you're in correct region (ap-southeast-2)

**Test:**
```bash
aws kms describe-key --key-id [arn]
```

---

### Error: "Cannot create grant for cross-account key"

**Cause:** Key policy doesn't allow `kms:CreateGrant` operation

**Fix:**
1. Contact Platform Team to update key policy
2. RDS and ECS services require `CreateGrant` permission
3. Provide service principal that needs the grant (e.g., `rds.amazonaws.com`)

---

## SLA & Timeline

**New KMS Key Request:**
- Contact: Platform Team (platform-team@jemena.com.au)
- SLA: 2-5 business days (for new applications)
- SLA: Included in BU onboarding (for Databricks workspaces)

**Key Policy Updates:**
- Contact: Platform Team
- SLA: 1-2 business days

**Emergency Key Access Issues:**
- Escalate to: Platform Lead (Sampath Jagannathan)
- Priority: CRITICAL (blocks deployment)

---

## Real-World Examples

### Example 1: Data Mesh Manager Production

**Request sent:** 2024-07-05
**Key provided:** 2024-07-09 (4 business days)
**Key ID:** `14fe3e9e-8485-4ee8-9bf0-5ae8beafaa8e`
**Alias:** `app-datahub-prod-datamesh-manager-kms-key`

**Documentation:** `docs/datamesh-manager-prod/fleeting/datamesh-manager-production-improvement-deployments.md` lines 79-98

### Example 2: Network Model EWB

**Key Alias:** `app-datahub-prod-ewb-kms-key`
**Usage:** Shared across EWB and Datastores repos
**Pattern:** Alias reference allows key rotation without code changes

---

## Best Practices

1. **Use Aliases When Possible:**
   - Alias: `arn:aws:kms:ap-southeast-2:484357440923:alias/app-name`
   - Allows platform team to rotate underlying key without code changes

2. **Request Keys Early:**
   - KMS key is often the longest lead-time item for new deployments
   - Include in initial infrastructure planning

3. **Document Key Purpose:**
   - Add comments in tfvars explaining what the key encrypts
   - Helps during troubleshooting and audits

4. **Test Key Access Before Deployment:**
   - Run `aws kms describe-key` to verify access
   - Test decrypt operation with dummy ciphertext

5. **Include All Services in Request:**
   - List ALL AWS services that will use the key (RDS, ECS, CloudWatch, Secrets Manager)
   - Prevents back-and-forth for key policy updates

---

## Related Patterns

**For Cross-Account DNS:** See `cross-account-dns-terraform-pattern.md`
**For VPC Endpoints:** See `coordination-workflows.md` (VPC endpoint for KMS API)
**For Shared VPC:** See main `jemena-shared-vpc-navigator` skill

---

## Contact for Issues

**KMS Key Requests:**
- Platform Team: platform-team@jemena.com.au
- David Hunter (core-network team)
- Slack: #datahub-platform

**Key Policy Issues:**
- Platform Team
- SLA: 1-2 business days

**Emergency (Production Blocked):**
- Platform Lead: Sampath Jagannathan
- Slack: #datahub-platform @here
