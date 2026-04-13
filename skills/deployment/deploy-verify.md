---
description: Autonomous deploy → verify → auto-fix → rollback pipeline for Vercel, Railway, and Fly.io
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
---

# Self-Healing Deploy Pipeline

Act as an autonomous deployment agent. Execute all steps in order without stopping for confirmation unless a hard-abort condition is met. Capture all command output to temp log files so diagnosis can happen without re-running commands.

---

## Section 1 — Identity Guard

Before any bytes move, verify the CLI is aimed at the correct project. A wrong-target detection is a **hard abort** — do not enter the auto-fix loop, do not attempt a fix. Log the mismatch and stop.

**Detect platform from current directory (search subdirs for monorepos):**

```bash
PLATFORM="unknown"
DEPLOY_DIR="."

[ -f "vercel.json" ] || [ -f ".vercel/project.json" ] && PLATFORM="vercel"

if [ -f "fly.toml" ]; then
  PLATFORM="fly"
elif FLY_TOML=$(find . -maxdepth 2 -name "fly.toml" -not -path "*/node_modules/*" | head -1); [ -n "$FLY_TOML" ]; then
  PLATFORM="fly"
  DEPLOY_DIR=$(dirname "$FLY_TOML")
  echo "NOTE: fly.toml found in subdirectory: $DEPLOY_DIR (monorepo layout)"
fi

railway status 2>/dev/null | grep -q "Project" && PLATFORM="railway"
[ -f "railway.json" ] && PLATFORM="railway"
echo "Detected platform: $PLATFORM (deploy dir: $DEPLOY_DIR)"
```

All subsequent commands must run from `$DEPLOY_DIR`, not necessarily the repo root.

**Vercel identity check:**

```bash
LOCAL_PROJECT_ID=$(cat .vercel/project.json 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('projectId',''))")
echo "Linked project ID: $LOCAL_PROJECT_ID"

vercel project ls 2>&1 | head -20
```

Hard abort trigger: project name in `.vercel/project.json` or `vercel.json` does not match the expected project for this directory.

**Fly.io identity check:**

```bash
FLY_APP=$(grep "^app " "$DEPLOY_DIR/fly.toml" | awk '{print $3}' | tr -d '"')
echo "fly.toml app name: $FLY_APP"

FLY_PRE_VERSION=$(fly status --app "$FLY_APP" --json 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('Machines',[{}])[0].get('config',{}).get('image','unknown'))" 2>/dev/null)
echo "Pre-deploy version: $FLY_PRE_VERSION"

fly status --app "$FLY_APP" 2>&1 | head -10
```

Hard abort trigger: `fly status` returns "app not found" or the app name differs from the expected name for this repository.

**Railway identity check:**

```bash
railway status 2>&1
# Confirm project name and service name match expected values for this repo.
# If `railway status` shows a different project, HARD ABORT.
```

---

## Section 2 — Env Var Gate

Inspect platform-stored secrets against the required list. Missing vars abort before deploy. Do not attempt to fill them in — surface the gap and stop.

**Vercel:**
```bash
vercel env ls production 2>&1 | tee /tmp/vercel-env-ls.log
```

**Fly.io:**
```bash
fly secrets list --app "$FLY_APP" 2>&1 | tee /tmp/fly-secrets-ls.log
```

**Railway:**
```bash
railway variables 2>&1 | tee /tmp/railway-vars.log
```

Compare output against your project's required-vars list. Abort if any required variable is absent.

---

## Section 3 — Local Build Gate

Run the build locally before pushing. This catches TypeScript errors, missing dependencies, and broken imports before wasting a deploy slot.

```bash
if [ -f "package.json" ]; then
  npm run build 2>&1 | tee /tmp/local-build.log
  BUILD_EXIT=$?
  if [ $BUILD_EXIT -ne 0 ]; then
    echo "LOCAL BUILD FAILED — aborting deploy"
    cat /tmp/local-build.log
    exit 1
  fi
  echo "Local build passed."
fi
```

Fix any build errors before proceeding. The deploy step does not run until the local build is green.

---

