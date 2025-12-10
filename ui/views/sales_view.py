import customtkinter as ctk
from tkinter import messagebox
from ui.views.table_view import TableView
from ui.components.context_menu import ContextMenu
from src.styles import COLORS, FONTS

class SalesView(ctk.CTkFrame):
    def __init__(self, parent, data_manager, popup_manager):
        super().__init__(parent, fg_color="transparent")
        self.dm = data_manager
        self.pm = popup_manager
        self.context_menu = ContextMenu(self)
                
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
            ("신규견적", self.on_quote),
            ("신규주문", self.on_order),
            ("일괄출고", self.on_delivery),
            ("일괄입금", self.on_payment)
        ]
        
        for text, cmd in buttons:
            ctk.CTkButton(btn_frame, text=text, command=cmd, width=80, height=28,
                          fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
                          font=FONTS["main_bold"]).pack(side="left", padx=5)
                          
        # Table View
        self.table_view = TableView(self, self.dm, self.pm)
        self.table_view.pack(fill="both", expand=True)
        
        self.table_view.tree.bind("<Button-3>", self.on_right_click)
        
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
            self.pm.open_production_popup(mgmt_nos)
            
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

    def on_right_click(self, event):
        # Identify the row under the mouse
        item = self.table_view.tree.identify_row(event.y)
        if not item: return
        
        # Select the row
        self.table_view.tree.selection_set(item)
        
        # Get item values
        values = self.table_view.tree.item(item, "values")
        mgmt_no = values[0]
        status = values[1]
        
        # Clear and populate context menu
        self.context_menu.clear()
        
        # Add Delete option
        self.context_menu.add_command("삭제", lambda: self.delete_item(mgmt_no, status), text_color=COLORS["danger"])
        
        # Show context menu
        self.context_menu.show(event.x_root, event.y_root)

    def delete_item(self, mgmt_no, status):
        if not messagebox.askyesno("삭제 확인", f"정말 {status} 건 ({mgmt_no})을 삭제하시겠습니까?"):
            return

        success = False
        msg = ""

        if status == "견적":
            success, msg = self.dm.delete_quote(mgmt_no)
        elif status == "주문":
            success, msg = self.dm.delete_order(mgmt_no)
        
        if success:
            messagebox.showinfo("삭제 완료", "삭제되었습니다.")
            self.refresh_data()
        else:
            messagebox.showerror("오류", f"삭제 실패: {msg}")
