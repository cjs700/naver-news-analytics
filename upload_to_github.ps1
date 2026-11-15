# ====================================================================
#  upload_to_github.ps1
#  G 드라이브(Google Drive)의 뉴스 분석 결과 중 CSV/TXT 와 코드만
#  D:\projects\Python\naver-news-analytics 저장소로 동기화한 뒤
#  GitHub(cjs700/naver-news-analytics)에 자동 커밋·업로드한다.
#
#  Windows 작업 스케줄러가 매일 10:00 에 실행한다.
#  (09:00 에 도는 News_analytics.py 분석이 끝난 뒤 여유를 두고 실행)
#
#  실행 기록: G:\...\News\logs\github_upload.log
#  수동 실행: 이 파일 우클릭 → "PowerShell에서 실행"
# ====================================================================
$ErrorActionPreference = "Stop"

$SRC = "G:\내 드라이브\03_데이터분석_실습노트북\News"
$DST = "D:\projects\Python\naver-news-analytics"
$LOG = Join-Path $SRC "logs\github_upload.log"
$GIT = "C:\Anaconda3\Library\bin\git.exe"

function Write-Log($msg) {
    $line = "{0}  {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $msg
    try { Add-Content -Path $LOG -Value $line -Encoding UTF8 } catch { }
    Write-Output $line
}

