@echo off
echo ======================================
echo  폐쇄망 반입용 pip 패키지 다운로드
echo  인터넷 되는 PC에서 실행하세요
echo ======================================

mkdir pip_packages

echo [1/2] PyTorch CPU 버전 다운로드...
pip download torch torchvision --index-url https://download.pytorch.org/whl/cpu -d pip_packages

echo [2/2] 나머지 패키지 다운로드...
pip download -r requirements.txt -d pip_packages

echo.
echo 완료!
echo pip_packages 폴더를 폐쇄망 서버로 복사 후:
echo   pip install --no-index --find-links=pip_packages -r requirements.txt
pause
