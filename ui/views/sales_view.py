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
            ("일괄출고/입금", self.on_production)
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
        
    def on_production(self):
        mgmt_nos = self.get_selected_mgmt_nos()
        if mgmt_nos:
            self.pm.open_production_popup(mgmt_nos)
            
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
        
        # Add Copy option
        self.context_menu.add_command("복사", lambda: self.copy_item(mgmt_no, status), text_color=COLORS["text"])
        
        # [신규] 견적 상태일 때 주문확정 메뉴 추가
        if status == "견적":
            self.context_menu.add_command("주문확정", lambda: self.confirm_order(mgmt_no), text_color=COLORS["primary"])

        # [신규] 주문 상태일 때 생산 시작 메뉴 추가
        if status == "주문":
            self.context_menu.add_command("생산 시작", lambda: self.start_production(mgmt_no), text_color=COLORS["primary"])
        
        # Add Delete option
        self.context_menu.add_command("삭제", lambda: self.delete_item(mgmt_no, status), text_color=COLORS["danger"])
        
        # Show context menu
        self.context_menu.show(event.x_root, event.y_root)

    def copy_item(self, mgmt_no, status):
        if status == "견적":
            self.pm.open_quote_popup(mgmt_no, copy_mode=True)
        elif status == "주문":
            self.pm.open_order_popup(mgmt_no, copy_mode=True)
        else:
            messagebox.showinfo("알림", "복사할 수 없는 항목입니다.")

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

    def confirm_order(self, mgmt_no):
        def on_confirm(po_no):
            success, msg = self.dm.confirm_order(mgmt_no, po_no)
            if success:
                messagebox.showinfo("성공", "주문이 확정되었습니다.")
                self.refresh_data()
            else:
                messagebox.showerror("오류", f"주문 확정 실패: {msg}")
                
        self.pm.open_mini_order_popup(mgmt_no, on_confirm)

    def start_production(self, mgmt_no):
        if not messagebox.askyesno("생산 시작", "주문 상태를 '생산중'으로 변경하고 생산 요청을 진행하시겠습니까?"):
            return

        # 1. 상태 업데이트
        success, msg = self.dm.update_order_status(mgmt_no, "생산중")
        if not success:
            messagebox.showerror("오류", f"상태 변경 실패: {msg}")
            return

        # 2. 변경된 데이터 가져오기
        df = self.dm.df_data
        target_rows = df[df["관리번호"] == mgmt_no].to_dict("records")
        
        if not target_rows:
            messagebox.showwarning("경고", "데이터를 찾을 수 없어 생산 요청 파일 생성을 건너뜁니다.")
            self.refresh_data()
            return

        # 3. 생산 요청 파일 내보내기
        export_success, export_msg = self.dm.export_to_production_request(target_rows)

        if export_success:
            messagebox.showinfo("성공", f"생산 요청이 완료되었습니다.\n{export_msg}")
        else:
            messagebox.showwarning("주의", f"상태는 변경되었으나 생산 요청 파일 업데이트에 실패했습니다.\n{export_msg}")
            
        self.refresh_data()
