#!/usr/bin/env python3
"""
대학생 AI 어시스턴트 - 실행 진입점
매일 아침 자동으로 이메일 요약 + 일정 알림을 텔레그램으로 전송합니다.
"""

from agent import run_morning_briefing

if __name__ == "__main__":
    run_morning_briefing()
