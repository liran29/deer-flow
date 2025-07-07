#!/bin/bash
# Quick backup script for deer-flow project
# Usage: ./scripts/quick_backup.sh [commit_message]

set -e

echo "🔄 Quick Backup Script for deer-flow"
echo "=================================="

# Default commit message if none provided
COMMIT_MSG="${1:-Update: organize files and improve token management system}"

echo "📊 Checking repository status..."
git status --short

echo ""
echo "📝 Adding all changes..."
git add .

echo ""
echo "📋 Creating commit with message: '$COMMIT_MSG'"
git commit -m "$(cat <<EOF
$COMMIT_MSG

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

echo ""
echo "✅ Commit created successfully!"
git status

echo ""
echo "🚀 To push to remote, run:"
echo "   git push origin $(git branch --show-current)"
echo ""
echo "📁 Files organized and backed up! 🎯"