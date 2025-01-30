#!/bin/bash

if [ -d .venv ]; then ## Check if there is a .venv folder in the current directory, and if there is, activate it
    source .venv/bin/activate
elif [ -d .conda ]; then ## Check if there is a .conda folder in the current directory, and if there is, activate it
    source .conda/bin/activate
else 
    echo "No virtual environment found in the current directory"
    echo "" 
    echo "To create a virtual environment, run the command: python -m venv .venv"
    echo "To create a conda environment, run the command: conda create --prefix .conda python=3.11"
    echo ""
    echo "After creating the virtual environment, run the command: source .venv/bin/activate or source .conda/bin/activate to active the virtual environment, then run the command: pip install -r requirements.txt to install the required packages"
    echo ""
    echo "Once your virtual environment has been created, and the required packages have been installed, you can re-run this script"
    exit 1
fi

./workflow.py $@ ## Run the workflow.py script with the arguments passed to the run.sh script
