# Prod → GitHub loop probe · 2026-08-03

Throwaway commit from prod (CO@prod-coordinator) to verify the code-repo push
path works end-to-end:
- Autonomous prod deploy-key: NOT authorized for code-repos (read-only intent)
- HD's Yubikey-SK: agent-forwarded via VS Code Remote-SSH, required for this push

If you see this on GitHub, the Yubikey-touch flow is proven. Branch can be
deleted after verification.
