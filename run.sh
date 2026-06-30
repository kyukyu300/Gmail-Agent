#!/bin/bash
# 대학생 AI 에이전트 실행 쉘 스크립트

# 스크립트 디렉토리로 이동
cd /Users/gyujin/.gemini/antigravity/scratch/college-agent

# PATH 설정 (명령어 못찾는 현상 방지)
export PATH="/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin:/opt/homebrew/bin:$PATH"

# 에이전트 실행 및 로그 저장
/usr/bin/python3 main.py >> logs/agent.log 2>&1
