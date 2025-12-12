import tkinter as tk
from datetime import datetime
from tkinter import messagebox
import customtkinter as ctk
import pandas as pd

from ui.popups.base_popup import BasePopup
from src.styles import COLORS, FONTS
from src.config import Config
from managers.export_manager import ExportManager
from ui.widgets.autocomplete_entry import AutocompleteEntry

class OrderPopup(BasePopup):
    def __init__(self, parent, data_manager, refresh_callback, mgmt_no=None, copy_mode=False):
        self.export_manager = ExportManager(data_manager)
        
        self.copy_mode = copy_mode
        self.copy_src_no = mgmt_no if copy_mode else None
        
        real_mgmt_no = None if copy_mode else mgmt_no
        
        self.item_widgets_map = {} # 위젯 추적용
        self.item_rows = [] # 데이터 추적용 (BasePopup 호환)

        super().__init__(parent, data_manager, refresh_callback, popup_title="주문", mgmt_no=real_mgmt_no)
        self.geometry("1350x750")

        if not real_mgmt_no:
            self.entry_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
            self.combo_status.set("주문")
            self._generate_new_id()
            
        if self.copy_mode and self.copy_src_no:
            self._load_copied_data()

        # [신규] 품목 추가 단축키 (Ctrl + +)
        self.bind("<Control-plus>", self._on_add_item_shortcut)
        self.bind("<Control-equal>", self._on_add_item_shortcut)

    def _create_header(self, parent):
        # 공통 헤더 사용 (Title + ID)
        header_frame = ctk.CTkFrame(parent, height=50, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 10))
        
        title_text = f"{self.popup_title} #{self.mgmt_no}" if self.mgmt_no else f"새 {self.popup_title}"
        self.lbl_title = ctk.CTkLabel(header_frame, text=title_text, font=FONTS["header"])
        self.lbl_title.pack(side="left", padx=10)
        
        extra_frame = ctk.CTkFrame(parent, fg_color="transparent")
        extra_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(extra_frame, text="상태:", font=FONTS["main_bold"]).pack(side="left")
        self.combo_status = ctk.CTkComboBox(extra_frame, values=["주문", "생산중", "완료", "취소", "보류"], 
                                          width=100, font=FONTS["main"], state="readonly")
        self.combo_status.pack(side="left", padx=5)
        self.combo_status.set("주문")
        
        # 주문번호 표시
        ctk.CTkLabel(extra_frame, text="주문번호:", font=FONTS["main_bold"]).pack(side="left", padx=(20, 5))
        self.entry_id = ctk.CTkEntry(extra_frame, width=120) 
        self.entry_id.pack(side="left")
        if self.mgmt_no: self.entry_id.insert(0, self.mgmt_no)
        else: self.entry_id.insert(0, "NEW")
        self.entry_id.configure(state="readonly")

    def _setup_info_panel(self, parent):
        # 1행: 수주일, 구분
        self.entry_date = self.create_grid_input(parent, 0, 0, "수주일", placeholder="YYYY-MM-DD")
        self.combo_type = self.create_grid_combo(parent, 0, 1, "구분", ["내수", "수출"], command=self.on_type_change)

        # 2행: 통화, 세율
        self.combo_currency = self.create_grid_combo(parent, 1, 0, "통화", ["KRW", "USD", "EUR", "CNY", "JPY"], command=self.on_currency_change)
        self.entry_tax_rate = self.create_grid_input(parent, 1, 1, "세율(%)")

        # 3행: 프로젝트명
        f_project = ctk.CTkFrame(parent, fg_color="transparent")
        f_project.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        ctk.CTkLabel(f_project, text="프로젝트명", width=60, anchor="w", font=FONTS["main"], text_color=COLORS["text_dim"]).pack(side="left")
        self.entry_project = ctk.CTkEntry(f_project, height=28, fg_color=COLORS["entry_bg"], border_color=COLORS["entry_border"], border_width=2)
        self.entry_project.pack(side="left", fill="x", expand=True)

        # 4행: 업체명
        f_client = ctk.CTkFrame(parent, fg_color="transparent")
        f_client.grid(row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        ctk.CTkLabel(f_client, text="업체명", width=60, anchor="w", font=FONTS["main"], text_color=COLORS["text_dim"]).pack(side="left")
        
        client_names = self.dm.df_clients["업체명"].unique().tolist() if not self.dm.df_clients.empty else []
        self.entry_client = AutocompleteEntry(f_client, completevalues=client_names, command=self._on_client_select,
                                              height=28, fg_color=COLORS["entry_bg"], border_color=COLORS["entry_border"], border_width=2)
        self.entry_client.pack(side="left", fill="x", expand=True)

        # 5행: 결제조건, 지급조건
        self.entry_payment_terms = self.create_grid_input(parent, 4, 0, "결제조건")
        self.entry_payment_cond = self.create_grid_input(parent, 4, 1, "지급조건")

        # 6행: 발주서 No.
        f_po = ctk.CTkFrame(parent, fg_color="transparent")
        f_po.grid(row=5, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        ctk.CTkLabel(f_po, text="발주서 No.", width=60, anchor="w", font=FONTS["main"], text_color=COLORS["text_dim"]).pack(side="left")
        self.entry_po_no = ctk.CTkEntry(f_po, height=28, fg_color=COLORS["entry_bg"], border_color=COLORS["entry_border"], border_width=2)
        self.entry_po_no.pack(side="left", fill="x", expand=True)

        # 7행: 주문요청
        f_req = ctk.CTkFrame(parent, fg_color="transparent")
        f_req.grid(row=6, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        ctk.CTkLabel(f_req, text="주문요청", width=60, anchor="w", font=FONTS["main"], text_color=COLORS["text_dim"]).pack(side="left")
        self.entry_req = ctk.CTkTextbox(f_req, height=60, fg_color=COLORS["entry_bg"], border_color=COLORS["entry_border"], border_width=2)
        self.entry_req.pack(side="left", fill="x", expand=True)

        # 8행: 비고
        f_note = ctk.CTkFrame(parent, fg_color="transparent")
        f_note.grid(row=7, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        ctk.CTkLabel(f_note, text="비고", width=60, anchor="w", font=FONTS["main"], text_color=COLORS["text_dim"]).pack(side="left", anchor="n", pady=5)
        self.entry_note = ctk.CTkTextbox(f_note, height=60, fg_color=COLORS["entry_bg"], border_color=COLORS["entry_border"], border_width=2)
        self.entry_note.pack(side="left", fill="x", expand=True)

        # 9행: 발주서 파일
        f_file = ctk.CTkFrame(parent, fg_color="transparent")
        f_file.grid(row=8, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        self.entry_order_file, _, _ = self.create_file_input_row(f_file, "발주서 파일", "발주서경로")

        # 10행: 버튼 (견적서발행, 출고요청서, PI발행)
        f_btn = ctk.CTkFrame(parent, fg_color="transparent")
        f_btn.grid(row=9, column=0, columnspan=2, sticky="ew", padx=5, pady=(20, 5))
        
        ctk.CTkButton(f_btn, text="📄 견적서 발행 (PDF)", command=self.export_quote, height=30, width=120,
                      fg_color=COLORS["bg_light"], hover_color=COLORS["primary_hover"], 
                      text_color=COLORS["text"], font=FONTS["main_bold"]).pack(side="left", padx=5, expand=True)

        ctk.CTkButton(f_btn, text="📄 출고요청서 (PDF)", command=self.export_order_request, height=30, width=120,
                      fg_color=COLORS["bg_light"], hover_color=COLORS["primary_hover"], 
                      text_color=COLORS["text"], font=FONTS["main_bold"]).pack(side="left", padx=5, expand=True)
                      
        ctk.CTkButton(f_btn, text="📄 PI 발행 (PDF)", command=self.export_pi, height=30, width=120,
                      fg_color=COLORS["bg_light"], hover_color=COLORS["primary_hover"], 
                      text_color=COLORS["text"], font=FONTS["main_bold"]).pack(side="left", padx=5, expand=True)

    def _setup_items_panel(self, parent):
        # 타이틀 & 추가 버튼
        title_frame = ctk.CTkFrame(parent, fg_color="transparent")
        title_frame.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(title_frame, text="주문 품목 리스트", font=FONTS["header"]).pack(side="left")
        
        ctk.CTkButton(title_frame, text="+ 품목 추가", command=self._add_item_row, width=100, height=30,
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"]).pack(side="right")
        
        # 헤더 (BasePopup.COL_CONFIG 사용)
        configs = [
            self.COL_CONFIG["item"], self.COL_CONFIG["model"], self.COL_CONFIG["desc"],
            self.COL_CONFIG["qty"], self.COL_CONFIG["price"], self.COL_CONFIG["supply"],
            self.COL_CONFIG["tax"], self.COL_CONFIG["total"], self.COL_CONFIG["delete"]
        ]
        
        header_frame = ctk.CTkFrame(parent, height=35, fg_color=COLORS["bg_dark"])
        header_frame.pack(fill="x", padx=15)
        
        for conf in configs:
            ctk.CTkLabel(header_frame, text=conf["header"], width=conf["width"], font=FONTS["main_bold"]).pack(side="left", padx=2)
            
        self.scroll_items = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        self.scroll_items.pack(fill="both", expand=True, padx=10, pady=5)
        
        # 합계 표시 영역
        total_frame = ctk.CTkFrame(parent, fg_color="transparent", height=40)
        total_frame.pack(fill="x", padx=20, pady=10)
        
    def on_type_change(self, type_val): self._calculate_totals()

    def on_currency_change(self, currency):
        if currency == "KRW":
            self.entry_tax_rate.delete(0, "end")
            self.entry_tax_rate.insert(0, "10")
            self.combo_type.set("내수")
        else:
            self.entry_tax_rate.delete(0, "end")
            self.entry_tax_rate.insert(0, "0")
            self.combo_type.set("수출")
        self._calculate_totals()
        
        # Recalculate all rows
        for row in self.item_rows: self.calculate_row(row)


    def _load_data(self):
        df = self.dm.df_data
        rows = df[df["관리번호"] == self.mgmt_no]
        if rows.empty: return
        
        first = rows.iloc[0]
        self.entry_id.configure(state="normal")
        self.entry_id.delete(0, "end")
        self.entry_id.insert(0, str(first["관리번호"]))
        self.entry_id.configure(state="readonly")
        
        date_val = str(first.get("수주일", ""))
        if not date_val or date_val == "nan" or date_val == "-":
            date_val = datetime.now().strftime("%Y-%m-%d")
        self.entry_date.delete(0, "end"); self.entry_date.insert(0, date_val)

        self.combo_type.set(str(first.get("구분", "내수")))
        
        client_name = str(first.get("업체명", ""))
        self.entry_client.set_value(client_name) # AutocompleteEntry method
        
        self.combo_currency.set(str(first.get("통화", "KRW")))
        
        po_no = str(first.get("발주서번호", "")).replace("nan", "")
        self.entry_po_no.delete(0, "end"); self.entry_po_no.insert(0, po_no)
        
        saved_tax = first.get("세율(%)", "")
        if saved_tax != "" and saved_tax != "-": tax_rate = str(saved_tax)
        else:
            currency = str(first.get("통화", "KRW"))
            tax_rate = "10" if currency == "KRW" else "0"
        self.entry_tax_rate.delete(0, "end"); self.entry_tax_rate.insert(0, tax_rate)

        self.entry_project.delete(0, "end"); self.entry_project.insert(0, str(first.get("프로젝트명", "")))
        
        self.entry_payment_terms.delete(0, "end"); self.entry_payment_terms.insert(0, str(first.get("결제조건", "")).replace("nan", ""))
        self.entry_payment_cond.delete(0, "end"); self.entry_payment_cond.insert(0, str(first.get("지급조건", "")).replace("nan", ""))
        
        self.entry_req.delete("1.0", "end"); self.entry_req.insert("1.0", str(first.get("주문요청사항", "")).replace("nan", ""))
        
        # Note (Multiline)
        note_val = str(first.get("비고", ""))
        self.entry_note.delete("1.0", "end")
        self.entry_note.insert("1.0", note_val)
        
        if self.entry_order_file:
            path = str(first.get("발주서경로", "")).replace("nan", "")
            if path: self.update_file_entry("발주서경로", path)
            
        current_status = str(first.get("Status", "주문"))
        self.combo_status.set(current_status)
        
        self._on_client_select(client_name)
        for _, row in rows.iterrows(): self._add_item_row(row)

    def _load_copied_data(self):
        df = self.dm.df_data
        rows = df[df["관리번호"] == self.copy_src_no]
        if rows.empty: return
        
        first = rows.iloc[0]
        
        self.combo_type.set(str(first.get("구분", "내수")))
        
        client_name = str(first.get("업체명", ""))
        self.entry_client.set_value(client_name)
        
        po_no = str(first.get("발주서번호", "")).replace("nan", "")
        self.entry_po_no.delete(0, "end"); self.entry_po_no.insert(0, po_no)

        self.combo_currency.set(str(first.get("통화", "KRW")))
        
        saved_tax = first.get("세율(%)", "")
        if saved_tax != "" and saved_tax != "-": tax_rate = str(saved_tax)
        else:
            currency = str(first.get("통화", "KRW"))
            tax_rate = "10" if currency == "KRW" else "0"
        self.entry_tax_rate.delete(0, "end"); self.entry_tax_rate.insert(0, tax_rate)

        original_proj = str(first.get("프로젝트명", ""))
        self.entry_project.delete(0, "end"); self.entry_project.insert(0, f"{original_proj} (Copy)")
        
        self.entry_payment_terms.delete(0, "end"); self.entry_payment_terms.insert(0, str(first.get("결제조건", "")).replace("nan", ""))
        self.entry_payment_cond.delete(0, "end"); self.entry_payment_cond.insert(0, str(first.get("지급조건", "")).replace("nan", ""))
        
        self.entry_req.delete("1.0", "end"); self.entry_req.insert("1.0", str(first.get("주문요청사항", "")).replace("nan", ""))
        
        # Note (Multiline)
        note_val = str(first.get("비고", ""))
        self.entry_note.delete("1.0", "end")
        self.entry_note.insert("1.0", note_val)
        
        self._on_client_select(client_name)
        for _, row in rows.iterrows(): self._add_item_row(row)
        
        self.title(f"주문 복사 등록 (원본: {self.copy_src_no}) - Sales Manager")

    # ==========================================================================
    # 저장 및 삭제
    # ==========================================================================
    def save(self, destroy_after=True):
        mgmt_no = self.entry_id.get()
        client = self.entry_client.get()
        
        if not client:
            messagebox.showwarning("경고", "고객사를 선택해주세요.", parent=self)
            return
        if not self.item_rows:
            messagebox.showwarning("경고", "최소 1개 이상의 품목을 추가해주세요.", parent=self)
            return

        try: tax_rate_val = float(self.entry_tax_rate.get().strip())
        except: tax_rate_val = 0

        new_rows = []
        req_note_val = self.entry_req.get("1.0", "end-1c")
        
        # File Save Logic
        order_file_path = ""
        success, msg, new_path = self.file_manager.save_file(
             "발주서경로", "발주서", "PO", client
        )
        if success:
             order_file_path = new_path
        else:
             if self.entry_order_file.get().strip():
                 messagebox.showwarning("파일 저장 실패", f"파일 저장에 실패했습니다. 기존 경로를 유지하거나 저장되지 않을 수 있습니다.\n{msg}", parent=self)

        if not order_file_path: 
             order_file_path = self.full_paths.get("발주서경로", "")
             if not order_file_path and self.entry_order_file:
                  order_file_path = self.entry_order_file.get().strip()
        
        # Force Status to "주문"
        # Force Status to "주문" -> Removed to respect current status
        # self.combo_status.set("주문")

        common_data = {
            "관리번호": mgmt_no,
            "구분": self.combo_type.get(),
            "업체명": client,
            "프로젝트명": self.entry_project.get(),
            "통화": self.combo_currency.get(),
            "환율": 1, 
            "세율(%)": tax_rate_val,
            "결제조건": self.entry_payment_terms.get(),
            "지급조건": self.entry_payment_cond.get(),
            "주문요청사항": req_note_val,
            "비고": self.entry_note.get("1.0", "end-1c"), # Multiline get
            "Status": self.combo_status.get(), # Use current status
            "발주서경로": order_file_path,
            "수주일": self.entry_date.get(),
            "발주서번호": self.entry_po_no.get().strip()
        }
        
        for item in self.item_rows:
            row_data = common_data.copy()
            row_data.update({
                "품목명": item["item"].get(), "모델명": item["model"].get(), "Description": item["desc"].get(),
                "수량": float(item["qty"].get().replace(",","") or 0),
                "단가": float(item["price"].get().replace(",","") or 0),
                "공급가액": float(item["supply"].get().replace(",","") or 0),
                "세액": float(item["tax"].get().replace(",","") or 0),
                "합계금액": float(item["total"].get().replace(",","") or 0),
                "기수금액": 0, "미수금액": float(item["total"].get().replace(",","") or 0)
            })
            new_rows.append(row_data)

        if self.mgmt_no and not self.copy_mode:
            success, msg = self.dm.update_order(mgmt_no, new_rows, client)
        else:
            # Copy mode or New
            success, msg = self.dm.add_order(new_rows, mgmt_no, client)
        
        if success:
            messagebox.showinfo("완료", "저장되었습니다.", parent=self)
            self.refresh_callback()
            if destroy_after:
                self.destroy()
            return True, "저장되었습니다.", new_rows
        else:
            messagebox.showerror("실패", msg, parent=self)
            return False, msg, []

    def delete(self):
        if messagebox.askyesno("삭제 확인", f"정말 이 주문({self.mgmt_no})을 삭제하시겠습니까?", parent=self):
            success, msg = self.dm.delete_order(self.mgmt_no)
            if success:
                messagebox.showinfo("삭제 완료", "삭제되었습니다.", parent=self)
                self.refresh_callback()
                self.destroy()
            else:
                messagebox.showerror("실패", msg, parent=self)

    def export_quote(self):
        client_name = self.entry_client.get()
        if not client_name:
            self.attributes("-topmost", False)
            messagebox.showwarning("경고", "고객사를 선택해주세요.", parent=self)
            self.attributes("-topmost", True)
            return

        client_row = self.dm.df_clients[self.dm.df_clients["업체명"] == client_name]
        if client_row.empty:
            self.attributes("-topmost", False)
            messagebox.showerror("오류", "고객 정보를 찾을 수 없습니다.", parent=self)
            self.attributes("-topmost", True)
            return
        
        quote_info = {
            "client_name": client_name,
            "mgmt_no": self.entry_id.get(),
            "date": self.entry_date.get(),
            "valid_until": "", 
            "payment_terms": self.entry_payment_terms.get(),
            "payment_cond": self.entry_payment_cond.get(),
            "warranty": "",
            "tax_rate": self.entry_tax_rate.get(),
            "currency": self.combo_currency.get(),
            "note": self.entry_note.get("1.0", "end-1c")
        }
        
        items = []
        for row in self.item_rows:
            items.append({
                "item": row["item"].get(),
                "model": row["model"].get(),
                "desc": row["desc"].get(),
                "qty": float(row["qty"].get().replace(",", "") or 0),
                "price": float(row["price"].get().replace(",", "") or 0),
                "supply": float(row["supply"].get().replace(",", "") or 0),
                "tax": float(row["tax"].get().replace(",", "") or 0),
                "total": float(row["total"].get().replace(",", "") or 0)
            })

        success, result = self.export_manager.export_quote_to_pdf(
            client_row.iloc[0], quote_info, items
        )
        
        self.attributes("-topmost", False)
        if success:
            messagebox.showinfo("성공", f"견적서가 생성되었습니다.\n{result}", parent=self)
        else:
            messagebox.showerror("실패", result, parent=self)
        self.attributes("-topmost", True)

    def export_order_request(self):
        client_name = self.entry_client.get()
        if not client_name:
            self.attributes("-topmost", False)
            messagebox.showwarning("경고", "고객사를 선택해주세요.", parent=self)
            self.attributes("-topmost", True)
            return

        client_row = self.dm.df_clients[self.dm.df_clients["업체명"] == client_name]
        if client_row.empty:
            self.attributes("-topmost", False)
            messagebox.showerror("오류", "고객 정보를 찾을 수 없습니다.", parent=self)
            self.attributes("-topmost", True)
            return
        
        order_info = {
            "client_name": client_name,
            "mgmt_no": self.entry_id.get(),
            "date": self.entry_date.get(),
            "type": self.combo_type.get(),
            "req_note": self.entry_req.get("1.0", "end-1c"),
        }
        
        items = []
        for row in self.item_rows:
            items.append({
                "item": row["item"].get(),
                "model": row["model"].get(),
                "desc": row["desc"].get(),
                "qty": float(row["qty"].get().replace(",", "") or 0),
            })

        success, result = self.export_manager.export_order_request_to_pdf(
            client_row.iloc[0], order_info, items
        )
        
        self.attributes("-topmost", False)
        if success:
            messagebox.showinfo("성공", f"출고요청서가 생성되었습니다.\n{result}", parent=self)
        else:
            messagebox.showerror("실패", result, parent=self)
        self.attributes("-topmost", True)

    def export_pi(self):
        client_name = self.entry_client.get()
        if not client_name:
            self.attributes("-topmost", False)
            messagebox.showwarning("경고", "고객사를 선택해주세요.", parent=self)
            self.attributes("-topmost", True)
            return

        client_row = self.dm.df_clients[self.dm.df_clients["업체명"] == client_name]
        if client_row.empty:
            self.attributes("-topmost", False)
            messagebox.showerror("오류", "고객 정보를 찾을 수 없습니다.", parent=self)
            self.attributes("-topmost", True)
            return
        
        order_info = {
            "client_name": client_name,
            "mgmt_no": self.entry_id.get(),
            "date": self.entry_date.get(),
            "po_no": self.entry_po_no.get(), 
        }
        
        items = []
        for row in self.item_rows:
            items.append({
                "item": row["item"].get(),
                "model": row["model"].get(),
                "desc": row["desc"].get(),
                "qty": float(row["qty"].get().replace(",", "") or 0),
                "price": float(row["price"].get().replace(",", "") or 0),
                "amount": float(row["supply"].get().replace(",", "") or 0)
            })

        success, result = self.export_manager.export_pi_to_pdf(
            client_row.iloc[0], order_info, items
        )
        
        self.attributes("-topmost", False)
        if success:
            messagebox.showinfo("성공", f"PI가 생성되었습니다.\n{result}", parent=self)
        else:
            messagebox.showerror("실패", result, parent=self)
        self.attributes("-topmost", True)

    def _generate_new_id(self):
        new_id = self.dm.get_next_order_id()
        if hasattr(self, 'entry_id'):
            self.entry_id.configure(state="normal")
            self.entry_id.delete(0, "end")
            self.entry_id.insert(0, new_id)
            self.entry_id.configure(state="readonly")

    def _create_footer(self, parent):
        self.footer_frame = ctk.CTkFrame(parent, height=60, fg_color="transparent")
        self.footer_frame.pack(fill="x", pady=(10, 0), side="bottom")

        # 1. 취소 버튼 (항상 표시)
        self.btn_cancel = ctk.CTkButton(self.footer_frame, text="취소", command=self.destroy, width=80, height=40,
                      fg_color=COLORS["bg_light"], hover_color=COLORS["bg_light_hover"], text_color=COLORS["text"])
        self.btn_cancel.pack(side="right", padx=5)

        # 2. 신규/복사 vs 기존
        if not self.mgmt_no or self.copy_mode:
             # 신규/복사 모드 -> [생성] 버튼
            self.btn_save = ctk.CTkButton(self.footer_frame, text="생성", command=self.save, width=120, height=40,
                          fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"], font=FONTS["main_bold"])
            self.btn_save.pack(side="right", padx=5)
        else:
            # 기존 모드
            current_status = self.combo_status.get()
            
            if current_status == "주문":
                # 주문 상태 -> [주문 수정] [생산 시작]
                
                # 주문 수정
                self.btn_save = ctk.CTkButton(self.footer_frame, text="주문 수정", command=self.save, width=120, height=40,
                              fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"], font=FONTS["main_bold"])
                self.btn_save.pack(side="right", padx=5)
                
                # 생산 시작
                self.btn_start_production = ctk.CTkButton(self.footer_frame, text="생산 시작", command=self.start_production, width=120, height=40,
                                                          fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"], font=FONTS["main_bold"])
                self.btn_start_production.pack(side="right", padx=5)
            else:
                # 그 외 상태 -> [주문 저장]
                self.btn_save = ctk.CTkButton(self.footer_frame, text="주문 저장", command=self.save, width=120, height=40,
                              fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"], font=FONTS["main_bold"])
                self.btn_save.pack(side="right", padx=5)

    def start_production(self):
        if messagebox.askyesno("생산 시작", "주문 상태를 '생산중'으로 변경하고 저장하시겠습니까?", parent=self):
            self.combo_status.set("생산중")
            # 저장 후 데이터 받아오기 (팝업 닫지 않음)
            success, msg, saved_rows = self.save(destroy_after=False)
            
            if success:
                # 생산 요청 파일로 내보내기
                export_success, export_msg = self.dm.export_to_production_request(saved_rows)
                
                if export_success:
                    messagebox.showinfo("생산 요청 완료", f"생산 요청이 완료되었습니다.\n{export_msg}", parent=self)
                else:
                    messagebox.showwarning("생산 요청 실패", f"주문은 저장되었으나 생산 요청 파일 업데이트에 실패했습니다.\n{export_msg}", parent=self)
                
                self.destroy()