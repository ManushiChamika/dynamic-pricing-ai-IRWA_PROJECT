# Enhanced Branch Age Comparison Script for PowerShell
# Save as compare-branch-age.ps1 and run from repo root
# Requires: gh, jq, git

$ErrorActionPreference = 'Stop'

# 0) parse owner/repo from origin URL
$origin_url = git remote get-url origin 2>$null
if (-not $origin_url) {
  Write-Error "ERROR: cannot read origin URL. Run from repo root with 'origin' remote configured."
  exit 1
}
$owner_repo = $origin_url -replace '^(git@github.com:|https://github.com/)([^/]+)/([^/]+)(\.git)?$', '$2/$3'
Write-Host "OWNER/REPO: $owner_repo"
Write-Host

# 1) show remote branch refs & SHAs
Write-Host "=== git ls-remote for dev and DEV ==="
git ls-remote origin refs/heads/dev refs/heads/DEV
if ($LASTEXITCODE -ne 0) {
  git ls-remote origin | Select-String -Pattern 'refs/heads/(dev|DEV)'
}
Write-Host

# 2) PRIMARY: Query GitHub CreateEvent via REST events - comprehensive search
Write-Host "=== GitHub CreateEvent (branch) for dev/DEV — comprehensive search ==="
Write-Host "Searching all repository events for branch creation..."

# First try: Recent events with pagination
Write-Host "--- Searching recent events ---"
$createEvents = gh api "repos/$owner_repo/events" --paginate | jq -r '.[] | select(.type=="CreateEvent" and .payload.ref_type=="branch") | "\(.payload.ref)\t\(.created_at)\t\(.actor.login)"'
if ($createEvents) {
  $createEvents | Where-Object { $_ -match '^(dev|DEV)\b' }
}

# Second try: Activity events (different endpoint)
Write-Host "--- Searching activity events ---"
$activityEvents = gh api "repos/$owner_repo/activity" --paginate 2>$null | jq -r '.[] | select(.activity_type=="push" and .ref=="refs/heads/dev" or .ref=="refs/heads/DEV") | "\(.ref | sub("refs/heads/"; ""))\t\(.timestamp)\t\(.actor.login)"' 2>$null
if ($activityEvents) {
  $activityEvents
}

# Third try: Using GitHub search API for commits
Write-Host "--- Searching for earliest commits via GitHub search ---"
try {
  $devSearch = gh api "search/commits?q=repo:$owner_repo+author-date:2020-01-01..2025-12-31" --paginate 2>$null | jq -r '.items[] | select(.commit.message | test("dev|DEV"; "i")) | "\(.sha[0:7])\t\(.commit.author.date)\t\(.commit.author.name)\t\(.commit.message | split("\n")[0])"' 2>$null
  if ($devSearch) {
    Write-Host "Found commits mentioning dev/DEV:"
    $devSearch | Select-Object -First 10
  }
} catch {
  Write-Host "Search API not accessible or no results"
}

# Fourth try: Direct branch info API
Write-Host "--- Getting branch information directly ---"
try {
  $devBranch = gh api "repos/$owner_repo/branches/dev" 2>$null | jq -r '"\(.name)\t\(.commit.commit.author.date)\t\(.commit.commit.author.name)"'
  $DEVBranch = gh api "repos/$owner_repo/branches/DEV" 2>$null | jq -r '"\(.name)\t\(.commit.commit.author.date)\t\(.commit.commit.author.name)"'
  if ($devBranch) { Write-Host "dev branch latest commit: $devBranch" }
  if ($DEVBranch) { Write-Host "DEV branch latest commit: $DEVBranch" }
} catch {
  Write-Host "Direct branch API failed"
}

Write-Host

# 3) Fallback: earliest unique commit per branch
Write-Host "=== Fallback: earliest commit unique to each branch (approximate) ==="
git fetch origin --prune
$sha_dev = git rev-list --reverse origin/dev --not origin/DEV 2>$null | Select-Object -First 1
if ($sha_dev) {
  Write-Host "origin/dev earliest unique commit:"
  git show -s --format="%H %ai %an %s" $sha_dev
} else {
  Write-Host "No commits unique to origin/dev (it may be ancestor of origin/DEV or origin/dev missing)"
}
Write-Host
$sha_DEV = git rev-list --reverse origin/DEV --not origin/dev 2>$null | Select-Object -First 1
if ($sha_DEV) {
  Write-Host "origin/DEV earliest unique commit:"
  git show -s --format="%H %ai %an %s" $sha_DEV
} else {
  Write-Host "No commits unique to origin/DEV (it may be ancestor of origin/dev or origin/DEV missing)"
}
Write-Host

# 4) Alternative: Get ALL commits from both branches and find divergence point
Write-Host "=== Alternative: Full commit history analysis ==="
Write-Host "Finding first commit on each branch (may show creation point)..."
try {
  $devFirstCommit = git rev-list --max-parents=0 origin/dev 2>$null | Select-Object -First 1
  $DEVFirstCommit = git rev-list --max-parents=0 origin/DEV 2>$null | Select-Object -First 1
  
  if ($devFirstCommit) {
    Write-Host "origin/dev first commit:"
    git show -s --format="%H %ai %an %s" $devFirstCommit
  }
  if ($DEVFirstCommit) {
    Write-Host "origin/DEV first commit:"
    git show -s --format="%H %ai %an %s" $DEVFirstCommit
  }
  
  # Find merge base (common ancestor)
  $mergeBase = git merge-base origin/dev origin/DEV 2>$null
  if ($mergeBase) {
    Write-Host "Common ancestor (merge base):"
    git show -s --format="%H %ai %an %s" $mergeBase
  }
} catch {
  Write-Host "Full history analysis failed"
}
Write-Host

# 5) Extra: list topmost commits on both branches for quick comparison
Write-Host "=== Top commits on origin/dev and origin/DEV ==="
Write-Host "origin/dev ->"
git log --format="%h %ai %an %s" -n 5 origin/dev
Write-Host
Write-Host "origin/DEV ->"
git log --format="%h %ai %an %s" -n 5 origin/DEV
Write-Host

# 6) Summary heuristic (best-effort)
Write-Host "=== ENHANCED SUMMARY ==="
Write-Host "1. CreateEvent data = most reliable if found above"
Write-Host "2. Branch API data = shows latest commit info per branch"
Write-Host "3. Unique commits = shows which branch has exclusive commits"
Write-Host "4. First commits = shows the earliest commit reachable from each branch"
Write-Host "5. Common ancestor = shows where branches diverged"
Write-Host
Write-Host "Analysis complete. Review all sections above to determine which branch is older."
Write-Host "If branches are identical (same commits), either can be safely deleted."
