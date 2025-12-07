import platform

import customtkinter as ctk

# ==========================================
# [Color System] (Light, Dark) Tuples
# ==========================================
# 다크 모드와 라이트 모드를 모두 지원하기 위해 (Light색상, Dark색상) 튜플로 정의합니다.
COLORS = {
    # 주요 브랜드 컬러 (파란색 계열)
    "primary": ("#1565C0", "#3B8ED0"), 
    "primary_hover": ("#0D47A1", "#36719F"),
    
    # 상태별 색상 (빨강, 초록, 주황)
    "danger": ("#C62828", "#E04F5F"),
    "danger_hover": ("#B71C1C", "#D32F2F"),
    "success": ("#2E7D32", "#2CC985"),
    "warning": ("#EF6C00", "#D35400"),
    
    # 텍스트 색상
    "text": ("#212121", "#FFFFFF"),
    "text_dim": ("#616161", "#AAAAAA"), # 흐린 텍스트
    
    # 배경 색상 (계층 구조)
    "bg_dark": ("#F5F5F5", "#2b2b2b"),    # 가장 어두운 배경 (사이드바 등)
    "bg_medium": ("#FFFFFF", "#333333"),  # 중간 배경 (카드, 리스트 등)
    "bg_light": ("#E0E0E0", "#555555"),   # 밝은 배경 (버튼, 입력창 등)
    "bg_light_hover": ("#BDBDBD", "#666666"),
    
    # 테두리 및 기타
    "border": ("#9E9E9E", "#444444"),
    "transparent": "transparent"
}

# ==========================================
# [Font System] OS별 표준 한글 폰트 설정
# ==========================================
def get_system_font():
    """OS에 따라 적절한 한글 폰트를 반환합니다."""
    system_os = platform.system()
    if system_os == "Windows":
        return "Malgun Gothic"  # 윈도우: 맑은 고딕
    elif system_os == "Darwin": 
        return "Apple SD Gothic Neo" # 맥: 애플 SD 산돌고딕
    else: 
        return "NanumGothic" # 리눅스 등

FONT_FAMILY = get_system_font()

# 공통 폰트 프리셋
FONTS = {
    "title": (FONT_FAMILY, 20, "bold"),      # 페이지 타이틀
    "header": (FONT_FAMILY, 16, "bold"),     # 섹션 헤더
    "main": (FONT_FAMILY, 12),               # 일반 본문
    "main_bold": (FONT_FAMILY, 12, "bold"),  # 강조 본문
    "small": (FONT_FAMILY, 10),              # 작은 텍스트
}

def get_color_str(key):
    """
    Matplotlib 등 튜플 색상을 지원하지 않는 라이브러리를 위해
    현재 테마에 맞는 단일 색상 문자열을 반환합니다.
    """
    color_val = COLORS.get(key)
    if not isinstance(color_val, tuple):
        return color_val
    
    mode = ctk.get_appearance_mode()
    if mode == "Light":
        return color_val[0]
    else:
        return color_val[1]