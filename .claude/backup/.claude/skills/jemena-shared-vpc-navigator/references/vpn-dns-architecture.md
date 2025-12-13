# VPN Access Architecture for Data Platform Engineers

## Purpose

Complete architectural documentation of how data platform engineers access AWS resources (Databricks workspaces, Data Mesh Manager, EWB) when working remotely via Corporate VPN.

This reference explains:
- Full network path from VPN connection to AWS resources
- DNS resolution flow through conditional forwarders
- Why conditional forwarders are critical for VPN access
- Troubleshooting VPN-specific access issues
- Differences between VPN and Zscaler access patterns

---

## Table of Contents

- [Network Topology](#network-topology)
- [VPN to AWS Network Path](#vpn-to-aws-network-path)
- [DNS Resolution Flow](#dns-resolution-flow)
- [Conditional Forwarder Configuration](#conditional-forwarder-configuration)
- [VPN vs Zscaler Comparison](#vpn-vs-zscaler-comparison)
- [Troubleshooting VPN Access Issues](#troubleshooting-vpn-access-issues)
- [Contact Matrix](#contact-matrix)

---

## Network Topology

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         REMOTE USER (VPN)                               │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ Corporate Laptop                                                  │  │
│  │   • VPN Client (Cisco AnyConnect or similar)                     │  │
│  │   • Connected to Corporate VPN Gateway                           │  │
│  │   • Assigned internal IP (10.x.x.x range)                        │  │
│  │   • DNS servers set to Active Directory DNS                      │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                              ↓                                          │
│                    VPN Tunnel (IPSec/SSL)                               │
└─────────────────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                   CORPORATE DATA CENTER                                 │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ VPN Gateway / Concentrator                                       │  │
│  │   • Terminates VPN connections                                   │  │
│  │   • Routes traffic to internal networks                          │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                              ↓                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ Active Directory DNS Servers                                     │  │
│  │   • ALINTA Domain Controllers (Production)                       │  │
│  │     - 10.155.5.14 (WPRDC212)                                     │  │
│  │     - 10.156.5.14 (WPRDC213)                                     │  │
│  │   • PowerDev Domain Controllers (Nonprod)                        │  │
│  │     - 10.156.154.102 (MDVDC212)                                  │  │
│  │     - 10.156.154.142 (MDVDC213)                                  │  │
│  │                                                                  │  │
│  │ Conditional Forwarders Configured:                               │  │
│  │   • *.cloud.databricks.com                                       │  │
│  │   • *.nonprod-vpc.aws.int                                        │  │
│  │   • *.prod-vpc.aws.int                                           │  │
│  │   → Forward to Route 53 Inbound Endpoints                        │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                              ↓                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ F5 GTM (Global Traffic Manager)                                  │  │
│  │   • jvpdclbs01, jvsdclbs01 (10.157.22.55/56)                     │  │
│  │   • Authoritative for lbs.* zones                                │  │
│  │   • iRule enforces DNS authorization                             │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                               ↓
                    AWS Direct Connect (Private VIF)
                               ↓
┌─────────────────────────────────────────────────────────────────────────┐
│           AWS CORE-NETWORK ACCOUNT (234268347951)                       │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ Route 53 Resolver INBOUND Endpoints                              │  │
│  │   • core-network-prod-r53-inbound-endpoint                       │  │
│  │   • ENI IPs (3 AZs for high availability):                       │  │
│  │     - 10.32.1.130 (ap-southeast-2a)                              │  │
│  │     - 10.32.2.194 (ap-southeast-2b)                              │  │
│  │     - 10.32.3.190 (ap-southeast-2c)                              │  │
│  │   • Receives DNS queries FROM on-premises TO AWS                 │  │
│  │   • Resolves queries using Private Hosted Zones                  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                              ↓                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ Route 53 Private Hosted Zones                                    │  │
│  │   • prod-vpc.aws.int (Z0230776MG3AOI9WPI6K)                      │  │
│  │   • nonprod-vpc.aws.int (Z067397015OIIZFMCSI1G)                  │  │
│  │   • dmz-vpc.aws.int                                              │  │
│  │   • *.cloud.databricks.com (workspace-specific PHZs)             │  │
│  │                                                                  │  │
│  │ DNS Records:                                                     │  │
│  │   • dmm.prod-vpc.aws.int → ALB IP (10.32.x.x)                   │  │
│  │   • jemena-digital-field.cloud.databricks.com → FEPL IPs        │  │
│  │   • ewb.prod-vpc.aws.int → ALB IP (10.32.x.x)                   │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                              ↓                                          │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │ Databricks Frontend Private Link (FEPL)                         │  │
│  │   • ENI IPs: 10.32.78.59, 10.32.78.86, 10.32.78.16              │  │
│  │   • Serves ALL workspaces (prod + nonprod)                       │  │
│  └──────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
                               ↓
┌─────────────────────────────────────────────────────────────────────────┐
│           APPLICATION ACCOUNTS (Prod/Nonprod)                           │
│   • ALB endpoints for DMM, EWB applications                             │
│   • Databricks workspaces accessible via FEPL                           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## VPN to AWS Network Path

### Step-by-Step Network Flow

**1. User Initiates VPN Connection**
- User opens VPN client on corporate laptop
- Authenticates against corporate AD (username/password + MFA)
- VPN concentrator assigns internal IP from corporate range
- DNS settings automatically configured to use AD DNS servers

**2. VPN Tunnel Established**
- Encrypted tunnel created between laptop and corporate gateway
- All traffic routed through tunnel (split or full tunnel depending on config)
- User can now access internal corporate resources

**3. DNS Query Initiated**
- User opens browser and navigates to: `https://dmm.prod-vpc.aws.int`
- Browser sends DNS query to configured DNS server (AD DNS)

**4. AD DNS Receives Query**
- Active Directory DNS server (e.g., 10.155.5.14) receives query
- Checks local zones - no authoritative zone for `prod-vpc.aws.int`
- Evaluates conditional forwarder rules

**5. Conditional Forwarder Matches**
- Rule matches: `*.prod-vpc.aws.int` → Forward to Route 53 Inbound Endpoints
- DNS query forwarded to: 10.32.1.130, 10.32.2.194, 10.32.3.190
- Traffic routed via AWS Direct Connect private VIF

**6. Route 53 Resolver Processes Query**
- Inbound endpoint receives query from on-premises (10.155.5.14 source)
- Queries Private Hosted Zone: `prod-vpc.aws.int`
- Returns A record for `dmm.prod-vpc.aws.int` → ALB IP (e.g., 10.32.45.78)

**7. DNS Response Returns to Client**
- Route 53 → AD DNS → VPN tunnel → Laptop
- Browser receives private IP (10.32.x.x)
- Initiates HTTPS connection to ALB

**8. Application Traffic Flows**
- HTTPS request: Laptop → VPN → Direct Connect → ALB (10.32.x.x)
- ALB forwards to ECS tasks running Data Mesh Manager
- Response returns via same path

---

## DNS Resolution Flow

### Detailed DNS Query Path

```
┌──────────────────────────────────────────────────────────────────┐
│ Step 1: User Query                                               │
│ User: "nslookup jemena-digital-field.cloud.databricks.com"      │
│ Source: 10.155.x.x (VPN-assigned IP)                            │
│ Destination: 10.155.5.14 (AD DNS server)                        │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│ Step 2: AD DNS Server Processing                                │
│ Server: WPRDC212 (10.155.5.14)                                  │
│ Action: Check local zones → No match                            │
│ Action: Check conditional forwarders                            │
│ Match: *.cloud.databricks.com → Route 53 Inbound Endpoints      │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│ Step 3: Forwarded to Route 53                                   │
│ Source: 10.155.5.14 (AD DNS server)                             │
│ Destination: 10.32.1.130, 10.32.2.194, 10.32.3.190 (round-robin)│
│ Protocol: DNS over Direct Connect                               │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│ Step 4: Route 53 Resolver Inbound Endpoint                      │
│ Endpoint: core-network-prod-r53-inbound-endpoint                │
│ Action: Query Private Hosted Zone                               │
│ Zone: jemena-digital-field.cloud.databricks.com                 │
│ Record Type: A (Alias to FEPL endpoint)                         │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│ Step 5: PHZ Returns Answer                                      │
│ Answer: 10.32.78.59 (FEPL IP)                                   │
│ TTL: 300 seconds                                                 │
└──────────────────────────────────────────────────────────────────┘
                              ↓
┌──────────────────────────────────────────────────────────────────┐
│ Step 6: Response Returns to User                                │
│ Path: Route 53 → Direct Connect → AD DNS → VPN → Laptop         │
│ User receives: 10.32.78.59                                       │
│ Browser connects to FEPL → Databricks workspace                 │
└──────────────────────────────────────────────────────────────────┘
```

### Key DNS Characteristics

**Multi-AZ High Availability:**
- Route 53 Inbound Endpoints span 3 AZs (2a, 2b, 2c)
- If one AZ fails, queries automatically route to healthy endpoints
- AD DNS servers configured with all 3 IPs for resilience

**Caching Behavior:**
- AD DNS servers cache responses (TTL: 300 seconds)
- Subsequent queries from users served from cache
- Reduces latency and Route 53 query volume

**Latency:**
- VPN user to AD DNS: ~5-10ms (on-prem latency)
- AD DNS to Route 53: ~2-5ms (Direct Connect latency)
- Route 53 query resolution: <1ms
- **Total DNS resolution time: ~10-20ms**

---

## Conditional Forwarder Configuration

### Required Conditional Forwarders

For data platform engineers to access AWS resources via VPN, the following conditional forwarders MUST be configured on Active Directory DNS servers:

| Domain Pattern | Target IPs | Purpose | Status |
|----------------|------------|---------|--------|
| **\*.cloud.databricks.com** | 10.32.1.130<br>10.32.2.194<br>10.32.3.190 | Databricks workspace access | ✅ Configured |
| **\*.nonprod-vpc.aws.int** | 10.32.1.130<br>10.32.2.194<br>10.32.3.190 | Nonprod applications (DMM, EWB) | ✅ Configured |
| **\*.prod-vpc.aws.int** | 10.32.1.130<br>10.32.2.194<br>10.32.3.190 | Prod applications (DMM, EWB) | ⚠️ Verify |

### Configuration Details

**Active Directory DNS Servers:**
- **Production (ALINTA domain):**
  - WPRDC212: 10.155.5.14
  - WPRDC213: 10.156.5.14

- **Nonproduction (PowerDev domain):**
  - MDVDC212: 10.156.154.102
  - MDVDC213: 10.156.154.142

**PowerShell Configuration Example:**
```powershell
# Create conditional forwarder for Databricks workspaces
Add-DnsServerConditionalForwarderZone `
  -Name "cloud.databricks.com" `
  -MasterServers 10.32.1.130,10.32.2.194,10.32.3.190 `
  -ReplicationScope "Forest"

# Create conditional forwarder for prod VPC
Add-DnsServerConditionalForwarderZone `
  -Name "prod-vpc.aws.int" `
  -MasterServers 10.32.1.130,10.32.2.194,10.32.3.190 `
  -ReplicationScope "Forest"

# Create conditional forwarder for nonprod VPC
Add-DnsServerConditionalForwarderZone `
  -Name "nonprod-vpc.aws.int" `
  -MasterServers 10.32.1.130,10.32.2.194,10.32.3.190 `
  -ReplicationScope "Forest"

# Verify configuration
Get-DnsServerZone | Where-Object {$_.ZoneType -eq "Forwarder"}
```

### Why Conditional Forwarders are Critical

**Without Conditional Forwarders:**
- AD DNS attempts to resolve `*.prod-vpc.aws.int` via public DNS root servers
- No public zone exists for `*.aws.int` (internal domain)
- Query returns NXDOMAIN (domain does not exist)
- **User cannot access application from VPN**

**With Conditional Forwarders:**
- AD DNS forwards query to Route 53 Inbound Endpoints
- Route 53 queries Private Hosted Zones (authoritative)
- Returns private ALB/FEPL IPs
- **User successfully accesses application**

---

## VPN vs Zscaler Comparison

### Two Corporate Access Patterns

Jemena uses TWO distinct access patterns for remote users, each with different DNS resolution paths:

| Aspect | VPN Access | Zscaler Access |
|--------|-----------|----------------|
| **Use Case** | Working from home (full remote) | Working from office (behind Zscaler proxy) |
| **Network Path** | VPN → Direct Connect → AWS | Zscaler Client → ZPA Appliances (in AWS) → Route 53 |
| **DNS Resolution** | AD DNS → Conditional Forwarders → Route 53 | Zscaler intercepts DNS → Routes to Route 53 |
| **DNS Config Required** | Conditional forwarders on AD DNS | Zscaler rule for `*.cloud.databricks.com` |
| **Troubleshooting** | Check VPN connection + conditional forwarders | Check Zscaler client running + rules |
| **Latency** | ~10-20ms (VPN + Direct Connect) | ~5-10ms (already in AWS) |
| **Common Issues** | Missing conditional forwarder, VPN routing | Zscaler rule missing, client not running |

### When to Use VPN vs Zscaler

**VPN Access (Recommended for):**
- Working fully remote (home, cafe, travel)
- Accessing internal corporate resources (.net.int domains)
- SSH/RDP to on-premises servers
- Full network connectivity to corporate resources

**Zscaler Access (Recommended for):**
- Working from Jemena offices
- Cloud application access only (Databricks, DMM, EWB)
- Faster DNS resolution (ZPA appliances in AWS)
- No VPN overhead

**Best Practice:** Office users should use Zscaler, remote users should use VPN

---

## Troubleshooting VPN Access Issues

### Decision Tree for VPN Access Problems

```
User reports: "Can't access Databricks/DMM/EWB from VPN"
         ↓
┌────────────────────────────────────────────────────────────┐
│ Step 1: Verify VPN Connection                             │
│ Test: ping internal.jemena.com.au                         │
│ Test: ping 10.155.5.14 (AD DNS server)                    │
│                                                            │
│ If fails → VPN connection issue                           │
│   - Reconnect VPN                                          │
│   - Check VPN client logs                                 │
│   - Contact IT Support for VPN issues                     │
└────────────────────────────────────────────────────────────┘
         ↓ (VPN works)
┌────────────────────────────────────────────────────────────┐
│ Step 2: Test DNS Resolution                               │
│ Command: nslookup dmm.prod-vpc.aws.int                    │
│ Command: nslookup jemena-digital-field.cloud.databricks.com│
│                                                            │
│ Expected: Private IPs (10.32.x.x)                         │
│ Actual outcomes →                                          │
└────────────────────────────────────────────────────────────┘
         ↓
    ┌────┴──────┐
    ↓           ↓
┌─────────┐  ┌──────────┐
│ Returns │  │ Returns  │
│ Public  │  │ NXDOMAIN │
│ IPs     │  │ (error)  │
│ 3.x.x.x │  │          │
└─────────┘  └──────────┘
    ↓           ↓
┌───────────────────────────────────────────────────────────┐
│ Diagnosis: Conditional forwarder misconfigured            │
│                                                           │
│ Root Cause:                                               │
│ - Conditional forwarder missing on AD DNS                 │
│ - Forwarder pointing to wrong IPs                        │
│ - Forwarder rule pattern incorrect                       │
│                                                           │
│ Fix:                                                      │
│ 1. Contact core-network team (David Hunter)              │
│ 2. Provide domain pattern (*.prod-vpc.aws.int)           │
│ 3. Provide target IPs (10.32.1.130/2.194/3.190)          │
│ 4. SLA: 1-2 business days                                │
└───────────────────────────────────────────────────────────┘
```

### Common VPN Access Issues

**Issue 1: DNS Returns Public IPs Instead of Private IPs**
- **Symptom:** `nslookup jemena-digital-field.cloud.databricks.com` returns 3.x.x.x
- **Cause:** Conditional forwarder not configured for `*.cloud.databricks.com`
- **Fix:** AD DNS server querying public DNS instead of Route 53
- **Contact:** Core-network team to add conditional forwarder

**Issue 2: DNS Timeout / No Response**
- **Symptom:** `nslookup dmm.prod-vpc.aws.int` times out
- **Cause 1:** VPN routing table missing route to 10.32.0.0/16
- **Cause 2:** Firewall blocking DNS traffic to Route 53 endpoints
- **Fix:** Verify VPN routing, check firewall rules
- **Contact:** Core-network team for routing, Security team for firewall

**Issue 3: Inconsistent DNS Resolution (Flips Between Public/Private)**
- **Symptom:** DNS results change on subsequent queries
- **Cause:** Conditional forwarder using wrong domain pattern
- **Example:** Forwarder set to `sydney.privatelink.cloud.databricks.com` instead of `*.cloud.databricks.com`
- **Fix:** Update conditional forwarder to wildcard pattern
- **Reference:** See DNS Workaround #1 in main SKILL.md

**Issue 4: Can Resolve DNS But Can't Connect**
- **Symptom:** `nslookup` works (returns 10.32.x.x) but browser can't connect
- **Cause 1:** VPN split-tunnel not routing 10.32.0.0/16 through tunnel
- **Cause 2:** Corporate firewall blocking HTTPS (443) to AWS
- **Fix:** Verify VPN routing table includes 10.32.0.0/16
- **Test:** `traceroute dmm.prod-vpc.aws.int` to see where traffic drops

---

## Contact Matrix

### VPN Access Issues - Who to Contact

| Issue Type | Team | Contact | SLA | Communication Channel |
|------------|------|---------|-----|----------------------|
| **VPN Connection Issues** | IT Support | Service Desk | <4 hours | ServiceNow ticket |
| **Conditional Forwarder (DNS)** | Core-Network | David Hunter | 1-2 days | Email + Slack (#cloud-networking) |
| **Route 53 Configuration** | Core-Network | David Hunter | 2-5 days | Email + Slack (#cloud-networking) |
| **Firewall Rules (AWS → On-prem)** | Security | Security Team | 3-7 days | ServiceNow ticket |
| **Direct Connect Issues** | Core-Network | Network Operations | <1 hour (critical) | On-call escalation |
| **Application Issues (DMM/EWB)** | Platform Team | Digital Analytics | <4 hours | Slack (#datahub-platform) |
| **Databricks Workspace Issues** | Platform Team | Digital Analytics | <4 hours | Slack (#datahub-platform) |

### Escalation Path for Critical Issues

**P1 - Production workspace completely inaccessible from VPN:**
1. Immediate: Slack #datahub-platform + tag @platform-lead
2. If no response in 15 min: On-call engineer (PagerDuty)
3. Parallel: ServiceNow P1 ticket for visibility

**P2 - VPN access degraded (slow or intermittent):**
1. ServiceNow ticket to core-network team
2. Slack #cloud-networking with ticket number
3. Expected resolution: 4-8 hours

**P3 - Individual user can't access (VPN config issue):**
1. IT Service Desk ticket
2. Include VPN logs and DNS test results
3. Expected resolution: Same day

---

## Testing VPN Access

### Pre-Deployment Checklist

Before deploying new applications accessible via VPN, verify:

- [ ] Route 53 Private Hosted Zone created
- [ ] DNS A record added pointing to ALB/FEPL
- [ ] Conditional forwarder configured on AD DNS (both prod and nonprod)
- [ ] VPN test from remote user successful
- [ ] Office test from Zscaler successful
- [ ] DNS resolution returns private IPs (not public)
- [ ] HTTPS connection successful (valid TLS certificate)

### Testing Commands

**From VPN-connected laptop:**
```bash
# Test 1: Verify VPN connection
ping 10.155.5.14
# Expected: Replies from 10.155.5.14

# Test 2: DNS resolution
nslookup dmm.prod-vpc.aws.int
# Expected: 10.32.x.x (private IP)

# Test 3: HTTPS connectivity
curl -I https://dmm.prod-vpc.aws.int
# Expected: HTTP/2 200 (or 302 redirect to login)

# Test 4: Traceroute to verify path
traceroute dmm.prod-vpc.aws.int
# Expected: Route through 10.x.x.x IPs (via Direct Connect)

# Test 5: DNS query time
nslookup -debug dmm.prod-vpc.aws.int
# Expected: Query time < 50ms
```

**Interpreting Results:**
- **Query time < 20ms:** Cached response from AD DNS
- **Query time 20-50ms:** Fresh query forwarded to Route 53
- **Query time > 100ms:** Potential network issue, investigate

---

## Summary

### Key Takeaways for Data Platform Engineers

1. **VPN access requires conditional forwarders** - Without them, DNS queries won't reach Route 53
2. **Route 53 Inbound Endpoints are critical** - They receive queries from corporate DNS (10.32.1.130, 10.32.2.194, 10.32.3.190)
3. **Three domains need forwarders** - `*.cloud.databricks.com`, `*.prod-vpc.aws.int`, `*.nonprod-vpc.aws.int`
4. **VPN vs Zscaler are different paths** - Office users prefer Zscaler, remote users use VPN
5. **Core-network team manages forwarders** - Data platform engineers cannot configure AD DNS directly

### Architecture Principles

- **Separation of Concerns:** Core-network team owns DNS infrastructure, platform team owns applications
- **Shared VPC Model:** VPN access demonstrates why subnets are shared (Direct Connect attachment in core-network account)
- **High Availability:** Route 53 endpoints span 3 AZs, AD DNS configured with all 3 IPs
- **Security:** All traffic encrypted (VPN tunnel + TLS for applications)

---

**Document maintained by:** Platform Engineering Team
**Last updated:** 2025-01-16
**Related documents:**
- `../SKILL.md` - Main jemena-shared-vpc-navigator skill
- `route53-resolver-rules.md` - Detailed resolver rule configuration
- `CLOUD-Hybrid DNS-161125-060322.pdf` - Official DNS architecture PDF
