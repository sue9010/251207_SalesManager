import customtkinter as ctk
from tkinter import messagebox
from ui.views.table_view import TableView
from src.styles import COLORS, FONTS

class SalesView(ctk.CTkFrame):
    def __init__(self, parent, data_manager, popup_manager):
        super().__init__(parent, fg_color="transparent")
        self.dm = data_manager
        self.pm = popup_manager
                
        self._create_ui()

    def _create_ui(self):
        # Top Action Bar
        action_frame = ctk.CTkFrame(self, fg_color="transparent")
        action_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        # Title (Optional, can be removed if not needed)
        ctk.CTkLabel(action_frame, text="판매 관리", font=FONTS["header"]).pack(side="left")
        
        # Buttons Frame
        btn_frame = ctk.CTkFrame(action_frame, fg_color="transparent")
        btn_frame.pack(side="right")
        
        buttons = [
            ("견적", self.on_quote),
            ("주문", self.on_order),
            ("출고", self.on_delivery),
            ("입금", self.on_payment),
            ("종료", self.on_close),
        ]
        
        for text, cmd in buttons:
            ctk.CTkButton(btn_frame, text=text, command=cmd, width=80, height=35,
                          fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
                          font=FONTS["main_bold"]).pack(side="left", padx=5)
                          
        # Table View
        self.table_view = TableView(self, self.dm, self.pm)
        self.table_view.pack(fill="both", expand=True)
        
    def get_selected_mgmt_nos(self):
        selection = self.table_view.tree.selection()
        if not selection:
            messagebox.showwarning("경고", "항목을 선택해주세요.")
            return []
        
        mgmt_nos = []
        for item in selection:
            values = self.table_view.tree.item(item, "values")
            mgmt_nos.append(values[0]) # Assuming first column is mgmt_no
        return mgmt_nos

    def on_quote(self):
        self.pm.open_quote_popup()
        
    def on_order(self):
        self.pm.open_order_popup()
        
    def on_delivery(self):
        mgmt_nos = self.get_selected_mgmt_nos()
        if mgmt_nos:
            self.pm.open_delivery_popup(mgmt_nos)
            
    def on_payment(self):
        mgmt_nos = self.get_selected_mgmt_nos()
        if mgmt_nos:
            self.pm.open_payment_popup(mgmt_nos)
            
    def on_close(self):
        mgmt_nos = self.get_selected_mgmt_nos()
        if mgmt_nos:
            self.pm.open_after_sales_popup(mgmt_nos)
            
    def on_refresh(self):
        self.table_view.refresh_data()

    def refresh_data(self):
        self.on_refresh()
