import customtkinter as ctk
from tkinter import messagebox
from ui.views.purchase_table_view import PurchaseTableView
from src.styles import COLORS, FONTS

class PurchaseView(ctk.CTkFrame):
    def __init__(self, parent, data_manager, popup_manager):
        super().__init__(parent, fg_color="transparent")
        self.dm = data_manager
        self.pm = popup_manager
                
        self._create_ui()

    def _create_ui(self):
        # 1. 상단 액션바 (타이틀 및 메인 버튼)
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        # 타이틀
        ctk.CTkLabel(action_frame, text="구매 관리", font=FONTS["header"]).pack(side="left")
        
        # 버튼 프레임
        btn_frame = ctk.CTkFrame(action_frame, fg_color="transparent")
        btn_frame.pack(side="right")
        
        # 메인 버튼들
        buttons = [
            ("신규발주", self.on_purchase),
            ("일괄입고", self.on_receiving),
            ("일괄지급", self.on_payment)
        ]
        
        for text, cmd in buttons:
            ctk.CTkButton(btn_frame, text=text, command=cmd, width=80, height=28,
                          fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
                          font=FONTS["main_bold"]).pack(side="left", padx=5)
                          
        # 2. 테이블 뷰 포함 (필터 및 리스트 영역)
        self.table_view = PurchaseTableView(self, self.dm, self.pm)
        self.table_view.pack(fill="both", expand=True)
        
    def get_selected_mgmt_nos(self):
        selection = self.table_view.tree.selection()
        if not selection:
            messagebox.showwarning("경고", "항목을 선택해주세요.")
            return []
        
        mgmt_nos = []
        for item in selection:
            values = self.table_view.tree.item(item, "values")
            mgmt_nos.append(values[0]) 
        return mgmt_nos

    # --- 핸들러 ---

    def on_purchase(self):
        self.pm.open_purchase_popup()
        
    def on_receiving(self):
        mgmt_nos = self.get_selected_mgmt_nos()
        if mgmt_nos:
            messagebox.showinfo("알림", f"선택된 {len(mgmt_nos)}건에 대한 입고 처리는 추후 구현됩니다.")
            
    def on_payment(self):
        mgmt_nos = self.get_selected_mgmt_nos()
        if mgmt_nos:
            messagebox.showinfo("알림", f"선택된 {len(mgmt_nos)}건에 대한 지급 처리는 추후 구현됩니다.")
            
    def on_refresh(self):
        self.table_view.refresh_data()

    def refresh_data(self):
        self.on_refresh()