# Download all wheels for requirements.txt into wheelhouse/
$wheelhouse = "wheelhouse"
if (!(Test-Path $wheelhouse)) { New-Item -ItemType Directory -Path $wheelhouse }
python -m pip download -r requirements.txt -d $wheelhouse
Write-Host "All wheels downloaded to $wheelhouse"
