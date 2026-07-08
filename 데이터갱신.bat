@echo off
chcp 65001 >nul
echo [1/2] 유튜브에서 최신 TVC 영상 데이터를 수집합니다...
python "%~dp0update_data.py"
echo.
echo [2/3] 카메라 무빙 레퍼런스를 수집합니다...
python "%~dp0update_moves.py"
echo.
echo [3/5] 5초 컷(초단편 트랜지션/무빙)을 수집합니다... (길이 검증 때문에 몇 분 걸려요)
python "%~dp0update_shorts.py"
echo.
echo [4/5] 프로덕션/디렉터 + 모션 스튜디오(Vimeo) 레퍼런스를 수집합니다...
python "%~dp0update_legends.py"
python "%~dp0update_vimeo.py"
python "%~dp0update_hip.py"
python "%~dp0update_feeds.py"
echo.
echo [5/5] 새 영상에 기본 태그를 부여합니다 (기존 태그는 유지)...
python "%~dp0tag_tools.py" fallback
echo.
echo [6/6] 웹 배포 (GitHub Pages)...
python "%~dp0publish.py"
echo.
echo 완료! 브라우저에서 페이지를 새로고침(F5)하세요.
echo (새 영상의 사람/장소/분위기 정밀 태깅은 Claude에게 "새 영상 태깅해줘"라고 요청하세요)
pause
