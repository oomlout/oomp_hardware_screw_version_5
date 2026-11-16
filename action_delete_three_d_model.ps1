[CmdletBinding(SupportsShouldProcess = $true)]
param()

$ErrorActionPreference = 'Stop'
$partsPath = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot 'parts'))
if (-not (Test-Path -LiteralPath $partsPath -PathType Container)) {
    throw "Parts folder not found: $partsPath"
}
if ((Get-Item -LiteralPath $partsPath).Attributes -band [System.IO.FileAttributes]::ReparsePoint) {
    throw "Cannot delete models through a linked parts folder: $partsPath"
}
$partsPrefix = $partsPath + [System.IO.Path]::DirectorySeparatorChar
$targets = @()
foreach ($part in Get-ChildItem -LiteralPath $partsPath -Directory -Force) {
    # Do not follow linked product folders outside this repository.
    if ($part.Attributes -band [System.IO.FileAttributes]::ReparsePoint) { continue }
    $target = [System.IO.Path]::GetFullPath((Join-Path $part.FullName 'three_d_model'))
    if (-not $target.StartsWith($partsPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Model folder is outside parts: $target"
    }
    if (-not (Test-Path -LiteralPath $target -PathType Container)) { continue }
    $entries = @((Get-Item -LiteralPath $target -Force)) + @(Get-ChildItem -LiteralPath $target -Recurse -Force)
    if ($entries | Where-Object { $_.Attributes -band [System.IO.FileAttributes]::ReparsePoint }) {
        throw "Cannot delete a model folder containing linked files or folders: $target"
    }
    $targets += $target
}

$removed = 0
foreach ($target in $targets) {
    if ($PSCmdlet.ShouldProcess($target, 'Delete generated 3D model folder')) {
        Remove-Item -LiteralPath $target -Recurse -Force
        Write-Host "Deleted: $target"
        $removed++
    }
}
if ($WhatIfPreference) {
    Write-Host "Preview complete: $($targets.Count) model folders would be deleted."
} else {
    Write-Host "Deleted $removed model folders. Working YAML recipes are preserved."
}