try {
    Write-Log "===== 자동 업로드 시작 ====="

    # ── 0. 사전 점검 ────────────────────────────────────────────
    if (-not (Test-Path $SRC)) {
        Write-Log "[실패] 원본 폴더를 찾을 수 없습니다: $SRC"
        Write-Log "        Google Drive 가 마운트되지 않았거나 로그인이 풀렸을 수 있습니다."
        exit 1
    }
    if (-not (Test-Path $DST)) { Write-Log "[실패] 저장소 폴더 없음: $DST"; exit 1 }
    if (-not (Test-Path $GIT)) { Write-Log "[실패] git 실행파일 없음: $GIT"; exit 1 }

    # ── 1. 최상단 파일 동기화 ───────────────────────────────────
    #  README.md 는 저장소 전용 부록(A-1~A-5)이 붙어 있으므로 덮어쓰지 않는다.
    foreach ($f in @("insight_master.csv", "requirements.txt",
                     "install_requirements.bat", "uninstall_task_scheduler.bat")) {
        $s = Join-Path $SRC $f
        if (Test-Path $s) { Copy-Item $s (Join-Path $DST $f) -Force }
    }

    # ── 2. 실행 스크립트 동기화 ─────────────────────────────────
    foreach ($f in @("News_analytics.py", "install_task_scheduler.bat", "run_test.bat")) {
        $s = Join-Path $SRC "실행파일\$f"
        if (Test-Path $s) { Copy-Item $s (Join-Path $DST "실행파일\$f") -Force }
    }

    # ── 3. 언론사 oid 캐시 ──────────────────────────────────────
    $cache = Join-Path $SRC "_cache\press_oid_map.json"
    if (Test-Path $cache) { Copy-Item $cache (Join-Path $DST "_cache\press_oid_map.json") -Force }

    # ── 4. 연도 폴더의 CSV/TXT 만 폴더구조 유지하며 복사 ────────
    #  PNG 는 용량이 커서(하루 약 30MB) 제외한다. .gitignore 에서도 막고 있다.
    $copied = 0
    Get-ChildItem -Path $SRC -Directory | Where-Object { $_.Name -match '^\d{4}$' } | ForEach-Object {
        Get-ChildItem -Path $_.FullName -Recurse -File |
          Where-Object { $_.Extension -eq ".csv" -or $_.Extension -eq ".txt" } |
          ForEach-Object {
              $rel = $_.FullName.Substring($SRC.Length + 1)
              $target = Join-Path $DST $rel
              $dir = Split-Path $target -Parent
              if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
              Copy-Item $_.FullName $target -Force
              $copied++
          }
    }
    Write-Log "데이터 파일 $copied 개 동기화 완료"

    # ── 4-1. 일간종합 그래프 4종 업로드 (막대그래프 PNG + 워드클라우드 JPG) ──
    #  - 막대그래프 2종: 단색 면이 넓어 PNG 가 더 작으므로 원본 PNG 그대로 복사
    #  - 워드클라우드 2종: JPG(품질 75)로 변환 (PNG 대비 약 60% 절감)
    #  하루 약 0.45MB → 저장소가 1GB 에 닿는 시점을 약 5년 뒤로 늦춘다.
    #  보관 기간: 최근 395일(13개월). 그보다 오래된 날짜의 그래프는 저장소에서 지운다.
    #  G 드라이브 원본 PNG 는 건드리지 않고, csv 는 이 규칙과 무관하게 계속 쌓는다.
    #  5년쯤 뒤 저장소 히스토리 정리는 수동으로 한다.
    $IMG_FROM  = "20261115"                                   # 그래프 업로드 시작일
    $KEEP_DAYS = 395                                          # 저장소 보관 기간(일)
    $JPG_Q     = 75                                           # 워드클라우드 JPG 품질
    $cutoff    = (Get-Date).AddDays(-$KEEP_DAYS).ToString("yyyyMMdd")
    $minDay    = if ($IMG_FROM -gt $cutoff) { $IMG_FROM } else { $cutoff }

    Add-Type -AssemblyName System.Drawing
    $jpgCodec  = [System.Drawing.Imaging.ImageCodecInfo]::GetImageEncoders() | Where-Object { $_.MimeType -eq "image/jpeg" }
    $encParams = New-Object System.Drawing.Imaging.EncoderParameters(1)
    $encParams.Param[0] = New-Object System.Drawing.Imaging.EncoderParameter([System.Drawing.Imaging.Encoder]::Quality, [long]$JPG_Q)
    function Save-AsJpg([string]$srcPath, [string]$dstPath) {
        $img = [System.Drawing.Image]::FromFile($srcPath)
        try {
            $bmp = New-Object System.Drawing.Bitmap $img.Width, $img.Height
            $g = [System.Drawing.Graphics]::FromImage($bmp)
            $g.Clear([System.Drawing.Color]::White)                # 투명 배경이 검게 변하지 않도록 흰 바탕
            $g.DrawImage($img, 0, 0, $img.Width, $img.Height)
            $g.Dispose()
            $bmp.Save($dstPath, $jpgCodec, $encParams)
            $bmp.Dispose()
        } finally { $img.Dispose() }
    }
    function Get-ImgTargetName([string]$name) {               # 업로드할 파일 이름(확장자 결정)
        if ($name -like "*wordcloud*") { return ($name -replace '\.png$', '.jpg') }
        return $name
    }

    # JPG 품질을 바꾸면 보관 기간 안의 워드클라우드를 모두 다시 변환한다
    $imgDir = Join-Path $DST "images"
    if (-not (Test-Path $imgDir)) { New-Item -ItemType Directory -Force -Path $imgDir | Out-Null }
    $qFile = Join-Path $imgDir "jpg_quality.txt"
    $forceJpg = -not ((Test-Path $qFile) -and ((Get-Content $qFile -Raw).Trim() -eq "$JPG_Q"))

    # (1) 보관 기간 안의 그래프 복사/변환 (이미 최신이면 건너뜀)
    $pngs = Get-ChildItem -Path $SRC -Directory | Where-Object { $_.Name -match '^\d{4}$' } | ForEach-Object {
        Get-ChildItem -Path $_.FullName -Recurse -File -Filter "일간종합_*.png" |
          Where-Object { $_.Name -match '_(\d{8})\.png$' -and $Matches[1] -ge $minDay }
    }
    $imgCount = 0
    foreach ($p in $pngs) {
        $relDir = Split-Path ($p.FullName.Substring($SRC.Length + 1)) -Parent
        $target = Join-Path (Join-Path $DST $relDir) (Get-ImgTargetName $p.Name)
        $isJpg  = $target -like "*.jpg"
        $fresh  = (Test-Path $target) -and ((Get-Item $target).LastWriteTime -ge $p.LastWriteTime)
        if ($fresh -and -not ($isJpg -and $forceJpg)) { continue }
        $dir = Split-Path $target -Parent
        if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Force -Path $dir | Out-Null }
        if ($isJpg) { Save-AsJpg $p.FullName $target } else { Copy-Item $p.FullName $target -Force }
        $imgCount++
    }
    Set-Content -Path $qFile -Value "$JPG_Q" -Encoding ASCII

    # (2) 저장소 정리: 형식이 바뀐 파일(막대그래프 JPG, 워드클라우드 PNG)과 보관 기간이 지난 그래프 삭제
    $removed = 0
    Get-ChildItem -Path $DST -Directory | Where-Object { $_.Name -match '^\d{4}$' } | ForEach-Object {
        Get-ChildItem -Path $_.FullName -Recurse -File -Filter "일간종합_*" | Where-Object {
            ($_.Extension -eq ".png" -or $_.Extension -eq ".jpg") -and (
                ($_.Extension -eq ".jpg" -and $_.Name -notlike "*wordcloud*") -or
                ($_.Extension -eq ".png" -and $_.Name -like "*wordcloud*") -or
                ($_.Name -match '_(\d{8})\.(png|jpg)$' -and $Matches[1] -lt $cutoff))
        } | ForEach-Object { Remove-Item $_.FullName -Force; $removed++ }
    }

    # (3) 가장 최근 날짜의 4종을 images\latest 에 고정 이름으로 복사 (README 첫 화면용)
    $latestDir = Join-Path $imgDir "latest"
    if (-not (Test-Path $latestDir)) { New-Item -ItemType Directory -Force -Path $latestDir | Out-Null }
    Get-ChildItem -Path $latestDir -File | Where-Object {
        ($_.Extension -eq ".jpg" -and $_.Name -notlike "*wordcloud*") -or
        ($_.Extension -eq ".png" -and $_.Name -like "*wordcloud*")
    } | ForEach-Object { Remove-Item $_.FullName -Force; $removed++ }
    if ($pngs) {
        $latestDay = ($pngs | ForEach-Object { if ($_.Name -match '_(\d{8})\.png$') { $Matches[1] } } |
                      Sort-Object -Descending | Select-Object -First 1)
        $d = $latestDay
        $dayDir = Join-Path $DST ("{0}\{1}\{2}" -f $d.Substring(0,4), $d.Substring(4,2), $d.Substring(6,2))
        foreach ($kind in @("빈도수_barplot_TOP20", "빈도수_wordcloud", "감성분석_barplot", "감성분석_wordcloud")) {
            $name = Get-ImgTargetName "일간종합_${kind}_$d.png"
            $src  = Join-Path $dayDir $name
            if (Test-Path $src) { Copy-Item $src (Join-Path $latestDir ($kind + [IO.Path]::GetExtension($name))) -Force }
        }
        Set-Content -Path (Join-Path $latestDir "date.txt") -Value $latestDay -Encoding UTF8
        Write-Log "그래프 $imgCount 개 갱신, 정리 $removed 개 (최신 $latestDay, 보관 $cutoff 이후, JPG 품질 $JPG_Q)"
    }

    # ── 5. 변경사항 확인 ────────────────────────────────────────
    $status = & $GIT -C $DST status --porcelain
    if (-not $status) {
        Write-Log "[완료] 변경사항이 없어 커밋을 건너뜁니다."
        exit 0
    }
    $changed = ($status | Measure-Object).Count
    Write-Log "변경된 파일 $changed 개 발견"

    # ── 6. 커밋 ────────────────────────────────────────────────
    & $GIT -C $DST add -A
    if ($LASTEXITCODE -ne 0) { Write-Log "[실패] git add 오류 (exit $LASTEXITCODE)"; exit 1 }

    $today = Get-Date -Format "yyyy-MM-dd"
    $msg = "데이터 자동 업데이트 $today ($changed 개 파일)"
    & $GIT -C $DST commit -q -m $msg
    if ($LASTEXITCODE -ne 0) { Write-Log "[실패] git commit 오류 (exit $LASTEXITCODE)"; exit 1 }

    # ── 6-1. GitHub 쪽 변경을 먼저 받아 합치기 ─────────────────
    #  GitHub 웹이나 다른 PC에서 파일을 추가하면 push 가 "rejected"로
    #  막힌다(2026-09-28 사례). push 전에 원격 변경을 병합해 이를 막는다.
    $prevEAP = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $pull = (& $GIT -C $DST pull --no-rebase --no-edit origin main 2>&1 | Out-String).Trim()
    $pullExit = $LASTEXITCODE
    if ($pullExit -ne 0) { & $GIT -C $DST merge --abort 2>&1 | Out-Null }
    $ErrorActionPreference = $prevEAP
    if ($pullExit -ne 0) {
        Write-Log "[실패] GitHub 변경사항 병합 오류 (exit $pullExit): $pull"
        Write-Log "        같은 파일을 양쪽에서 고쳐 충돌했을 수 있습니다. 수동 병합이 필요합니다."
        exit 1
    }

    # ── 7. 업로드 ──────────────────────────────────────────────
    #  git push 는 정상 동작 중에도 진행상황을 stderr 로 출력한다.
    #  ErrorActionPreference=Stop 상태에서 2>&1 로 받으면 PowerShell 이 이를
    #  오류로 오인해 예외를 던지므로, 이 구간만 Continue 로 낮춘다.
    $prevEAP = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    $push = (& $GIT -C $DST push origin main 2>&1 | Out-String).Trim()
    $pushExit = $LASTEXITCODE
    $ErrorActionPreference = $prevEAP

    if ($pushExit -ne 0) {
        Write-Log "[실패] git push 오류 (exit $pushExit): $push"
        if ($push -match "Authentication failed|Invalid username|could not read Username") {
            Write-Log "        GitHub 로그인이 만료됐습니다. github_재연결.bat 을 더블클릭해 다시 로그인하세요."
        } else {
            Write-Log "        원격 저장소와 맞지 않습니다. github_재연결.bat 을 실행하거나 수동 확인이 필요합니다."
        }
        exit 1
    }

    $sha = (& $GIT -C $DST rev-parse --short HEAD).Trim()
    Write-Log "[성공] 커밋 $sha 업로드 완료 — $msg"
    Write-Log "        https://github.com/cjs700/naver-news-analytics"
    exit 0
}
catch {
    Write-Log "[실패] 예외 발생: $($_.Exception.Message)"
    exit 1
}
