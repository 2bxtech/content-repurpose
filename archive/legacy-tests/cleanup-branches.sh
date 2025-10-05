#!/bin/bash
# Cleanup merged and stale local branches

echo "🧹 Cleaning up local branches..."

# Delete all backup branches (code is in main)
git branch -D backup/phase1-database-foundation
git branch -D backup/phase10a-authentication-foundation-complete
git branch -D backup/phase10b-transformation-api
git branch -D backup/phase2-auth-workspace-foundation
git branch -D backup/phase3-pre-multitenant-rls
git branch -D backup/phase4-async-task-processing
git branch -D backup/phase5-real-time-websockets-plus-enhanced-testing-framework-complete
git branch -D backup/phase6-file-processing-enhancement-complete
git branch -D backup/phase7-ai-provider-management-complete
git branch -D backup/phase8-advanced-security-and-monitoring-complete
git branch -D backup/phase9-complete-deployment-infrastructure

# Delete all merged feature branches
git branch -D feat/transformation-presets
git branch -D feat/phase10-frontend-enhancement-ux
git branch -D feat/phase10b-transformation-api-fixes
git branch -D feat/systematic-code-quality-improvements
git branch -D feat/advanced-security-and-monitoring
git branch -D feat/background-processing
git branch -D feat/database-foundation
git branch -D feat/deployment-patterns-and-containerization
git branch -D feat/file-processing-enhancement
git branch -D feat/jwt-refresh-tokens
git branch -D feat/multi-tenant-rls
git branch -D feat/real-time-collaboration

# Delete old misc branches
git branch -D update-documentation
git branch -D ai-provider-management
git branch -D dev-old

echo "✅ Cleanup complete!"
echo ""
echo "Remaining branches:"
git branch -a
