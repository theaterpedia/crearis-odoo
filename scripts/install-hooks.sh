#!/usr/bin/env bash
# Install the repo's local git hooks. Opt-in, because .git/hooks is per-clone and never
# version-controlled -- so a committed hook script is not the same thing as a running gate.
#
#   ./scripts/install-hooks.sh          install
#   ./scripts/install-hooks.sh --remove uninstall
#
# The pre-commit gate runs scripts/check_template_i18n.py --staged. It is fast (no DB, no
# network) and only inspects modules with staged changes.
#
# ⚠ It will BLOCK a commit whose .po msgid has drifted from its XML source. That is the
# point -- on a fresh install such a translation silently never applies. Escape hatch if
# you need it: `git commit --no-verify`.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HOOK="$REPO_ROOT/.git/hooks/pre-commit"

if [[ "${1:-}" == "--remove" ]]; then
    rm -f "$HOOK" && echo "removed $HOOK"
    exit 0
fi

mkdir -p "$(dirname "$HOOK")"
cat > "$HOOK" <<'HOOKEOF'
#!/usr/bin/env bash
# Installed by scripts/install-hooks.sh -- remove with scripts/install-hooks.sh --remove
set -euo pipefail
REPO_ROOT="$(git rev-parse --show-toplevel)"
if [[ -f "$REPO_ROOT/scripts/check_template_i18n.py" ]]; then
    python3 "$REPO_ROOT/scripts/check_template_i18n.py" --staged || {
        echo ""
        echo "pre-commit: template i18n gate FAILED (see above)."
        echo "  A drifted msgid means the translation silently never applies on a fresh install."
        echo "  Override with: git commit --no-verify"
        exit 1
    }
fi
HOOKEOF
chmod +x "$HOOK"
echo "installed $HOOK"
echo "  gate: scripts/check_template_i18n.py --staged"
