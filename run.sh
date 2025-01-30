#!/bin/bash

if [ -d .venv ]; then ## Check if there is a .venv folder in the current directory, and if there is, activate it
    source .venv/bin/activate
elif [ -d .conda ]; then ## Check if there is a .conda folder in the current directory, and if there is, activate it
    source .conda/bin/activate
else 
    echo "No virtual environment found in the current directory"
    exit 1
fi

./workflow.py $@ ## Run the workflow.py script with the arguments passed to the run.sh script
