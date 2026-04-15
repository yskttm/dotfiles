#!/usr/bin/env bash
# Claude Code status line command
# Displays all available information from the JSON input

input=$(cat)

# Core info
version=$(echo "$input" | jq -r '.version // empty')
model=$(echo "$input" | jq -r '.model.display_name // empty')
cwd=$(echo "$input" | jq -r '.cwd // empty')
session_name=$(echo "$input" | jq -r '.session_name // empty')

# Context window
used_pct=$(echo "$input" | jq -r '.context_window.used_percentage // empty')
remaining_pct=$(echo "$input" | jq -r '.context_window.remaining_percentage // empty')
ctx_size=$(echo "$input" | jq -r '.context_window.context_window_size // empty')
total_in=$(echo "$input" | jq -r '.context_window.total_input_tokens // empty')
total_out=$(echo "$input" | jq -r '.context_window.total_output_tokens // empty')
cur_in=$(echo "$input" | jq -r '.context_window.current_usage.input_tokens // empty')
cur_out=$(echo "$input" | jq -r '.context_window.current_usage.output_tokens // empty')
cache_write=$(echo "$input" | jq -r '.context_window.current_usage.cache_creation_input_tokens // empty')
cache_read=$(echo "$input" | jq -r '.context_window.current_usage.cache_read_input_tokens // empty')

# Rate limits
five_h_pct=$(echo "$input" | jq -r '.rate_limits.five_hour.used_percentage // empty')
# five_h_reset=$(echo "$input" | jq -r '.rate_limits.five_hour.resets_at // empty')
# seven_d_pct=$(echo "$input" | jq -r '.rate_limits.seven_day.used_percentage // empty')
# seven_d_reset=$(echo "$input" | jq -r '.rate_limits.seven_day.resets_at // empty')

# Optional: vim mode, agent, worktree, output_style
vim_mode=$(echo "$input" | jq -r '.vim.mode // empty')
agent_name=$(echo "$input" | jq -r '.agent.name // empty')
agent_type=$(echo "$input" | jq -r '.agent.type // empty')
worktree_name=$(echo "$input" | jq -r '.worktree.name // empty')
worktree_branch=$(echo "$input" | jq -r '.worktree.branch // empty')
output_style=$(echo "$input" | jq -r '.output_style.name // empty')

# Git branch (from cwd or workspace.current_dir)
git_dir=$(echo "$input" | jq -r '.workspace.current_dir // .cwd // empty')
git_branch=""
if [ -n "$git_dir" ]; then
  git_branch=$(git -C "$git_dir" --no-optional-locks symbolic-ref --short HEAD 2>/dev/null)
  if [ -z "$git_branch" ]; then
    git_branch=$(git -C "$git_dir" --no-optional-locks rev-parse --short HEAD 2>/dev/null)
  fi
fi

# Git worktree name from workspace (linked worktree)
git_worktree=$(echo "$input" | jq -r '.workspace.git_worktree // empty')

# ANSI colors
RESET='\033[0m'
BOLD='\033[1m'
DIM='\033[2m'
CYAN='\033[36m'
GREEN='\033[32m'
YELLOW='\033[33m'
BLUE='\033[34m'
MAGENTA='\033[35m'
RED='\033[31m'
WHITE='\033[37m'

parts=()

# Current time
parts+=("$(printf "${MAGENTA}$(date +%H:%M)${RESET}")")

# Version
# [ -n "$version" ] && parts+=("$(printf "${DIM}v${version}${RESET}")")

# Model
[ -n "$model" ] && parts+=("$(printf "${WHITE}${BOLD}${model}${RESET}")")

# Output style
[ -n "$output_style" ] && [ "$output_style" != "default" ] && parts+=("$(printf "${DIM}style:${output_style}${RESET}")")

