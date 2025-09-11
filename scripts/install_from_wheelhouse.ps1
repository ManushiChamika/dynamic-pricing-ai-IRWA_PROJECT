# Install all packages from local wheelhouse/ into the current venv
$wheelhouse = "wheelhouse"
python -m pip install --no-index --find-links=$wheelhouse -r requirements.txt
Write-Host "All packages installed from $wheelhouse"
