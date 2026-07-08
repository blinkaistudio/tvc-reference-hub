@echo off
chcp 65001 >nul
cd /d "%~dp0"
rem 유튜브/비메오 임베드는 file:// 에서 재생이 막혀 로컬 서버로 띄웁니다 (갱신 버튼도 서버가 처리)
start "TVC허브 서버 (이 창을 닫으면 사이트가 꺼집니다)" /min python serve.py
