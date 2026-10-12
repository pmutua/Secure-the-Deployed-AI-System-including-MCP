#!/usr/bin/env bash
# Deliverable 1: executable version of the secrets-hygiene checklist.
# Run from the repository root. Fails closed on the first broken check
# rather than reaching a final "OK" line on a repository it never
# actually examined.
set -euo pipefail

fail() { echo "FAIL: $*" >&2; exit 1; }

# 1) .env must be ignored. git check-ignore's exit code IS the signal --
#    -q suppresses the matched-rule text since we only need the boolean.
if ! git check-ignore -q .env; then
  fail ".env is not gitignored"
fi

# 2) .env must never appear in history. --all walks every ref, not just
#    the current branch, so a secret committed on an abandoned feature
#    branch is still caught even though it never merged.
if git log --all --full-history -- .env 2>/dev/null | grep -q .; then
  fail ".env appears in git history: rotate the secrets"
fi

# 3) Compose files must not inline a quoted secret-shaped value.
#    Delegated to Python, which has a real regex engine.
python encryption/check_gitignore.py || fail "check_gitignore.py reported a problem"

echo "OK: secrets_not_in_git.sh passed"
