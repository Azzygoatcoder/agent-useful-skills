#!/usr/bin/env pwsh
# redeploy-skills.ps1 — 把本仓库的技能部署为 DSH 用户技能（链接式），并自愈缺失/失效链接。
#
# 设计原则（通用性）：
#   - 不包含任何本机路径；脚本位置决定仓库根，目标目录可用环境变量覆盖。
#   - 技能来源：<repo>/skills/* 与 <repo>/plugins/*/skills/*（仓库自身结构契约）。
#   - 链接管理范围：只管理「指向本仓库」的链接；真实目录与仓库外链接一律不碰。
#   - 平台无关：Windows 用目录联接(Junction，无需管理员)，macOS/Linux 用符号链接。
#
# 用法：
#   pwsh bin/redeploy-skills.ps1            # 部署 / 自愈（创建缺失链接、清理失效链接）
#   pwsh bin/redeploy-skills.ps1 -Check     # 只读校验（链接完整性 + frontmatter），有问题时退出码 1
#
# 环境变量覆盖：
#   DSH_HOME    自定义 dsh 主目录（缺省 $HOME/.dsh）
#   DSH_SKILLS  自定义技能目录（缺省 <DSH_HOME>/skills）
param(
  [switch]$Check
)
$ErrorActionPreference = 'Stop'

$repoRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..'))
$dshHome  = if ($env:DSH_HOME)   { $env:DSH_HOME }   else { Join-Path $HOME '.dsh' }
$target   = if ($env:DSH_SKILLS) { $env:DSH_SKILLS } else { Join-Path $dshHome 'skills' }

$manifestPath = Join-Path $repoRoot 'skills.manifest.json'
if (-not (Test-Path $manifestPath)) {
  Write-Error "缺少 skills.manifest.json：$manifestPath"
  exit 2
}
$manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json
$defaultSkillNames = @($manifest.default)

function Get-SkillSources {
  $dirs = @()
  $top = Join-Path $repoRoot 'skills'
  if (Test-Path $top) { $dirs += Get-ChildItem $top -Directory }
  $plugins = Join-Path $repoRoot 'plugins'
  if (Test-Path $plugins) {
    Get-ChildItem $plugins -Directory | ForEach-Object {
      $s = Join-Path $_.FullName 'skills'
      if (Test-Path $s) { $dirs += Get-ChildItem $s -Directory }
    }
  }
  $dirs
}

function Test-Frontmatter([string]$skillDir, [ref]$issues) {
  $skillMd = Join-Path $skillDir 'SKILL.md'
  if (-not (Test-Path $skillMd)) { $issues.Value += "[frontmatter] $($skillDir | Split-Path -Leaf): 缺 SKILL.md"; return }
  $head = (Get-Content $skillMd -TotalCount 12) -join "`n"
  $nameMatch = [regex]::Match($head, '(?m)^name:\s*(.+)$')
  if (-not $nameMatch.Success) { $issues.Value += "[frontmatter] 缺 name: $($skillDir | Split-Path -Leaf)"; return }
  $name = $nameMatch.Groups[1].Value.Trim().Trim('"', "'")
  if ($name -ne ($skillDir | Split-Path -Leaf)) { $issues.Value += "[frontmatter] name($name) != 目录名($($skillDir | Split-Path -Leaf))" }
  $desc = [regex]::Match($head, '(?m)^description:\s*(\S|$)')
  if (-not $desc.Success) { $issues.Value += "[frontmatter] 缺 description: $($skillDir | Split-Path -Leaf)" }
}

$allSources = @(Get-SkillSources)
$missingFromManifest = $defaultSkillNames | Where-Object { $_ -notin $allSources.Name }
if ($missingFromManifest) {
  Write-Warning "skills.manifest.json 中的技能在仓库未找到: $($missingFromManifest -join ', ')"
}
$sources = @($allSources | Where-Object { $_.Name -in $defaultSkillNames })
if ($sources.Count -eq 0) {
  Write-Error "默认技能清单为空或仓库内未找到对应目录（检查 skills.manifest.json）"
  exit 2
}
$names = $sources | ForEach-Object { $_.Name }
$dups = $names | Group-Object | Where-Object Count -gt 1
if ($dups) {
  Write-Warning "存在同名技能（会互相覆盖）: $(($dups | ForEach-Object Name) -join ', ')"
}
New-Item -ItemType Directory -Force -Path $target | Out-Null

$issues = @()
foreach ($src in $sources) {
  $name = $src.Name
  $dest = Join-Path $target $name
  if (Test-Path $dest) {
    $item = Get-Item $dest -Force
    if ($item.LinkType) {
      $linkTarget = if ($item.Target) { [System.IO.Path]::GetFullPath($item.Target) } else { '' }
      $inRepo = $linkTarget.StartsWith($repoRoot, [System.StringComparison]::OrdinalIgnoreCase)
      if (-not $inRepo) {
        $issues += "[跳过] $dest 是指向仓库外的链接，不动"
      }
    } else {
      $issues += "[跳过] $dest 是真实目录（不在管理范围，请手动处理）"
    }
  } else {
    if ($Check) { $issues += "[缺失] $name" }
    else {
      if ($IsWindows) { New-Item -ItemType Junction -Path $dest -Target ([System.IO.Path]::GetFullPath($src.FullName)) | Out-Null }
      else { New-Item -ItemType SymbolicLink -Path $dest -Target ([System.IO.Path]::GetFullPath($src.FullName)) | Out-Null }
      Write-Host "已链接 $name <- $($src.FullName)"
    }
  }
}

# 清理：指向本仓库但已不在当前技能清单里的失效链接
if (Test-Path $target) {
  Get-ChildItem $target -Force | Where-Object { $_.LinkType -and $_.Name -notin $names } | ForEach-Object {
    $t = if ($_.Target) { [System.IO.Path]::GetFullPath($_.Target) } else { '' }
    if ($t.StartsWith($repoRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
      if ($Check) { $issues += "[失效链接] $($_.Name)" }
      else { Remove-Item $_.FullName -Force; Write-Host "已清理失效链接 $($_.Name)" }
    }
  }
}

if ($Check) {
  foreach ($src in $sources) { Test-Frontmatter $src.FullName ([ref]$issues) }
  if ($issues.Count -gt 0) {
    $issues | ForEach-Object { Write-Host "✗ $_" }
    Write-Host "校验失败：$($issues.Count) 个问题（技能数 $($sources.Count)）"
    exit 1
  }
  Write-Host "✓ 全部通过：$($sources.Count) 个技能链接完好，frontmatter 合规"
  exit 0
}

exit 0
