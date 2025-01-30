# Check if there is a .venv folder in the current directory, and if there is, activate it
if (Test-Path -Path .\.venv) {
    & .\.venv\Scripts\Activate.ps1
}
# Check if there is a .conda folder in the current directory, and if there is, activate it
elseif (Test-Path -Path .\.conda) {
    & .\.conda\Scripts\Activate.ps1
}
else {
    Write-Host "No virtual environment found in the current directory"
    exit 1
}

# Run the workflow.py script with the arguments passed to the run.ps1 script
& python .\workflow.py @args