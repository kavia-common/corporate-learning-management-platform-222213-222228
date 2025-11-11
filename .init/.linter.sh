#!/bin/bash
cd /home/kavia/workspace/code-generation/corporate-learning-management-platform-222213-222228/django_backend
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

