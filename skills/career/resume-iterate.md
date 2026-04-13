---
name: resume-iterate
description: >
  Systematically extract, catalog, and aggregate career evidence from all available sources
  to build the strongest possible application dossier. Use when preparing for a job application,
  updating a resume, or gathering evidence for a specific role. Also triggers on: "resume",
  "dossier", "application", "evidence", "gap analysis", "candidacy", "job prep".
---

# Resume Iterate — Cross-Domain Evidence Pulling

## Purpose

Systematically extract, catalog, and aggregate career evidence from all available sources to build the strongest possible application dossier. Designed for iterative runs — each pass discovers new evidence, flags gaps, and updates the master dossier. The dossier is **additive-only** — never remove existing content, only append new evidence.

## When to Use

- Before applying to a role (initial evidence gathering)
- When new sources become available (new endorsements, updated repos, new certifications)
- When targeting a specific role and need to map evidence to requirements
- Periodic refresh to capture recent activity
- When updating an existing dossier with newly discovered evidence

## Non-Negotiable Rules

- **NEVER fabricate evidence** — if a data point can't be verified, mark it `NEEDS_CONFIRMATION`
- **Separate facts from inferences** — clearly label strength assessments vs raw data
- **Preserve attribution** — every quote gets a name and source
- **Flag staleness** — note when evidence is >12 months old
- **Privacy first** — never expose credentials, tokens, or PII in output files
- **Additive only** — never remove or overwrite existing dossier content; only append
- **Version every update** — bump the version number and note what changed in the header

## Evidence Domains

### 1. GitHub Profile

**Method**: GitHub REST API via `curl`

```bash
curl -s "https://api.github.com/users/[your-github-username]" | jq '{login, name, company, blog, bio, public_repos, followers, following, created_at}'
curl -s "https://api.github.com/users/[your-github-username]/repos?per_page=100&sort=updated" | jq '.[] | {name, description, language, stargazers_count, forks_count, created_at, updated_at, topics}'
curl -s "https://api.github.com/users/[your-github-username]/events/public?per_page=100" | jq '.[] | {type, repo: .repo.name, created_at}'
```

**Key fields**: repo count, languages used, commit frequency, topics, stars, forks
**Limitation**: Private repos and private activity are not visible via API. Note this gap explicitly.

### 2. LinkedIn Profile

**Method**: Browser automation (LinkedIn blocks API/fetch)
**Extract**: Headline, summary, experience entries, skills/endorsements, connection count, posts, recommendations, certifications, education.

### 3. Local Repositories

**Method**: Bash commands — scan all repos in your code directory

```bash
find ~/Code -maxdepth 3 -name ".git" -type d 2>/dev/null | sed 's/\/.git//'
# Count Python files (exclude venvs)
find ~/Code -name "*.py" -not -path "*/node_modules/*" -not -path "*/.venv/*" -not -path "*/venv/*" -not -path "*/__pycache__/*" 2>/dev/null | wc -l
# Count TypeScript files
find ~/Code \( -name "*.ts" -o -name "*.tsx" \) 2>/dev/null | grep -v node_modules | wc -l
```

For each key repo, extract:
- Primary languages and frameworks
- Key technical decisions (from README or code)
- Scale indicators (file count, complexity, integration depth)
- Real outcomes if documented

### 4. Performance Reviews

**Method**: Read any uploaded `.docx` or PDF review files
**Extract**: Ratings, manager comments (verbatim), peer endorsements, listed accomplishments, stated goals, promotions.

### 5. Certifications and Education

**Method**: Read certificate images/PDFs, LinkedIn, official transcripts
**Extract**: Certification name, issuer, date obtained, expiry (if any), credential ID for verification.

### 6. Cloud and Infrastructure Evidence

**Method**: Search repos for config files and documentation

```bash
find ~/Code -name "*terraform*" -o -name "*.tf" -o -name "*kubernetes*" -o -name "*.yaml" 2>/dev/null | grep -v node_modules | head -20
grep -rl "googleapis\|service_account\|GoogleAuth\|AWS\|azure" ~/Code --include="*.ts" --include="*.py" 2>/dev/null | grep -v node_modules | head -20
```

**Extract**: Cloud providers used, services configured, IAM/auth patterns, infrastructure-as-code depth.

### 7. Speaking and Conference Evidence

**Method**: LinkedIn posts, uploaded proposals, calendar
**Extract**: Event name, date, topic, role (speaker/panelist/attendee), audience size.

### 8. Open Source Contributions

**Method**: GitHub API — search for PRs and issues on external repos

```bash
curl -s "https://api.github.com/search/issues?q=author:[your-github-username]+is:pr+is:merged&per_page=20" | jq '.items[] | {title, repository_url, created_at, html_url}'
```

**Extract**: Repos contributed to, PR titles, merge status, languages.

## Output Format

```markdown
### [DOMAIN] Item Title
- **Source**: Where found (file path, URL, API endpoint)
- **Date**: When the evidence is from
- **Confidence**: VERIFIED | INFERRED | NEEDS_CONFIRMATION
- **Relevance**: Which job requirements this maps to
- **Raw Evidence**: Verbatim quote or data point
- **Gap Flag**: What's missing or needs follow-up
```

## Iteration Protocol

1. **Scan** — Run all domain extractors, collect raw data
2. **Catalog** — Normalize into evidence items with metadata
3. **Diff** — Compare against existing dossier, identify NEW items
4. **Tag** — Mark each as `[NEW]`, `[UPDATED]`, or `[CONFIRMED]`
5. **Gap Analysis** — List what's still missing per job requirement
6. **Update Dossier** — Append new evidence to master file with version bump

## Role-Specific Mapping Template

| Requirement | Evidence Items | Strength | Gap |
|------------|---------------|----------|-----|
| Python 5+ yrs | [list items] | Strong/Moderate/Weak | [what's missing] |
| Cloud infra (GCP/AWS) | [list items] | Strong/Moderate/Weak | [what's missing] |
| System design | [list items] | Strong/Moderate/Weak | [what's missing] |
| Team leadership | [list items] | Strong/Moderate/Weak | [what's missing] |
| ... | ... | ... | ... |

## Quick Start

```
/resume-iterate                        # Full scan, all domains
/resume-iterate --domain github        # Single domain refresh
/resume-iterate --domain cloud         # Cloud/infra evidence only
/resume-iterate --domain ml            # ML/AI research evidence only
/resume-iterate --role "Senior Backend Engineer"  # Map to specific role
/resume-iterate --diff                 # Show only changes since last run
```

## Version History

Track updates in the dossier header:

```yaml
# Evidence Dossier
version: 2
last_updated: YYYY-MM-DD
domains_scanned: [github, linkedin, local-repos, certs, cloud]
new_items_this_run: 4
```
