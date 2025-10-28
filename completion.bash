#!/usr/bin/env bash
# Bash completion for icon command
# Source this file: source /home/zack/dev/iconics/completion.bash
# Or add to ~/.bashrc: source /home/zack/dev/iconics/completion.bash

_icon_completion() {
    local cur prev commands categories

    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    commands="search use suggest md here cat info recent stats validate list add import generate help history again quick popular s u sug h i r st v l imp gen"
    categories="files network security tools ui emoji development"

    # Get icon names from catalog
    _get_icon_names() {
        local iconics_dir="/home/zack/dev/iconics"
        if [[ -f "$iconics_dir/icon-catalog.json" ]]; then
            python3 -c "import json; catalog = json.load(open('$iconics_dir/icon-catalog.json')); print(' '.join([icon['semanticName'] for icon in catalog['icons']]))" 2>/dev/null
        fi
    }

    case "${COMP_CWORD}" in
        1)
            # Complete main commands
            COMPREPLY=($(compgen -W "${commands}" -- "${cur}"))
            ;;
        2)
            # Complete based on previous command
            case "${prev}" in
                use|u|md|markdown|info|i|here|h)
                    # Complete with icon names
                    COMPREPLY=($(compgen -W "$(_get_icon_names)" -- "${cur}"))
                    ;;
                cat|category|list|l)
                    # Complete with categories
                    COMPREPLY=($(compgen -W "${categories}" -- "${cur}"))
                    ;;
                suggest|sug|quick)
                    # Complete with common contexts
                    contexts="authentication auth login security network api data database error warning info settings navigation files code search user"
                    COMPREPLY=($(compgen -W "${contexts}" -- "${cur}"))
                    ;;
                import|imp)
                    # Complete with CSV files
                    COMPREPLY=($(compgen -f -X '!*.csv' -- "${cur}"))
                    ;;
                generate|gen)
                    # Complete with .csv extension
                    COMPREPLY=($(compgen -f -X '!*.csv' -- "${cur}"))
                    ;;
                *)
                    ;;
            esac
            ;;
        *)
            # For commands that take multiple icon names
            case "${COMP_WORDS[1]}" in
                use|u|md|markdown|here|h)
                    COMPREPLY=($(compgen -W "$(_get_icon_names)" -- "${cur}"))
                    ;;
            esac
            ;;
    esac
}

complete -F _icon_completion icon
complete -F _icon_completion /home/zack/dev/iconics/icon
