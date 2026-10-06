# Supply Chain Risk: claims-system MCP Server

**Who wrote it**: Claims Platform Team (internal, claims.internal.io)

**What it can reach**: Full adjuster note history and claim status for all open claims (50K+ claims with PII: customer names, policy details, loss descriptions)

**What it logs**: Every tools/call is logged with timestamp, claim_number, caller identity; logs retained 90 days in claims-audit.log

**Token theft scenario**: A stolen MCP token allows unlimited read-only access to claim details for all open claims; no write/modify capability, but adjuster notes contain sensitive personal information (address, phone, loss details)

**Decision**: SHIP with token scoping: read-only for get_adjuster_notes is acceptable for agent use, but require per-claim authorization audit if volume exceeds 1000 claims/day; rotate token monthly and alert on any unexpected caller IPs or tool patterns.
