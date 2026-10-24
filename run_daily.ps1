Set-Location "D:\os_pipeline"

$cultura = [System.Globalization.CultureInfo]::InvariantCulture
$fim = Get-Date
$inicio = $fim.AddDays(-7)

& "D:\os_pipeline\.venv\Scripts\python.exe" "src\main.py" `
    --inicio $inicio.ToString("MM/dd/yyyy", $cultura) `
    --fim $fim.ToString("MM/dd/yyyy", $cultura)

exit $LASTEXITCODE