#!/usr/bin/env bash
# Git pre-commit hook example for icon suggestions
# Install: cp examples/pre-commit-hook.sh .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit

# Check if README was modified and suggest icons
if git diff --cached --name-only | grep -q "README.md"; then
    echo "📝 README.md modified. Consider adding icons:"
    echo "   $ICONICS_ROOT/icon suggest <topic>"
    echo "   $ICONICS_ROOT/icon use <icon-names>"
fi

# Allow commit to proceed
exit 0
