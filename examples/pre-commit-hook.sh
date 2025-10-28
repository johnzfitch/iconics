#!/usr/bin/env bash
# Git pre-commit hook example for icon suggestions
# Install: cp examples/pre-commit-hook.sh .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit

# Check if README was modified and suggest icons
if git diff --cached --name-only | grep -q "README.md"; then
    echo "📝 README.md modified. Consider adding icons:"
    echo "   /home/zack/dev/iconics/icon suggest <topic>"
    echo "   /home/zack/dev/iconics/icon use <icon-names>"
fi

# Allow commit to proceed
exit 0
