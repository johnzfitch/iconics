# Iconics Setup Guide

## Basic Usage

No installation required! Use the icon command directly:

```bash
/home/zack/dev/iconics/icon search security
/home/zack/dev/iconics/icon use lock shield
```

## Optional: Add Alias

For convenience, add to your `~/.bashrc` or `~/.zshrc`:

```bash
alias icon='/home/zack/dev/iconics/icon'
```

Then reload:
```bash
source ~/.bashrc  # or source ~/.zshrc
```

Now you can use:
```bash
icon search security
icon use lock shield
```

## Optional: Shell Completion

### Bash Completion

Add to `~/.bashrc`:

```bash
source /home/zack/dev/iconics/completion.bash
```

### Zsh Completion

Add to `~/.zshrc`:

```bash
source /home/zack/dev/iconics/completion.zsh
```

Then reload your shell:
```bash
source ~/.bashrc  # or source ~/.zshrc
```

**Benefits:**
- Tab-complete commands: `icon s<TAB>` → `icon search`
- Tab-complete icon names: `icon use lo<TAB>` → `icon use lock`
- Tab-complete categories: `icon list se<TAB>` → `icon list security`
- Tab-complete contexts: `icon suggest auth<TAB>` → `icon suggest authentication`

## Optional: Git Hooks

To get icon suggestions when modifying READMEs:

```bash
# From your project directory
cp /home/zack/dev/iconics/examples/pre-commit-hook.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

## Optional: Project Preferences

Create a `.iconics` file in your project root to customize behavior:

```bash
cp /home/zack/dev/iconics/examples/.iconics /path/to/your/project/
```

Edit the file to set preferred icons and contexts for your project type.

---

That's it! The system works out of the box with no required setup.
