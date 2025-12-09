import os
import sys
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk

try:
    from tkinterdnd2 import TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False

# [변경] 폴더 구조 변경에 따른 Import 경로 수정
from src.config import Config
from managers.data_manager import DataManager
from managers.popup_manager import PopupManager
from src.styles import COLORS, FONT_FAMILY, FONTS

# [변경] UI Views Import 경로 수정 (ui.views 패키지)
from ui.views.calendar_view import CalendarView
from ui.views.client_view import ClientView
from ui.views.dashboard import DashboardView
from ui.views.gantt_view import GanttView
from ui.views.kanban_view import KanbanView
from ui.views.sales_view import SalesView
from ui.views.table_view import TableView
from ui.views.placeholder_view import PlaceholderView

# DnD 라이브러리 가용성 체크 및 래퍼 클래스 설정
if DND_AVAILABLE:
    class BaseApp(ctk.CTk, TkinterDnD.DnDWrapper):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.TkdndVersion = TkinterDnD._require(self)
else:
    class BaseApp(ctk.CTk):
        pass

class SalesManagerApp(BaseApp):
    def __init__(self):
        super().__init__()

        # 1. 매니저 초기화 (데이터, 팝업)
        self.dm = DataManager()
        self.pm = PopupManager(self, self.dm, self.refresh_ui)

        # 2. 윈도우 기본 설정
        self.title(f"Sales Manager - v{Config.APP_VERSION}")
        self.geometry("1650x900")
        
        ctk.set_appearance_mode(self.dm.current_theme)
        ctk.set_default_color_theme("dark-blue")
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 그리드 설정
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.current_view = None
        self.nav_buttons = {}

        # 3. UI 구성
        self.create_sidebar()
        self.create_content_area()
        
        # 4. 초기 데이터 로드
        success, msg = self.dm.load_data()
        if not success:
            print(f"초기 로드 경고: {msg}") # 콘솔 로그로 대체 (UX 위해 팝업 생략 가능)
            
        # 초기 화면: 대시보드
        self.show_dashboard()
        
        # 5. 자동 새로고침 시작 (동시성 제어 보조)
        self.start_auto_refresh_loop()

    def start_auto_refresh_loop(self):
        """
        주기적으로 외부 파일 변경 사항을 체크하여 UI를 갱신합니다.
        (2인 동시 사용 시 데이터 최신화 유지)
        """
        try:
            if self.dm.check_for_external_changes():
                success, _ = self.dm.load_data()
                if success:
                    self.refresh_ui()
                    # 필요하다면 하단 상태바 등에 "데이터 갱신됨" 표시 가능
        except Exception as e:
            print(f"Auto Refresh Error: {e}")
        
        # 5초마다 체크 (서버 부하 고려하여 조절 가능)
        self.after(5000, self.start_auto_refresh_loop)

    def create_sidebar(self):
        self.sidebar_frame = ctk.CTkFrame(self, width=240, corner_radius=0, fg_color=COLORS["bg_dark"])
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_propagate(False)

        self.logo_label = ctk.CTkLabel(
            self.sidebar_frame, 
            text="Sales Manager", 
            font=("Emoji", 26, "bold"), 
            text_color=COLORS["primary"]
        )
        self.logo_label.pack(pady=(20, 10), padx=20, anchor="w")
        self.logo_label.bind("<Button-1>", lambda e: self.show_dashboard())
        self.logo_label.bind("<Enter>", lambda e: self.logo_label.configure(cursor="hand2"))
        self.logo_label.bind("<Leave>", lambda e: self.logo_label.configure(cursor=""))

        # (Label Text, Command, Unique Key)
        menu_groups = [
            ("통합관리", [
                ("업체", self.show_client_view, "client"),
            ]),
            ("판매관리", [
                ("판매관리", self.show_sales_view, "sales_management"),
            ]),
            ("구매관리", [
                ("견적", self.show_purchase_quote_view, "purchase_quote"),
                ("주문", self.show_purchase_order_view, "purchase_order"),
                ("납품", self.show_purchase_delivery_view, "purchase_delivery"),
                ("송금", self.show_purchase_payment_view, "purchase_payment"),
                ("사후처리", self.show_purchase_after_service_view, "purchase_as"),
            ]),
            ("일정 관리", [
                ("테이블 뷰", self.show_table_view, "schedule_table"),
                ("캘린더 뷰", self.show_calendar_view, "schedule_calendar"),
                ("칸반 보드", self.show_kanban_view, "schedule_kanban"),
                ("간트 차트", self.show_gantt_view, "schedule_gantt"),
            ])
        ]

        for group_name, items in menu_groups:
            ctk.CTkLabel(self.sidebar_frame, text=group_name, font=FONTS["main_bold"], text_color=COLORS["text_dim"]).pack(anchor="w", padx=20, pady=(10, 2))
            
            for text, command, key in items:
                btn = ctk.CTkButton(
                    self.sidebar_frame, 
                    text=text, 
                    command=command,
                    height=32, 
                    anchor="w", 
                    fg_color="transparent", 
                    text_color=COLORS["text"], 
                    hover_color=COLORS["bg_medium"], 
                    font=FONTS["main"]
                )
                btn.pack(fill="x", padx=10, pady=1)
                self.nav_buttons[key] = btn

        ctk.CTkFrame(self.sidebar_frame, height=1, fg_color=COLORS["border"]).pack(fill="x", pady=10, padx=10, side="bottom")
        
        ctk.CTkButton(self.sidebar_frame, text="⚙️  설정", command=self.pm.open_settings, 
                      height=32, anchor="w", fg_color="transparent", text_color=COLORS["text_dim"], 
                      hover_color=COLORS["bg_medium"], font=FONTS["main"]).pack(fill="x", padx=10, pady=2, side="bottom")
        
        ctk.CTkButton(self.sidebar_frame, text="🔄  데이터 로드", command=self.reload_all_data, 
                      height=32, anchor="w", fg_color=COLORS["bg_medium"], text_color=COLORS["text"], 
                      hover_color=COLORS["bg_light"], font=FONTS["main"]).pack(fill="x", padx=10, pady=5, side="bottom")

    def create_content_area(self):
        self.content_frame = ctk.CTkFrame(self, corner_radius=0, fg_color="transparent")
        self.content_frame.grid(row=0, column=1, sticky="nsew")
        
        # 뷰 인스턴스 생성 (PopupManager 전달)
        self.view_dashboard = DashboardView(self.content_frame, self.dm, self.pm)
        self.view_client = ClientView(self.content_frame, self.dm, self.pm)
        self.view_sales = SalesView(self.content_frame, self.dm, self.pm)
        self.view_calendar = CalendarView(self.content_frame, self.dm, self.pm)
        self.view_kanban = KanbanView(self.content_frame, self.dm, self.pm)
        self.view_gantt = GanttView(self.content_frame, self.dm, self.pm)
        self.view_table = TableView(self.content_frame, self.dm, self.pm)
        
        # 구매관리 뷰 (Placeholder)
        self.view_purchase_quote = PlaceholderView(self.content_frame, "구매 견적")
        self.view_purchase_order = PlaceholderView(self.content_frame, "구매 주문")
        self.view_purchase_delivery = PlaceholderView(self.content_frame, "구매 납품")
        self.view_purchase_payment = PlaceholderView(self.content_frame, "구매 송금")
        self.view_purchase_as = PlaceholderView(self.content_frame, "구매 사후처리")

    def switch_view(self, view_name_key, view_instance):
        # 버튼 활성화 상태 변경
        for key, btn in self.nav_buttons.items():
            if key == view_name_key:
                btn.configure(fg_color=COLORS["bg_light"], text_color=COLORS["primary"])
            else:
                btn.configure(fg_color="transparent", text_color=COLORS["text"])
        
        # 기존 뷰 숨기기
        for child in self.content_frame.winfo_children():
            child.pack_forget()
        
        # 새 뷰 보이기
        view_instance.pack(fill="both", expand=True)
        self.current_view = view_instance
        
        # 데이터 갱신 (뷰에 refresh_data 메서드가 있다면)
        if hasattr(view_instance, "refresh_data"):
            view_instance.refresh_data()

    def show_dashboard(self): self.switch_view(None, self.view_dashboard)
    
    # 통합관리
    def show_client_view(self): self.switch_view("client", self.view_client)
    
    # 판매관리
    def show_sales_view(self): self.switch_view("sales_management", self.view_sales)

    # 구매관리
    def show_purchase_quote_view(self): self.switch_view("purchase_quote", self.view_purchase_quote)
    def show_purchase_order_view(self): self.switch_view("purchase_order", self.view_purchase_order)
    def show_purchase_delivery_view(self): self.switch_view("purchase_delivery", self.view_purchase_delivery)
    def show_purchase_payment_view(self): self.switch_view("purchase_payment", self.view_purchase_payment)
    def show_purchase_after_service_view(self): self.switch_view("purchase_as", self.view_purchase_as)

    # 일정 관리
    def show_table_view(self): self.switch_view("schedule_table", self.view_table)
    def show_calendar_view(self): self.switch_view("schedule_calendar", self.view_calendar)
    def show_kanban_view(self): self.switch_view("schedule_kanban", self.view_kanban)
    def show_gantt_view(self): self.switch_view("schedule_gantt", self.view_gantt)

    def reload_all_data(self):
        success, msg = self.dm.load_data()
        if success:
            messagebox.showinfo("완료", "데이터를 새로고침했습니다.")
            self.refresh_ui()
        else:
            messagebox.showerror("오류", msg)

    def refresh_ui(self):
        """현재 활성화된 뷰와 테마를 갱신합니다."""
        if self.dm.is_dev_mode:
            self.sidebar_frame.configure(fg_color="#4a1e1e") # 개발모드 시 붉은 톤 배경
            self.logo_label.configure(text="[DEV MODE]", text_color=COLORS["danger"])
        else:
            self.sidebar_frame.configure(fg_color=COLORS["bg_dark"])
            self.logo_label.configure(text="Sales Manager", text_color=COLORS["primary"])
            
        if self.current_view and hasattr(self.current_view, "refresh_data"):
            self.current_view.refresh_data()

    def on_closing(self):
        self.quit()
        self.destroy()

if __name__ == "__main__":
    app = SalesManagerApp()
    app.mainloop()