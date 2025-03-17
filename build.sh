#!/usr/bin/env bash
# Render 빌드 스크립트

set -o errexit

pip install -r requirements.txt

# 데이터베이스 마이그레이션 (필요한 경우)
flask db upgrade
