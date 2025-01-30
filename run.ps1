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
    Write-Host "No virtual environment found in the current directory"
    Write-Host "" 
    Write-Host "To create a virtual environment, run the command: python -m venv .venv"
    Write-Host "To create a conda environment, run the command: conda create --prefix .conda python=3.11"
    Write-Host ""
    Write-Host "After creating the virtual environment, run the command: source .venv/bin/activate or source .conda/bin/activate to active the virtual environment, then run the command: pip install -r requirements.txt to install the required packages"
    Write-Host ""
    Write-Host "Once your virtual environment has been created, and the required packages have been installed, you can re-run this script"
    exit 1
}

# Run the workflow.py script with the arguments passed to the run.ps1 script
& python .\workflow.py @args