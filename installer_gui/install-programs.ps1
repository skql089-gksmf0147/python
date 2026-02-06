# ============================================
# 🧩 윈도우 기본 프로그램 자동 설치 & 최신 업데이트 스크립트
# --------------------------------------------
# 포함 프로그램:
# - Bandizip
# - KakaoTalk
# - PotPlayer
# - Python 3.12
# - Visual Studio Code
# ============================================

# 관리자 권한 확인
$IsAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
if (-not $IsAdmin) {
    Write-Host "⚠️  관리자 권한으로 PowerShell을 다시 실행해주세요." -ForegroundColor Red
    pause
    exit
}

Write-Host "`n🔹 기본 프로그램 최신 버전 설치를 시작합니다..." -ForegroundColor Cyan
Write-Host "-------------------------------------------`n"

# 설치할 프로그램 목록
$apps = @(
    "Bandizip.Bandizip",
    "Kakao.KakaoTalk",
    "Daum.PotPlayer",
    "Python.Python.3.12",
    "Microsoft.VisualStudioCode"
)

# 각 프로그램 최신 버전 설치
foreach ($app in $apps) {
    Write-Host "`n>> $app 설치 중..." -ForegroundColor Yellow
    try {
        winget install --id $app -e --accept-source-agreements --accept-package-agreements -h
    } catch {
        Write-Host "❌ $app 설치 실패" -ForegroundColor Red
    }
}

Write-Host "`n✅ 기본 프로그램 설치 완료!" -ForegroundColor Green

# ------------------------------------------------
# 이미 설치된 프로그램 최신 업데이트 수행
# ------------------------------------------------
Write-Host "`n🔹 설치된 프로그램을 최신 버전으로 업데이트합니다..." -ForegroundColor Cyan
try {
    winget upgrade --all --accept-source-agreements --accept-package-agreements
} catch {
    Write-Host "⚠️ 업데이트 중 일부 오류가 발생했습니다." -ForegroundColor Yellow
}

Write-Host "`n🎉 모든 작업이 완료되었습니다!" -ForegroundColor Green
pause
