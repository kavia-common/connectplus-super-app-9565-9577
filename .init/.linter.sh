#!/bin/bash
cd /home/kavia/workspace/code-generation/connectplus-super-app-9565-9577/backend_service
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

