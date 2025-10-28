#compdef icon
# Zsh completion for icon command
# Source this file: source /home/zack/dev/iconics/completion.zsh
# Or add to ~/.zshrc: source /home/zack/dev/iconics/completion.zsh

_icon() {
    local -a commands categories contexts icon_names

    commands=(
        'search:Search for icons by tag/name'
        's:Search for icons (short)'
        'use:Export icons and generate markdown'
        'u:Export icons (short)'
        'suggest:Get context-aware icon suggestions'
        'sug:Get suggestions (short)'
        'md:Generate markdown snippet'
        'markdown:Generate markdown snippet'
        'here:Export to current directory'
        'h:Export here (short)'
        'cat:Export all icons from category'
        'category:Export all icons from category'
        'info:Show detailed icon information'
        'i:Show info (short)'
        'recent:Show recently cataloged icons'
        'r:Show recent (short)'
        'stats:Show library statistics'
        'st:Show stats (short)'
        'validate:Validate catalog integrity'
        'v:Validate (short)'
        'list:List icons in category'
        'l:List category (short)'
        'add:Add new icon to catalog'
        'import:Bulk import from CSV'
        'imp:Import CSV (short)'
        'generate:Auto-generate CSV from filenames'
        'gen:Generate CSV (short)'
        'history:Show recently used icons'
        'again:Re-export last used icons'
        'quick:Quick mode (suggest + export top 3)'
        'popular:Show most popular icons'
        'help:Show help message'
    )

    categories=(files network security tools ui emoji development)
    contexts=(authentication auth login security network api data database error warning info settings navigation files code search user)

    # Get icon names from catalog
    _get_icon_names() {
        local iconics_dir="/home/zack/dev/iconics"
        if [[ -f "$iconics_dir/icon-catalog.json" ]]; then
            icon_names=(${(f)"$(python3 -c "import json; catalog = json.load(open('$iconics_dir/icon-catalog.json')); print('\n'.join([icon['semanticName'] for icon in catalog['icons']]))" 2>/dev/null)"})
        fi
    }

    case $CURRENT in
        2)
            # Complete main commands
            _describe 'commands' commands
            ;;
        3)
            # Complete based on previous command
            case $words[2] in
                use|u|md|markdown|info|i|here|h)
                    _get_icon_names
                    _describe 'icon names' icon_names
                    ;;
                cat|category|list|l)
                    _describe 'categories' categories
                    ;;
                suggest|sug|quick)
                    _describe 'contexts' contexts
                    ;;
                import|imp|generate|gen)
                    _files -g "*.csv"
                    ;;
            esac
            ;;
        *)
            # For commands that take multiple arguments
            case $words[2] in
                use|u|md|markdown|here|h)
                    _get_icon_names
                    _describe 'icon names' icon_names
                    ;;
            esac
            ;;
    esac
}

_icon "$@"