## Section 4 — Deploy

Run the deploy command in the foreground. Capture all output. Extract the deploy URL for use in verification.

**Vercel:**

```bash
vercel deploy --prod --yes 2>&1 | tee /tmp/vercel-deploy.log
DEPLOY_EXIT=$?

DEPLOY_URL=$(grep -oE 'https://[a-zA-Z0-9._-]+\.vercel\.app' /tmp/vercel-deploy.log | tail -1)
PROD_URL=$(grep -oE 'https://[a-zA-Z0-9._/-]+' /tmp/vercel-deploy.log | grep -v vercel\.app | tail -1)
echo "Deploy URL: ${PROD_URL:-$DEPLOY_URL}"
```

**Fly.io:**

```bash
fly deploy --app "$FLY_APP" 2>&1 | tee /tmp/fly-deploy.log
DEPLOY_EXIT=$?
DEPLOY_URL="https://$FLY_APP.fly.dev"
```

**Railway:**

```bash
railway up 2>&1 | tee /tmp/railway-deploy.log
DEPLOY_EXIT=$?

sleep 15
DEPLOY_URL=$(railway status --json 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('serviceUrl',''))" 2>/dev/null)
echo "Deploy URL: $DEPLOY_URL"
```

If `DEPLOY_EXIT` is non-zero AND the log shows a hard build failure (not a CLI timeout), jump to Section 6 immediately.

---

## Section 5 — Verification Loop

Run up to 3 health probes with 10-second backoff. A passing probe requires HTTP 200 AND a valid app fingerprint in the response body. HTTP 200 alone is not sufficient — CDN caches can serve stale deployments.

```bash
PROBE_URL="${DEPLOY_URL}/api/health"
PROBE_PASS=0

for ATTEMPT in 1 2 3; do
  echo "--- Probe $ATTEMPT of 3 ---"
  HTTP_STATUS=$(curl -s -o /tmp/probe-body.json -w "%{http_code}" "$PROBE_URL" 2>/dev/null)
  echo "HTTP status: $HTTP_STATUS"

  if [ "$HTTP_STATUS" = "200" ]; then
    FINGERPRINT=$(python3 -c "
import json, sys
try:
    d = json.load(open('/tmp/probe-body.json'))
    print(d.get('app', d.get('service', d.get('status', ''))))
except:
    print('')
" 2>/dev/null)
    echo "Fingerprint: $FINGERPRINT"

    if [ -n "$FINGERPRINT" ]; then
      PROBE_PASS=1
      break
    fi
  fi

  [ $ATTEMPT -lt 3 ] && echo "Probe failed. Waiting 10s..." && sleep 10
done

echo "Probe result: $PROBE_PASS (1=pass, 0=fail)"
```

If the response fingerprint is present but does NOT match your expected project, this is a **wrong-app hard abort** — the project is misconfigured at the platform level.

If `PROBE_PASS=1`: deployment verified. Jump to Section 9.

If `PROBE_PASS=0`: proceed to Section 6.

---

## Section 6 — Diagnosis

Read the deploy log and probe response before attempting any fix. Classify the failure:

| Symptom | Root cause | Next action |
|---|---|---|
| Build error in deploy log | **build-failure** | Fix source code error |
| Deploy succeeded, 5xx from health probe | **runtime-crash** | Read runtime logs |
| Deploy succeeded, 502/503/504 | **startup-failure** | Check port binding |
| Deploy succeeded, 200, wrong fingerprint | **wrong-project** | HARD ABORT |
| Railway CLI timed out, URL empty | **railway-async** | Poll status 90 more seconds |
| Env var error in runtime logs | **missing-env-var** | Add var via CLI, redeploy |

**Fetch runtime logs:**

```bash
# Vercel
vercel logs "$DEPLOY_URL" --limit 50 2>&1 | tee /tmp/runtime-logs.log

# Fly.io
fly logs --app "$FLY_APP" 2>&1 | head -80 | tee /tmp/runtime-logs.log

# Railway
railway logs 2>&1 | head -80 | tee /tmp/runtime-logs.log

cat /tmp/runtime-logs.log
```

