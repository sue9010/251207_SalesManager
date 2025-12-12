import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import pandas as pd
import os
import shutil
from datetime import datetime

from ui.popups.base_popup import BasePopup
from src.styles import COLORS, FONTS
from utils.file_dnd import FileDnDManager

class AccountingPopup(BasePopup):
    # 컬럼 설정 정의 (헤더명, 너비)
    COL_SPECS = {
        "items": [
            ("품목명", 120), ("모델명", 120), ("수량", 60), ("단가", 100), 
            ("공급가액", 100), ("세액", 80), ("합계금액", 100)
        ],
        "delivery": [
            ("일시", 100), ("모델명", 120), ("출고수량", 80), ("송장번호", 120), ("운송방법", 100), 
            ("수출신고번호", 150), ("수출신고필증", 200)
        ],
        "payment": [
            ("일시", 100), ("입금액", 120), ("통화", 60), ("증빙", 150), 
            ("세금계산서번호", 150), ("발행일", 120)
        ]
    }

    def __init__(self, parent, data_manager, refresh_callback, mgmt_no):
        # Handle list argument for mgmt_no
        if isinstance(mgmt_no, list):
            self.mgmt_nos = mgmt_no
            self.target_mgmt_no = mgmt_no[0]
        else:
            self.mgmt_nos = [mgmt_no]
            self.target_mgmt_no = mgmt_no

        self.dm = data_manager # Initialize dm early for FileDnDManager
        self.file_manager = FileDnDManager(self)
        self.entries = {} # {key: widget} for inline editing
        
        super().__init__(parent, data_manager, refresh_callback, popup_title="회계 처리", mgmt_no=self.target_mgmt_no)
        self.geometry("1400x900")

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

        # Related Documents
        ctk.CTkLabel(parent, text="관련 문서", font=FONTS["header"]).pack(anchor="w", pady=(10, 10), padx=10)
        self.files_scroll = ctk.CTkScrollableFrame(parent, fg_color=COLORS["bg_dark"], height=100)
        self.files_scroll.pack(fill="x", padx=10, pady=(0, 10))

    def _setup_items_panel(self, parent):
        """Right Panel Implementation"""
        self.tab_view = ctk.CTkTabview(parent)
        self.tab_view.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.tab_items = self.tab_view.add("품목 상세")
        self.tab_delivery = self.tab_view.add("출고 이력 (수출신고)")
        self.tab_payment = self.tab_view.add("입금 이력 (세금계산서)")
        
        self._setup_items_tab()
        self._setup_delivery_tab()
        self._setup_payment_tab()

    def _setup_items_tab(self):
        headers = [h for h, w in self.COL_SPECS["items"]]
        widths = [w for h, w in self.COL_SPECS["items"]]
        self._create_table(self.tab_items, headers, widths, "items_scroll")

    def _setup_delivery_tab(self):
        headers = [h for h, w in self.COL_SPECS["delivery"]]
        widths = [w for h, w in self.COL_SPECS["delivery"]]
        self._create_table(self.tab_delivery, headers, widths, "delivery_scroll")

    def _setup_payment_tab(self):
        headers = [h for h, w in self.COL_SPECS["payment"]]
        widths = [w for h, w in self.COL_SPECS["payment"]]
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
        
        # Notes
        self.txt_note.insert("1.0", str(row.get("비고", "")).replace("nan", ""))
        self.txt_note.configure(state="disabled")
        self.txt_req_note.insert("1.0", str(row.get("주문요청사항", "")).replace("nan", ""))
        self.txt_req_note.configure(state="disabled")

        # Load Files
        for widget in self.files_scroll.winfo_children(): widget.destroy()
        has_files = False
        
        # 1. Purchase Order (from Data sheet)
        if self._add_file_row("주문서(발주서)", row.get("발주서경로")): has_files = True
        
        # 2. Business Registration (from Client sheet)
        client_name = row.get("업체명", "")
        if client_name:
            client_row = self.dm.df_clients[self.dm.df_clients["업체명"] == client_name]
            if not client_row.empty:
                if self._add_file_row("사업자등록증", client_row.iloc[0].get("사업자등록증경로")): has_files = True
                
        if not has_files:
            ctk.CTkLabel(self.files_scroll, text="첨부 파일 없음", font=FONTS["small"], text_color=COLORS["text_dim"]).pack(pady=10)

        # Load Tabs
        self._load_items_tab(rows)
        self._load_delivery_tab()
        self._load_payment_tab()

    def _load_items_tab(self, rows):
        for widget in self.items_scroll.winfo_children(): widget.destroy()
        widths = [w for h, w in self.COL_SPECS["items"]]
        for _, row in rows.iterrows():
            self._add_row_to_table(self.items_scroll, [
                row.get("품목명", ""), row.get("모델명", ""), 
                f"{row.get('수량', 0):,.0f}", f"{row.get('단가', 0):,.0f}", 
                f"{row.get('공급가액', 0):,.0f}", f"{row.get('세액', 0):,.0f}", 
                f"{row.get('합계금액', 0):,.0f}"
            ], widths)

    def _load_delivery_tab(self):
        for widget in self.delivery_scroll.winfo_children(): widget.destroy()
        if hasattr(self.dm, 'df_delivery'):
            df_d = self.dm.df_delivery
            if "관리번호" in df_d.columns:
                d_rows = df_d[df_d["관리번호"] == self.target_mgmt_no]
                for idx, row in d_rows.iterrows():
                    self._add_delivery_row(idx, row)

    def _load_payment_tab(self):
        for widget in self.payment_scroll.winfo_children(): widget.destroy()
        if hasattr(self.dm, 'df_payment'):
            df_p = self.dm.df_payment
            if "관리번호" in df_p.columns:
                p_rows = df_p[df_p["관리번호"] == self.target_mgmt_no]
                for idx, row in p_rows.iterrows():
                    self._add_payment_row(idx, row)

    def _add_row_to_table(self, parent, values, widths):
        row_frame = ctk.CTkFrame(parent, fg_color="transparent", height=30)
        row_frame.pack(fill="x", pady=1)
        for v, w in zip(values, widths):
            ctk.CTkLabel(row_frame, text=str(v).replace("nan", ""), width=w, anchor="w").pack(side="left", padx=2)

    def _add_delivery_row(self, idx, row):
        row_frame = ctk.CTkFrame(self.delivery_scroll, fg_color="transparent", height=30)
        row_frame.pack(fill="x", pady=1)
        
        widths = [w for h, w in self.COL_SPECS["delivery"]]
        
        # Get Model Name from main data if available
        model_name = ""
        if hasattr(self.dm, 'df_data'):
            mgmt_no = row.get("관리번호")
            if mgmt_no:
                main_row = self.dm.df_data[self.dm.df_data["관리번호"] == mgmt_no]
                if not main_row.empty:
                    model_name = main_row.iloc[0].get("모델명", "")

        # Read-only fields
        ctk.CTkLabel(row_frame, text=str(row.get("일시", "")), width=widths[0], anchor="w").pack(side="left", padx=2)
        ctk.CTkLabel(row_frame, text=str(model_name), width=widths[1], anchor="w").pack(side="left", padx=2)
        ctk.CTkLabel(row_frame, text=f"{row.get('출고수량', 0):,.0f}", width=widths[2], anchor="w").pack(side="left", padx=2)
        
        invoice_no = str(row.get("송장번호", ""))
        ctk.CTkLabel(row_frame, text=invoice_no, width=widths[3], anchor="w").pack(side="left", padx=2)
        ctk.CTkLabel(row_frame, text=str(row.get("운송방법", "")), width=widths[4], anchor="w").pack(side="left", padx=2)
        
        # Editable: Export No
        entry_export_no = ctk.CTkEntry(row_frame, width=widths[5], height=24)
        entry_export_no.pack(side="left", padx=2)
        entry_export_no.insert(0, str(row.get("수출신고번호", "")).replace("nan", ""))
        
        # Bind FocusOut for synchronization
        if invoice_no:
            entry_export_no.bind("<FocusOut>", lambda e, inv=invoice_no, ent=entry_export_no: self._sync_export_info(inv, export_no=ent.get()))
            
        self.entries[f"delivery_export_no_{idx}"] = entry_export_no
        
        # Editable: Export File
        file_frame = ctk.CTkFrame(row_frame, width=widths[6], height=30, fg_color="transparent")
        file_frame.pack(side="left", padx=2)
        file_frame.pack_propagate(False)
        
        key = f"delivery_export_file_{idx}"
        entry_file = ctk.CTkEntry(file_frame, placeholder_text="파일", height=24)
        entry_file.pack(side="left", fill="x", expand=True)
        
        # Bind FocusOut/Return for synchronization (manual entry)
        if invoice_no:
             entry_file.bind("<FocusOut>", lambda e, inv=invoice_no, ent=entry_file: self._sync_export_info(inv, export_file_path=ent.get()))
             entry_file.bind("<Return>", lambda e, inv=invoice_no, ent=entry_file: self._sync_export_info(inv, export_file_path=ent.get()))

        btn_del = ctk.CTkButton(file_frame, text="X", width=24, height=24,
                                 command=lambda: self.file_manager.clear_entry(key),
                                 fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"])
        btn_del.pack(side="left", padx=1)
        
        self.file_manager.file_entries[key] = entry_file
        if self.file_manager.DND_AVAILABLE:
            # Wrap drop callback to include sync
            def on_drop(files):
                if files:
                    path = files[0]
                    entry_file.delete(0, "end")
                    entry_file.insert(0, path)
                    if invoice_no:
                        self._sync_export_info(invoice_no, export_file_path=path)
            
            self.file_manager._setup_dnd(entry_file, key, callback=on_drop)
            
        current_path = row.get("수출신고필증경로", "")
        if current_path and str(current_path) != "nan":
            self.file_manager.update_file_entry(key, str(current_path))

    def _sync_export_info(self, invoice_no, export_no=None, export_file_path=None):
        """Sync Export No and File Path for rows with the same Invoice No"""
        if not invoice_no or invoice_no == "nan": return

        # Iterate through all delivery rows to find matches
        if hasattr(self.dm, 'df_delivery'):
            df_d = self.dm.df_delivery
            # We need to find indices that match this invoice_no AND are in the current popup view
            # But simpler is to iterate through self.entries keys which we know are loaded
            
            target_indices = []
            # Find indices with same invoice_no in the dataframe
            # Note: We only care about rows related to this popup's mgmt_nos if we want to limit scope,
            # but usually invoice_no is unique enough or we want to sync across the board?
            # Requirement says "송장번호가 동일한 항목", implying within the current view or globally?
            # Usually within the current view (shipment history of this order/project).
            # Let's limit to the rows currently displayed (which are filtered by target_mgmt_no in _load_delivery_tab)
            
            # Wait, _load_delivery_tab filters by self.target_mgmt_no. 
            # If we have multiple mgmt_nos (e.g. grouped order), we should check all of them.
            # But currently _load_delivery_tab only loads for self.target_mgmt_no.
            # So we only sync within the currently visible rows.
            
            d_rows = df_d[df_d["관리번호"] == self.target_mgmt_no]
            for idx, row in d_rows.iterrows():
                if str(row.get("송장번호")) == invoice_no:
                    target_indices.append(idx)
            
            for idx in target_indices:
                # Update Export No
                if export_no is not None:
                    entry_key = f"delivery_export_no_{idx}"
                    if entry_key in self.entries:
                        current_val = self.entries[entry_key].get()
                        if current_val != export_no:
                            self.entries[entry_key].delete(0, "end")
                            self.entries[entry_key].insert(0, export_no)
                
                # Update File Path
                if export_file_path is not None:
                    file_key = f"delivery_export_file_{idx}"
                    if file_key in self.file_manager.file_entries:
                        current_val = self.file_manager.file_entries[file_key].get()
                        if current_val != export_file_path:
                            self.file_manager.update_file_entry(file_key, export_file_path)

    def _add_payment_row(self, idx, row):
        row_frame = ctk.CTkFrame(self.payment_scroll, fg_color="transparent", height=30)
        row_frame.pack(fill="x", pady=1)
        
        widths = [w for h, w in self.COL_SPECS["payment"]]
        
        # Read-only fields
        ctk.CTkLabel(row_frame, text=str(row.get("일시", "")), width=widths[0], anchor="w").pack(side="left", padx=2)
        ctk.CTkLabel(row_frame, text=f"{row.get('입금액', 0):,.0f}", width=widths[1], anchor="w").pack(side="left", padx=2)
        ctk.CTkLabel(row_frame, text=str(row.get("통화", "")), width=widths[2], anchor="w").pack(side="left", padx=2)
        
        # Proof File (Read-only view)
        proof_frame = ctk.CTkFrame(row_frame, width=widths[3], height=30, fg_color="transparent")
        proof_frame.pack(side="left", padx=2)
        proof_frame.pack_propagate(False)

        proof_path = str(row.get("외화입금증빙경로", ""))
        if proof_path and proof_path != "nan":
             ctk.CTkButton(proof_frame, text="증빙", width=50, height=24, 
                           command=lambda p=proof_path: self.open_file(p)).pack(side="left", padx=2)
        else:
             ctk.CTkLabel(proof_frame, text="-", width=50).pack(side="left", padx=2)
             
        # Editable: Tax Invoice No
        entry_tax_no = ctk.CTkEntry(row_frame, width=widths[4], height=24)
        entry_tax_no.pack(side="left", padx=2)
        entry_tax_no.insert(0, str(row.get("세금계산서번호", "")).replace("nan", ""))
        self.entries[f"payment_tax_no_{idx}"] = entry_tax_no
        
        # Editable: Tax Invoice Date
        entry_tax_date = ctk.CTkEntry(row_frame, width=widths[5], height=24, placeholder_text="YYYY-MM-DD")
        entry_tax_date.pack(side="left", padx=2)
        entry_tax_date.insert(0, str(row.get("세금계산서발행일", "")).replace("nan", ""))
        self.entries[f"payment_tax_date_{idx}"] = entry_tax_date

    def save_data(self, silent=False):
        """Save changes to Delivery and Payment sheets"""
        
        # 1. Update Delivery Data
        if hasattr(self.dm, 'df_delivery'):
            for key, widget in self.entries.items():
                if key.startswith("delivery_export_no_"):
                    idx = int(key.split("_")[-1])
                    if idx in self.dm.df_delivery.index:
                        self.dm.df_delivery.at[idx, "수출신고번호"] = widget.get()
            
            # Save Files
            for key, widget in self.file_manager.file_entries.items():
                if key.startswith("delivery_export_file_"):
                    idx = int(key.split("_")[-1])
                    path = widget.get()
                    if path and idx in self.dm.df_delivery.index:
                        # If path is not already in attachment root, save it
                        if not path.startswith(self.dm.attachment_root):
                            d_no = self.dm.df_delivery.at[idx, "출고번호"]
                            client = self.lbl_client.cget("text")
                            safe_client = "".join([c for c in client if c.isalnum() or c in (' ', '_')]).strip()
                            info_text = f"{safe_client}_{d_no}_Export"
                            success, msg, new_path = self.file_manager.save_file(key, "수출", "Export", info_text)
                            if success:
                                self.dm.df_delivery.at[idx, "수출신고필증경로"] = new_path
                        else:
                             self.dm.df_delivery.at[idx, "수출신고필증경로"] = path

        # 2. Update Payment Data
        if hasattr(self.dm, 'df_payment'):
             for key, widget in self.entries.items():
                if key.startswith("payment_tax_no_"):
                    idx = int(key.split("_")[-1])
                    if idx in self.dm.df_payment.index:
                        self.dm.df_payment.at[idx, "세금계산서번호"] = widget.get()
                elif key.startswith("payment_tax_date_"):
                    idx = int(key.split("_")[-1])
                    if idx in self.dm.df_payment.index:
                        self.dm.df_payment.at[idx, "세금계산서발행일"] = widget.get()

        # Save to Excel
        success, msg = self.dm.save_data()
        if success:
            if not silent:
                messagebox.showinfo("성공", "저장되었습니다.", parent=self)
            self._load_data() # Reload to reflect changes
            return True
        else:
            messagebox.showerror("실패", f"저장 실패: {msg}", parent=self)
            return False

    def close_order(self):
        """Set order status to '종료'"""
        if messagebox.askyesno("종결", "정말 이 주문을 종결 처리하시겠습니까?\n종결 후에는 수정이 제한될 수 있습니다.", parent=self):
            # Auto-save before closing
            if not self.save_data(silent=True):
                return

            try:
                self.dm.update_order_status(self.target_mgmt_no, "종료")
                messagebox.showinfo("완료", "주문이 종결되었습니다.", parent=self)
                if self.refresh_callback:
                    self.refresh_callback()
                self.destroy()
            except Exception as e:
                messagebox.showerror("오류", f"상태 업데이트 실패: {e}", parent=self)

    def _create_footer(self, parent):
        footer_frame = ctk.CTkFrame(parent, fg_color="transparent")
        footer_frame.pack(fill="x", pady=(10, 0), side="bottom")
        
        ctk.CTkButton(footer_frame, text="닫기", command=self.destroy, width=100, 
                      fg_color=COLORS["bg_light"], hover_color=COLORS["bg_light_hover"], 
                      text_color=COLORS["text"]).pack(side="left")
        
        # Right side buttons
        btn_frame = ctk.CTkFrame(footer_frame, fg_color="transparent")
        btn_frame.pack(side="right")
        
        ctk.CTkButton(btn_frame, text="저장", command=self.save_data, width=100, 
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"]).pack(side="left", padx=5)
                      
        ctk.CTkButton(btn_frame, text="종결", command=self.close_order, width=100, 
                      fg_color=COLORS["success"], hover_color=COLORS["success_hover"]).pack(side="left", padx=5)

    def _add_file_row(self, title, path):
        if path is None: path = ""
        path = str(path).strip()
        if not path or path == "-" or path.lower() == "nan" or path.lower() == "none":
            return False
            
        row = ctk.CTkFrame(self.files_scroll, fg_color="transparent")
        row.pack(fill="x", pady=2)
        
        # 1. Button (Right)
        ctk.CTkButton(row, text="열기", width=50, height=24,
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
                      command=lambda p=os.path.normpath(path): self.open_file(p)).pack(side="right", padx=5)
        
        # 2. Icon & Title
        ctk.CTkLabel(row, text="📄", font=FONTS["main"]).pack(side="left", padx=(5, 5))
        ctk.CTkLabel(row, text=title, font=FONTS["main_bold"], width=100, anchor="w").pack(side="left")
        
        # 3. Filename
        file_name = os.path.basename(path)
        if len(file_name) > 20:
            file_name = file_name[:17] + "..."
            
        ctk.CTkLabel(row, text=file_name, font=FONTS["small"], text_color=COLORS["text_dim"]).pack(side="left", padx=5)
        return True

    def open_file(self, path):
         if path and os.path.exists(path):
            try: os.startfile(path)
            except Exception as e: messagebox.showerror("에러", f"파일을 열 수 없습니다.\n{e}", parent=self)
            
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
