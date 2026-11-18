param(
    [string]$Output = 'experiments/network-ipv6-check-v1/report.json'
)
# Read-only Windows diagnostic. Two bounded TCP handshakes; no packet capture,
# browser/adapter/routing changes, HTTP requests or model input generation.
$ErrorActionPreference = 'Stop'
if (Test-Path -LiteralPath $Output) { throw 'Preserve the existing report; choose a new output path.' }
$wifi = @([System.Net.NetworkInformation.NetworkInterface]::GetAllNetworkInterfaces() |
    Where-Object { $_.Name -eq 'Wi-Fi' } | ForEach-Object {
        $properties = $_.GetIPProperties()
        $addresses = @($properties.UnicastAddresses | Where-Object {
            $_.Address.AddressFamily -eq [System.Net.Sockets.AddressFamily]::InterNetworkV6
        })
        [PSCustomObject]@{
            name = $_.Name
            state = $_.OperationalStatus.ToString()
            supports_ipv6 = $_.Supports([System.Net.NetworkInformation.NetworkInterfaceComponent]::IPv6)
            ipv6_address_count = $addresses.Count
            ipv6_link_local_count = @($addresses | Where-Object { $_.Address.IsIPv6LinkLocal }).Count
            ipv6_global_candidate_count = @($addresses | Where-Object {
                -not $_.Address.IsIPv6LinkLocal -and -not $_.Address.IsIPv6SiteLocal -and
                -not $_.Address.IsIPv6Multicast -and -not [System.Net.IPAddress]::IsLoopback($_.Address) -and
                -not $_.Address.ToString().StartsWith('fd') -and -not $_.Address.ToString().StartsWith('fc')
            }).Count
        }
    })
$routes = & route.exe print -6
if ($LASTEXITCODE -ne 0) { throw 'Native IPv6 route query failed.' }
$targetName = 'www.youtube.com'
$dns6 = @(Resolve-DnsName -Name $targetName -Type AAAA -DnsOnly |
    Where-Object { [int]$_.Type -eq 28 -and $_.Name -eq $targetName } |
    Select-Object -ExpandProperty IPAddress -Unique)
$systemAddresses = @([System.Net.Dns]::GetHostAddresses($targetName))
$v4 = @($systemAddresses | Where-Object { $_.AddressFamily -eq [System.Net.Sockets.AddressFamily]::InterNetwork })

function Test-BoundedConnection([string]$Address, [System.Net.Sockets.AddressFamily]$Family) {
    if (-not $Address) { return @{ status = 'no_address'; family = $Family.ToString() } }
    $client = [System.Net.Sockets.TcpClient]::new($Family)
    $timer = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        $task = $client.ConnectAsync([System.Net.IPAddress]::Parse($Address), 443)
        if (-not $task.Wait(3000)) {
            return @{ status = 'timeout'; family = $Family.ToString(); timeout_ms = 3000 }
        }
        return @{ status = 'connected'; family = $Family.ToString(); elapsed_ms = $timer.Elapsed.TotalMilliseconds }
    } catch {
        $failure = $_.Exception.GetBaseException()
        $details = @{ status = 'failed'; family = $Family.ToString(); error = $failure.Message }
        if ($failure -is [System.Net.Sockets.SocketException]) {
            $details.socket_error = $failure.SocketErrorCode.ToString()
            $details.native_error_code = $failure.NativeErrorCode
        }
        return $details
    } finally {
        $client.Dispose()
    }
}

$ipv4Probe = Test-BoundedConnection $(if ($v4.Count) { $v4[0].ToString() }) ([System.Net.Sockets.AddressFamily]::InterNetwork)
$ipv6Probe = Test-BoundedConnection $(if ($dns6.Count) { $dns6[0] }) ([System.Net.Sockets.AddressFamily]::InterNetworkV6)
$report = [ordered]@{
    created_utc = [DateTime]::UtcNow.ToString('o')
    interface = $wifi
    ipv6_default_route_lines = @($routes | Where-Object { $_ -match '\s::/0\s' }).Count
    dns = @{
        target = $targetName
        explicit_aaaa_records = $dns6.Count
        system_resolver_ipv4_count = $v4.Count
        system_resolver_ipv6_count = @($systemAddresses | Where-Object {
            $_.AddressFamily -eq [System.Net.Sockets.AddressFamily]::InterNetworkV6
        }).Count
    }
    tcp443_ipv4 = $ipv4Probe
    tcp443_ipv6 = $ipv6Probe
    capture_started = $false
    settings_changed = $false
    source_sha256 = (Get-FileHash -LiteralPath $PSCommandPath -Algorithm SHA256).Hash.ToLowerInvariant()
    limitations = 'Point-in-time Windows configuration and TCP reachability. Does not test QUIC/UDP quality, identify router versus ISP cause, or establish a permanent network state. No client addresses exported. Family is diagnostic metadata only.'
}
$parent = Split-Path -Parent $Output
if ($parent) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
$json = $report | ConvertTo-Json -Depth 8
[System.IO.File]::WriteAllText([System.IO.Path]::GetFullPath($Output), $json, [System.Text.UTF8Encoding]::new($false))
$json