---

## Section 7 — Auto-Fix Loop

Execute up to 3 fix-redeploy-verify rounds. Each round must apply a different fix strategy. If the same root cause recurs after 2 different approaches, escalate to rollback.

```
ATTEMPT = 0
MAX_ATTEMPTS = 3
FIXED = false

while ATTEMPT < MAX_ATTEMPTS and not FIXED:
  ATTEMPT += 1
  [Apply targeted fix per playbook below]
  [Re-run local build gate — Section 3]
  [Re-run deploy — Section 4]
  [Re-run verification loop — Section 5]
  if probes pass: FIXED = true; break
  else: [Re-run diagnosis — Section 6]

if not FIXED: [Proceed to Section 8 — Rollback]
```

**Fix playbook:**

`build-failure`: Read the exact TypeScript/module error. Open the affected file, apply the minimal fix. Re-run `npm run build` locally before redeploying.

`runtime-crash`: Read the stack trace. Common causes: unhandled promise rejection, missing await, null dereference. Add try/catch if the root cause is an unhandled async error.

`startup-failure`: Verify `process.env.PORT` is used (not a hardcoded port). For Fly: verify `internal_port` in `fly.toml` matches what the app listens on.

`missing-env-var`: Add via platform CLI only — never commit to repository:
```bash
vercel env add VAR_NAME production
fly secrets set VAR_NAME="value" --app "$FLY_APP"
railway variables set VAR_NAME="value"
```

`railway-async`: Wait 60 more seconds, re-poll URL, re-run verification probes.

---

## Section 8 — Rollback

**Vercel:**
```bash
vercel rollback --yes 2>&1 | tee /tmp/vercel-rollback.log
ROLLBACK_URL=$(grep -oE 'https://[a-zA-Z0-9._/-]+' /tmp/vercel-rollback.log | tail -1)
sleep 5
curl -s -o /tmp/rollback-probe.json -w "%{http_code}" "${ROLLBACK_URL}/api/health"
```

**Fly.io:**
```bash
fly releases list --app "$FLY_APP" --json 2>/dev/null | python3 -c "
import sys, json
releases = json.load(sys.stdin)
if len(releases) >= 2:
    print(releases[1].get('imageRef', ''))
" 2>/dev/null | xargs -I{} fly deploy --app "$FLY_APP" --image {}
```

**Railway:** No CLI rollback. Open https://railway.app/dashboard, navigate to the Deployments tab, click the last successful deployment, and click "Redeploy". Verify health endpoint after redeploy.

---

## Section 9 — Final Report

```
Deploy Pipeline Report
======================
Timestamp:    [UTC]
Platform:     [vercel | fly | railway]
Project:      [name]
Environment:  production

Outcome:      [SUCCESS | ROLLBACK | HARD-ABORT | MANUAL-REQUIRED]

Phases:
  1. Identity guard:   [PASS | ABORT]
  2. Env var gate:     [PASS | ABORT | SKIP]
  3. Local build:      [PASS | FAIL-FIXED | ABORT]
  4. Deploy:           [COMPLETE | TIMED-OUT | FAILED]
  5. Verification:     [PASS | FAIL (N/3 probes)]
  6-7. Auto-fix loop:  [N rounds | skipped]
     Round 1: [root cause] → [fix applied] → [result]
  8. Rollback:         [NOT-NEEDED | COMPLETE | MANUAL-REQUIRED]

Live URL:     [final verified URL, or "unknown"]
Health check: [HTTP status] — [fingerprint value]
```

---

## Rules

- Never run a deploy without passing the identity guard (Section 1). No exceptions.
- Never background a deploy command. Always run foreground and capture exit code.
- Never modify test assertions or health check logic to make a failing probe "pass".
- Never set secrets in `.env` files committed to git — use platform CLI only.
- A wrong-app fingerprint always triggers hard abort. Do not auto-fix it.
- Railway rollback is always manual — never claim it was automated.
- After any deployment (success or rollback), always end with a live health check curl. Never declare success without a confirmed live probe.