# CWD (replace $HOME with ~, abbreviate all but last component)
if [ -n "$cwd" ]; then
  display_cwd="${cwd/#$HOME/~}"
  IFS='/' read -ra _components <<< "$display_cwd"
  _abbreviated=()
  _last_idx=$(( ${#_components[@]} - 1 ))
  for _i in "${!_components[@]}"; do
    if [ "$_i" -eq "$_last_idx" ]; then
      _abbreviated+=("${_components[$_i]}")
    else
      _abbreviated+=("${_components[$_i]:0:1}")
    fi
  done
  display_cwd=$(IFS='/'; echo "${_abbreviated[*]}")
  parts+=("$(printf "${BLUE}${display_cwd}${RESET}")")
fi

# Git branch
if [ -n "$git_branch" ]; then
  git_str="$(printf "${YELLOW}${git_branch}${RESET}")"
  [ -n "$git_worktree" ] && git_str="${git_str}$(printf "${DIM}(wt:${git_worktree})${RESET}")"
  parts+=("$git_str")
fi

# Session name
[ -n "$session_name" ] && parts+=("$(printf "${DIM}session:${session_name}${RESET}")")

# Context window usage
if [ -n "$used_pct" ]; then
  used_int=$(printf "%.0f" "$used_pct")
  if [ "$used_int" -ge 80 ]; then
    color="$RED"
  else
    color="$DIM"
  fi
  ctx_str="${color}ctx:${used_int}%%${RESET}"
  parts+=("$(printf "$ctx_str")")
fi

# Token counts (total cumulative)
# if [ -n "$total_in" ] || [ -n "$total_out" ]; then
#   tok_str="$(printf "${DIM}total-in:${total_in} out:${total_out}${RESET}")"
#   parts+=("$tok_str")
# fi

# Current usage tokens
# if [ -n "$cur_in" ] || [ -n "$cur_out" ]; then
#   cur_str="$(printf "${DIM}last-in:${cur_in} out:${cur_out}${RESET}")"
#   [ -n "$cache_write" ] && [ "$cache_write" != "0" ] && cur_str="${cur_str}$(printf "${DIM} cw:${cache_write}${RESET}")"
#   [ -n "$cache_read" ]  && [ "$cache_read"  != "0" ] && cur_str="${cur_str}$(printf "${DIM} cr:${cache_read}${RESET}")"
#   parts+=("$cur_str")
# fi

# Rate limits
if [ -n "$five_h_pct" ]; then
  five_int=$(printf "%.0f" "$five_h_pct")
  [ "$five_int" -ge 80 ] && rl_color="$RED" || rl_color="$DIM"
  parts+=("$(printf "${rl_color}5h:${five_int}%%${RESET}")")
fi
# if [ -n "$seven_d_pct" ]; then
#   seven_int=$(printf "%.0f" "$seven_d_pct")
#   reset_time=""
#   [ -n "$seven_d_reset" ] && reset_time=" rst:$(date -r "$seven_d_reset" +%m/%d 2>/dev/null)"
#   [ "$seven_int" -ge 80 ] && rl_color="$RED" || rl_color="$DIM"
#   parts+=("$(printf "${rl_color}7d:${seven_int}%%${reset_time}${RESET}")")
# fi

# Vim mode
[ -n "$vim_mode" ] && parts+=("$(printf "${YELLOW}[${vim_mode}]${RESET}")")

# Agent
if [ -n "$agent_name" ]; then
  agent_str="$(printf "${GREEN}agent:${agent_name}${RESET}")"
  [ -n "$agent_type" ] && agent_str="${agent_str}$(printf "${DIM}(${agent_type})${RESET}")"
  parts+=("$agent_str")
fi

# Worktree
if [ -n "$worktree_name" ]; then
  wt_str="$(printf "${YELLOW}worktree:${worktree_name}${RESET}")"
  [ -n "$worktree_branch" ] && wt_str="${wt_str}$(printf "${DIM}(${worktree_branch})${RESET}")"
  parts+=("$wt_str")
fi

# Join all parts with separator
sep="$(printf "${DIM} | ${RESET}")"
result=""
for part in "${parts[@]}"; do
  if [ -z "$result" ]; then
    result="$part"
  else
    result="${result}${sep}${part}"
  fi
done

printf "%b\n" "$result"
