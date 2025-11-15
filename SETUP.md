# Iconics Setup Guide

## Basic Usage

No installation required! Use the icon command directly:

```bash
~/iconics/icon search security
~/iconics/icon use lock shield
```

Or if you've cloned to a different location:

```bash
/path/to/iconics/icon search security
/path/to/iconics/icon use lock shield
```

## Optional: Add Alias

For convenience, add to your `~/.bashrc` or `~/.zshrc`:

```bash
alias icon='~/iconics/icon'
```

Or if cloned elsewhere:

```bash
alias icon='/path/to/iconics/icon'
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

## Optional: Environment Variable

Set the `ICONICS_DIR` environment variable to help scripts find the icon library:

```bash
export ICONICS_DIR=~/iconics
```

Add this to your `~/.bashrc` or `~/.zshrc` to make it permanent.

## Optional: Shell Completion

### Bash Completion

Add to `~/.bashrc`:

```bash
source ~/iconics/completion.bash
```

### Zsh Completion

Add to `~/.zshrc`:

```bash
source ~/iconics/completion.zsh
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
cp ~/iconics/examples/pre-commit-hook.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

## Optional: Project Preferences

Create a `.iconics` file in your project root to customize behavior (if the example file exists):

```bash
cp ~/iconics/examples/.iconics /path/to/your/project/
```

Edit the file to set preferred icons and contexts for your project type.

---

That's it! The system works out of the box with no required setup.
