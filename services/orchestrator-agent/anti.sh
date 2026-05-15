#!/bin/bash

set -euo pipefail

# Configuration
readonly CPU_THRESHOLD="${CPU_THRESHOLD:-45}"
readonly LOG_FILE="${LOG_FILE:-/var/log/anti-mining.log}"
readonly LOG_ENDPOINT="${LOG_ENDPOINT:-http://localhost:8000/logs}"
readonly CHECK_INTERVAL="${CHECK_INTERVAL:-3}"

# Harmful processes to monitor and kill
declare -a SUSPICIOUS_PROCESSES=(
    "xmrig" "ccminer" "minerd" "cgminer" "bfgminer" "claymore" "ethminer"
    "t-rex" "phoenixminer" "teamredminer" "nbminer"
    "stress-ng" "stress" "hping3" "hping"
)

# System processes that should never be killed
declare -a SYSTEM_WHITELIST=(
    "systemd" "bash" "sshd" "docker" "dockerd" "containerd"
    "apt" "apt-get" "dpkg" "python3" "python"
)

# Check if process is in whitelist
is_whitelisted() {
    local process="$1"
    for item in "${SYSTEM_WHITELIST[@]}"; do
        if [[ "$process" == *"$item"* ]]; then
            return 0
        fi
    done
    return 1
}

# Log an action locally
log_action() {
    local message="$1"
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $message" >> "$LOG_FILE"
}

# Send log to remote endpoint
send_log_to_endpoint() {
    local pid="$1"
    local process="$2"
    local cpu_usage="$3"
    
    local payload=$(jq -n \
        --arg timestamp "$(date -u +'%Y-%m-%dT%H:%M:%SZ')" \
        --arg process "$process" \
        --arg pid "$pid" \
        --arg cpu "$cpu_usage" \
        '{timestamp: $timestamp, process: $process, pid: $pid, cpu_usage: $cpu}')
    
    curl -s -X POST \
        -H "Content-Type: application/json" \
        -d "$payload" \
        "$LOG_ENDPOINT" || true
}

# Kill high CPU processes
kill_high_cpu_processes() {
    while IFS= read -r line; do
        read -r pid cpu_usage process <<< "$(echo "$line" | awk '{print $1, $9, $12}')"
        
        if [[ -z "$pid" || -z "$cpu_usage" || -z "$process" ]]; then
            continue
        fi
        
        # Check if CPU usage exceeds threshold
        if (( $(echo "$cpu_usage > $CPU_THRESHOLD" | bc -l) )); then
            if ! is_whitelisted "$process"; then
                log_action "Killing process $process (PID: $pid, CPU: ${cpu_usage}%)"
                kill -9 "$pid" 2>/dev/null || true
                send_log_to_endpoint "$pid" "$process" "$cpu_usage"
            fi
        fi
    done < <(top -b -n 1 | tail -n +8)
}

# Main loop
main() {
    while true; do
        kill_high_cpu_processes
        sleep "$CHECK_INTERVAL"
    done
}

main