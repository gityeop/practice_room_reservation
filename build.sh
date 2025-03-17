#!/usr/bin/env bash
# Render 빌드 스크립트

set -o errexit

# 패키지 설치
pip install -r requirements.txt

# 정적 파일 설정 (파비콘 겸험)
mkdir -p /app/static/images/characters
cp -r static/images/characters/* /app/static/images/characters/ 2>/dev/null || true
cp static/favicon.ico /app/static/ 2>/dev/null || true

# 데이터베이스 마이그레이션 (필요한 경우)
flask db upgrade
