import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from tkinterdnd2 import DND_FILES
import pandas as pd

from ui.popups.base_popup import BasePopup
from src.styles import COLORS, FONTS

class AccountingPopup(BasePopup):
    def __init__(self, parent, data_manager, refresh_callback, mgmt_no):
        # Handle list argument for mgmt_no
        if isinstance(mgmt_no, list):
            self.mgmt_nos = mgmt_no
            self.target_mgmt_no = mgmt_no[0]
        else:
            self.mgmt_nos = [mgmt_no]
            self.target_mgmt_no = mgmt_no

        # Input variables (Initialize before super().__init__ calls _create_widgets)
        # self.var_tax_date = tk.StringVar()
        # self.var_tax_no = tk.StringVar()
        # self.var_export_no = tk.StringVar()
        # self.var_export_file = tk.StringVar()
        
        super().__init__(parent, data_manager, refresh_callback, popup_title="회계 처리", mgmt_no=self.target_mgmt_no)
        self.geometry("1200x800")

    def _setup_info_panel(self, parent):
        """Left Panel Implementation"""
        # --- Basic Info Section ---
        ctk.CTkLabel(parent, text="기본 정보", font=FONTS["header"]).pack(anchor="w", pady=(10, 10), padx=10)
        
        info_frame = ctk.CTkFrame(parent, fg_color=COLORS["bg_dark"])
        info_frame.pack(fill="x", pady=(0, 20), padx=10)
        
        self.lbl_client = self._add_info_row(info_frame, "업체명")
        self.lbl_project = self._add_info_row(info_frame, "프로젝트명")
        self.lbl_type = self._add_info_row(info_frame, "구분")
        self.lbl_currency = self._add_info_row(info_frame, "통화")
        
        # Financial Summary
        ctk.CTkLabel(parent, text="금액 요약", font=FONTS["header"]).pack(anchor="w", pady=(0, 10), padx=10)
        fin_frame = ctk.CTkFrame(parent, fg_color=COLORS["bg_dark"])
        fin_frame.pack(fill="x", pady=(0, 20), padx=10)
        
        self.lbl_total_amount = self._add_info_row(fin_frame, "주문금액")
        self.lbl_paid_amount = self._add_info_row(fin_frame, "입금금액")
        self.lbl_unpaid_amount = self._add_info_row(fin_frame, "미수금액", text_color=COLORS["danger"])

        # Notes (Read Only for reference)
        ctk.CTkLabel(parent, text="비고 / 요청사항", font=FONTS["header"]).pack(anchor="w", pady=(0, 10), padx=10)
        self.txt_note = ctk.CTkTextbox(parent, height=80, fg_color=COLORS["bg_dark"], text_color=COLORS["text"])
        self.txt_note.pack(fill="x", pady=(0, 5), padx=10)
        self.txt_req_note = ctk.CTkTextbox(parent, height=60, fg_color=COLORS["bg_dark"], text_color=COLORS["text"])
        self.txt_req_note.pack(fill="x", padx=10)

    def _setup_items_panel(self, parent):
        """Right Panel Implementation"""
        self.tab_view = ctk.CTkTabview(parent)
        self.tab_view.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tab_items = self.tab_view.add("품목 상세")
        self.tab_delivery = self.tab_view.add("출고 이력")
        self.tab_payment = self.tab_view.add("입금 이력")
        
        self._setup_items_tab()
        self._setup_delivery_tab()
        self._setup_payment_tab()

    def _setup_items_tab(self):
        headers = ["품목명", "모델명", "수량", "단가", "공급가액", "세액", "합계금액"]
        widths = [120, 120, 60, 100, 100, 80, 100]
        self._create_table(self.tab_items, headers, widths, "items_scroll")

    def _setup_delivery_tab(self):
        headers = ["일시", "출고수량", "송장번호", "운송방법", "시리얼번호"]
        widths = [100, 80, 120, 100, 150]
        self._create_table(self.tab_delivery, headers, widths, "delivery_scroll")

    def _setup_payment_tab(self):
        headers = ["일시", "입금액", "통화", "증빙"]
        widths = [100, 120, 80, 200]
        self._create_table(self.tab_payment, headers, widths, "payment_scroll")

    def _create_table(self, parent, headers, widths, scroll_attr_name):
        # Header
        header_frame = ctk.CTkFrame(parent, height=30, fg_color=COLORS["bg_dark"])
        header_frame.pack(fill="x", pady=(0, 5))
        for h, w in zip(headers, widths):
            ctk.CTkLabel(header_frame, text=h, width=w, font=FONTS["main_bold"]).pack(side="left", padx=2)
            
        # Scrollable Content
        scroll_frame = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True)
        setattr(self, scroll_attr_name, scroll_frame)

    def _add_info_row(self, parent, label, text_color=COLORS["text"]):
        row = ctk.CTkFrame(parent, fg_color="transparent", height=25)
        row.pack(fill="x", padx=5, pady=2)
        ctk.CTkLabel(row, text=label, width=80, anchor="w", font=FONTS["main"], text_color=COLORS["text_dim"]).pack(side="left")
        value_lbl = ctk.CTkLabel(row, text="-", font=FONTS["main"], text_color=text_color)
        value_lbl.pack(side="left", padx=5)
        return value_lbl

    def _on_drop_file(self, event):
        file_path = event.data
        if file_path.startswith('{') and file_path.endswith('}'):
            file_path = file_path[1:-1]
        self.var_export_file.set(file_path)

    def _open_file_dialog(self):
        from tkinter import filedialog
        file_path = filedialog.askopenfilename()
        if file_path:
            self.var_export_file.set(file_path)

    def _load_data(self):
        # Load Main Data
        df = self.dm.df_data
        row = df[df["관리번호"] == self.target_mgmt_no].iloc[0]
        
        # Basic Info
        self.lbl_client.configure(text=row.get("업체명", ""))
        self.lbl_project.configure(text=row.get("프로젝트명", ""))
        self.lbl_type.configure(text=row.get("구분", ""))
        self.lbl_currency.configure(text=row.get("통화", ""))
        
        # Financials
        rows = df[df["관리번호"] == self.target_mgmt_no]
        total = rows["합계금액"].sum()
        paid = rows["기수금액"].sum()
        unpaid = total - paid
        
        self.lbl_total_amount.configure(text=f"{total:,.0f}")
        self.lbl_paid_amount.configure(text=f"{paid:,.0f}")
        self.lbl_unpaid_amount.configure(text=f"{unpaid:,.0f}")
        
        # Existing Inputs
        # if pd.notna(row.get("세금계산서발행일")): self.var_tax_date.set(row.get("세금계산서발행일"))
        # self.var_tax_no.set(row.get("세금계산서번호", "") if pd.notna(row.get("세금계산서번호")) else "")
        # self.var_export_no.set(row.get("수출신고번호", "") if pd.notna(row.get("수출신고번호")) else "")
        # self.var_export_file.set(row.get("수출신고필증경로", "") if pd.notna(row.get("수출신고필증경로")) else "")
        
        # Notes
        self.txt_note.insert("1.0", str(row.get("비고", "")).replace("nan", ""))
        self.txt_note.configure(state="disabled")
        self.txt_req_note.insert("1.0", str(row.get("주문요청사항", "")).replace("nan", ""))
        self.txt_req_note.configure(state="disabled")

        # Load Tabs
        self._load_items_tab(rows)
        self._load_delivery_tab()
        self._load_payment_tab()

    def _load_items_tab(self, rows):
        for _, row in rows.iterrows():
            self._add_row_to_table(self.items_scroll, [
                row.get("품목명", ""), row.get("모델명", ""), 
                f"{row.get('수량', 0):,.0f}", f"{row.get('단가', 0):,.0f}", 
                f"{row.get('공급가액', 0):,.0f}", f"{row.get('세액', 0):,.0f}", 
                f"{row.get('합계금액', 0):,.0f}"
            ], [120, 120, 60, 100, 100, 80, 100])

    def _load_delivery_tab(self):
        # Filter Delivery Sheet by mgmt_no
        if hasattr(self.dm, 'df_delivery'):
            df_d = self.dm.df_delivery
            if "관리번호" in df_d.columns:
                d_rows = df_d[df_d["관리번호"] == self.target_mgmt_no]
                for _, row in d_rows.iterrows():
                    self._add_row_to_table(self.delivery_scroll, [
                        row.get("일시", ""), f"{row.get('출고수량', 0):,.0f}", 
                        row.get("송장번호", ""), row.get("운송방법", ""), 
                        row.get("시리얼번호", "")
                    ], [100, 80, 120, 100, 150])

    def _load_payment_tab(self):
        # Filter Payment Sheet
        if hasattr(self.dm, 'df_payment'):
            df_p = self.dm.df_payment
            if "관리번호" in df_p.columns:
                p_rows = df_p[df_p["관리번호"] == self.target_mgmt_no]
                for _, row in p_rows.iterrows():
                    self._add_row_to_table(self.payment_scroll, [
                        row.get("일시", ""), f"{row.get('입금액', 0):,.0f}", 
                        row.get("통화", ""), row.get("외화입금증빙경로", "")
                    ], [100, 120, 80, 200])

    def _add_row_to_table(self, parent, values, widths):
        row_frame = ctk.CTkFrame(parent, fg_color="transparent", height=30)
        row_frame.pack(fill="x", pady=1)
        for v, w in zip(values, widths):
            ctk.CTkLabel(row_frame, text=str(v).replace("nan", ""), width=w, anchor="w").pack(side="left", padx=2)

    def save(self):
        # Update Data Sheet
        df = self.dm.df_data
        mask = df["관리번호"] == self.target_mgmt_no
        
        if mask.any():
            # df.loc[mask, "세금계산서발행일"] = self.var_tax_date.get()
            # df.loc[mask, "세금계산서번호"] = self.var_tax_no.get()
            # df.loc[mask, "수출신고번호"] = self.var_export_no.get()
            # df.loc[mask, "수출신고필증경로"] = self.var_export_file.get()
            
            self.dm.save_data()
            messagebox.showinfo("성공", "저장되었습니다.", parent=self)
            if self.refresh_callback:
                self.refresh_callback()
            self.destroy()
        else:
            messagebox.showerror("오류", "데이터를 찾을 수 없습니다.", parent=self)

    def _create_footer(self, parent):
        footer_frame = ctk.CTkFrame(parent, fg_color="transparent")
        footer_frame.pack(fill="x", pady=(10, 0), side="bottom")
        
        ctk.CTkButton(footer_frame, text="닫기", command=self.destroy, width=100, 
                      fg_color=COLORS["bg_light"], hover_color=COLORS["bg_light_hover"], 
                      text_color=COLORS["text"]).pack(side="left")
        
        ctk.CTkButton(footer_frame, text="회계처리", command=self.on_accounting_btn, width=120, 
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"]).pack(side="right")

    def on_accounting_btn(self):
        from ui.popups.mini_accounting_popup import MiniAccountingPopup
        def after_close():
            # Update order status to '종료'
            try:
                self.dm.update_order_status(self.target_mgmt_no, "종료")
            except Exception as e:
                messagebox.showerror("오류", f"상태 업데이트 실패: {e}", parent=self)
                return
            # Notify user of completion
            messagebox.showinfo("완료", "회계처리가 완료되었습니다.", parent=self)
            # Refresh main view and close this popup
            if self.refresh_callback:
                self.refresh_callback()
            self.destroy()
        MiniAccountingPopup(self, self.dm, after_close, self.target_mgmt_no)

    def _on_popup_closed(self):
        if self.refresh_callback:
            self.refresh_callback()
        self._load_data()

    # Required Abstract Methods
    def delete(self): pass
    def _generate_new_id(self): pass
    def _add_item_row(self, item_data=None): pass
    def _calculate_totals(self): pass
    def _on_client_select(self, client_name): pass
