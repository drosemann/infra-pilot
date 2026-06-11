#!/bin/bash
set -e

echo "Installing dependencies..."

npm install --prefix services/management-panel
npm install --prefix services/discord-service
if [ -f "mobile/package.json" ]; then
  npm install --prefix mobile
fi

pip install -r requirements.txt
pip install -r services/orchestrator-agent/requirements.txt
pip install -r services/integration-service/requirements.txt

echo "All dependencies installed"
