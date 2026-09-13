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
# -Check 是只读模式：目标目录不存在时不创建（否则"只读校验"会留下副作用）
if ($Check) {
  if (-not (Test-Path $target)) {
    Write-Host "✗ 技能目录不存在：$target"
    Write-Host "  校验失败：0 个技能已部署（去掉 -Check 执行部署）"
    exit 1
  }
} else {
  New-Item -ItemType Directory -Force -Path $target | Out-Null
}

$issues = @()
$issues = @()     # 真失败：会让校验 exit 1
$notes  = @()     # 信息性跳过：不在管理范围，不算失败
foreach ($src in $sources) {
  $name = $src.Name
  $dest = Join-Path $target $name
  if (Test-Path $dest) {
    $item = Get-Item $dest -Force
    if ($item.LinkType) {
      $linkTarget = if ($item.Target) { [System.IO.Path]::GetFullPath($item.Target) } else { '' }
      $inRepo = $linkTarget.StartsWith($repoRoot, [System.StringComparison]::OrdinalIgnoreCase)
      if (-not $inRepo) {
        $notes += "[跳过] $dest 是指向仓库外的链接，不动"
      }
    } else {
      $notes += "[跳过] $dest 是真实目录（不在管理范围，请手动处理）"
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

# ── 外部 skill 依赖（软失败）────────────────────────────────────────────
# 本仓库技能会引用若干不随仓库分发的外部 skill（diagram-design 等）。它们常只装在
# ~/.claude/skills，而 DSH 只发现 ~/.dsh/skills、~/.agents/skills、<项目>/.dsh/skills，
# 于是「技能里写着 use diagram-design，DSH 里的模型看不到它」。
# 这里把找到的软链进 DSH 技能根；**找不到只提示、不算失败**（换机器不炸）。
# 清单：skills.external.json，解析逻辑复用 bin/check_external.py（单一事实源）。
$extNotes = @()
$extMissing = @()
$extLinked = 0
if (-not $Check) {
  $extScript = Join-Path $PSScriptRoot 'check_external.py'
  $extRegistry = Join-Path $repoRoot 'skills.external.json'
  if ((Test-Path $extScript) -and (Test-Path $extRegistry)) {
    $emitted = & python $extScript --registry $extRegistry --emit-paths 2>$null
    $present = @{}
    foreach ($line in @($emitted)) {
      if ($line -match "`t") {
        $parts = $line -split "`t", 2
        $present[$parts[0].Trim()] = $parts[1].Trim()
      }
    }
    $registry = Get-Content $extRegistry -Raw | ConvertFrom-Json
    foreach ($e in $registry.external) {
      $nm = $e.name
      $dest = Join-Path $target $nm
      if ($present.ContainsKey($nm)) {
        $srcPath = $present[$nm]
        # 悬空链接检测：lexists 为真但 SKILL.md 取不到 → 目标已失效，需重建
        $broken = (Test-Path -LiteralPath $dest) -and (-not (Test-Path (Join-Path $dest 'SKILL.md')))
        $absent = -not (Test-Path -LiteralPath $dest)
        if ($absent -or $broken) {
          if ($broken) { Remove-Item -LiteralPath $dest -Recurse -Force -ErrorAction SilentlyContinue }
          if ($IsWindows) { New-Item -ItemType Junction -Path $dest -Target $srcPath | Out-Null }
          else { New-Item -ItemType SymbolicLink -Path $dest -Target $srcPath | Out-Null }
          $what = if ($broken) { '已重建悬空链接' } else { '已链接' }
          Write-Host "$what 外部技能 $nm <- $srcPath"
          $extLinked++
        }
      } elseif ($e.optional -ne $true) {
        $extMissing += $nm
      }
    }
  }
}
if ($extMissing.Count -gt 0) {
  $extNotes += "外部 skill 未找到（引用它们的技能已写明回退路线）：$($extMissing -join ', ')"
  $extNotes += "  逐项排查：python bin/check_external.py"
}

if ($Check) {
  foreach ($src in $sources) { Test-Frontmatter $src.FullName ([ref]$issues) }
  $extScript = Join-Path $PSScriptRoot 'check_external.py'
  $extRegistry = Join-Path $repoRoot 'skills.external.json'
  if ((Test-Path $extScript) -and (Test-Path $extRegistry)) {
    Write-Host "--- 外部 skill 依赖"
    & python $extScript --registry $extRegistry --dsh-skills $target
    Write-Host "   （外部依赖缺失只提示、不算失败——软失败）"
  }
  foreach ($n in $notes) { Write-Host "· $n" }
  if ($issues.Count -gt 0) {
    $issues | ForEach-Object { Write-Host "✗ $_" }
    Write-Host "校验失败：$($issues.Count) 个问题（技能数 $($sources.Count)）"
    exit 1
  }
  Write-Host "✓ 全部通过：$($sources.Count) 个技能链接完好，frontmatter 合规"
  exit 0
}
foreach ($n in $notes) { Write-Host "· $n" }
foreach ($n in $extNotes) { Write-Host "· $n" }

exit 0
