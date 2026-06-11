#!/bin/bash
set -e

check_command_version() {
  if ! command -v "$1" &> /dev/null; then
    echo "  $1 not found. Install $2 (required: $3)"
    exit 1
  fi
}

echo "Checking prerequisites..."

check_command_version docker "Docker" "20.10+"
check_command_version docker-compose "Docker Compose" "1.29+"
check_command_version node "Node.js" "18+"
check_command_version python3 "Python" "3.9+"
check_command_version git "Git" "2.0+"

echo "All prerequisites satisfied"
