export EDITOR="code"
export PATH="$HOME/.local/bin:$PATH"

HISTSIZE=1000000
SAVEHIST=1000000
setopt extended_history share_history
setopt no_flow_control

(type brew &>/dev/null 2>&1) && eval "$(/opt/homebrew/bin/brew shellenv)"
(type mise &>/dev/null 2>&1) && eval "$(mise activate zsh)"

alias ls='eza -F'
alias ll='eza -al'
alias h='history -500'
alias current_folder='basename $PWD'
alias dc='docker compose'
alias dc_run='docker compose run --rm $(current_folder)'
alias dc_logs='docker compose logs -f -t --tail=200 $(current_folder)'
alias dc_restart='docker compose up -d $(current_folder)'
