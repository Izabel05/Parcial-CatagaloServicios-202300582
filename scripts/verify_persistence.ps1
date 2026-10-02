$ErrorActionPreference = 'Stop'

$composeArgs = @('-f', 'compose.test.yaml', '-p', 'catalogo-servicios-tests')
$probeSql = @"
CREATE TABLE IF NOT EXISTS persistence_probe (id INTEGER PRIMARY KEY, marker TEXT NOT NULL);
INSERT INTO persistence_probe (id, marker) VALUES (1, 'P12-ok')
ON CONFLICT (id) DO UPDATE SET marker=EXCLUDED.marker;
"@

try {
    docker compose @composeArgs up -d db
    $ready = $false
    for ($attempt = 1; $attempt -le 30; $attempt++) {
        docker compose @composeArgs exec -T db pg_isready -U catalogo_test -d catalogo_servicios_test *> $null
        if ($LASTEXITCODE -eq 0) {
            $ready = $true
            break
        }
        Start-Sleep -Seconds 2
    }
    if (-not $ready) {
        throw 'P12 no pudo esperar a que PostgreSQL estuviera disponible.'
    }
    docker compose @composeArgs exec -T db psql -U catalogo_test -d catalogo_servicios_test -v ON_ERROR_STOP=1 -c $probeSql
    docker compose @composeArgs restart db
    $ready = $false
    for ($attempt = 1; $attempt -le 30; $attempt++) {
        docker compose @composeArgs exec -T db pg_isready -U catalogo_test -d catalogo_servicios_test *> $null
        if ($LASTEXITCODE -eq 0) {
            $ready = $true
            break
        }
        Start-Sleep -Seconds 2
    }
    if (-not $ready) {
        throw 'P12 no pudo esperar a que PostgreSQL volviera a estar disponible.'
    }
    $marker = docker compose @composeArgs exec -T db psql -U catalogo_test -d catalogo_servicios_test -tAc "SELECT marker FROM persistence_probe WHERE id=1;"
    if ($marker.Trim() -ne 'P12-ok') {
        throw 'P12 falló: el marcador no persistió después del reinicio.'
    }
    Write-Output 'P12 OK: los datos persistieron después de reiniciar el contenedor sin eliminar el volumen.'
}
finally {
    docker compose @composeArgs down
}
