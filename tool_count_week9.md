# Week 9: Tool Discovery Before & After

## Server One: policy-docs (Original)

**tools/list response** (from policy-docs server):
```json
{
  "tools": [
    {"name": "search_policy_documents", "description": "Search for policy language"},
    {"name": "get_policy_section", "description": "Retrieve specific policy section"},
    {"name": "list_exclusions", "description": "List all exclusions for a policy type"}
  ]
}
```

**Tool Count Before**: **3 tools**
- search_policy_documents
- get_policy_section
- list_exclusions

---

## Server One + Server Two: claims-system (New)

**Server One: policy-docs** (unchanged)
- search_policy_documents
- get_policy_section
- list_exclusions

**Server Two: claims-system** (newly added via config)
```json
{
  "tools": [
    {"name": "get_claim_status", "description": "Get the current status of a claim"},
    {"name": "get_adjuster_notes", "description": "Get the timeline of adjuster notes"}
  ]
}
```

**Tool Count After**: **5 tools**
- search_policy_documents (from policy-docs)
- get_policy_section (from policy-docs)
- list_exclusions (from policy-docs)
- get_claim_status (from claims-system)
- get_adjuster_notes (from claims-system)

---

## Summary

| Metric | Before | After | Change |
|--------|--------|-------|--------|
| MCP Servers | 1 | 2 | +1 |
| Tools Discovered | 3 | 5 | +2 |
| Agent Code Changed | 0 lines | 0 lines | 0 (config-only) |

**New tools (claims-system server)**:
1. `get_claim_status` - Retrieve claim status (approved/denied/pending)
2. `get_adjuster_notes` - Retrieve adjuster note timeline

**Discovery Method**: Automatic via MCP tools/list protocol from mcp_servers_config.json
