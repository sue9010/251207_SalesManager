import tkinter as tk
from datetime import datetime
from tkinter import messagebox

import customtkinter as ctk
import pandas as pd

# [변경] 경로 수정
from ui.popups.base_popup import BasePopup
from src.styles import COLORS, FONTS
from src.config import Config
from managers.export_manager import ExportManager

class OrderPopup(BasePopup):
    def __init__(self, parent, data_manager, refresh_callback, mgmt_no=None, copy_mode=False):
        self.export_manager = ExportManager()
        
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
    

    def _create_header(self, parent):
        # 공통 헤더 사용
        self._create_common_header(parent, "주문서 작성/수정", self.mgmt_no)
        
        # 추가 헤더 (Status) - 별도 프레임에 구성
        extra_frame = ctk.CTkFrame(parent, fg_color="transparent")
        extra_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(extra_frame, text="상태:", font=FONTS["main_bold"]).pack(side="left")
        self.combo_status = ctk.CTkComboBox(extra_frame, values=["주문", "생산중", "완료", "취소", "보류"], 
                                          width=100, font=FONTS["main"], state="readonly")
        self.combo_status.pack(side="left", padx=5)
        self.combo_status.set("주문")

        # entry_id 호환성 유지 (Hidden Entry)
        self.entry_id = ctk.CTkEntry(extra_frame, width=0)
        self.entry_id.insert(0, self.mgmt_no if self.mgmt_no else "NEW")

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
        
        self.lbl_total_qty = ctk.CTkLabel(total_frame, text="총 수량: 0", font=FONTS["main_bold"])
        self.lbl_total_qty.pack(side="right", padx=10)
        
        self.lbl_total_amt = ctk.CTkLabel(total_frame, text="총 합계: 0", font=FONTS["header"], text_color=COLORS["primary"])
        self.lbl_total_amt.pack(side="right", padx=20)

    def _setup_info_panel(self, parent):
        # 스크롤 제거하고 일반 프레임 사용 (공간 최적화)
        main_frame = ctk.CTkFrame(parent, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 1. 기본 정보 (2열 그리드)
        ctk.CTkLabel(main_frame, text="기본 정보", font=FONTS["header"]).pack(anchor="w", pady=(0, 5))
        
        info_grid = ctk.CTkFrame(main_frame, fg_color="transparent")
        info_grid.pack(fill="x", pady=(0, 10))
        
        # Helper to create labeled entry in grid
        def create_grid_input(parent, row, col, label, var_name, placeholder="", width=None):
            f = ctk.CTkFrame(parent, fg_color="transparent")
            f.grid(row=row, column=col, sticky="ew", padx=2, pady=2)
            ctk.CTkLabel(f, text=label, width=60, anchor="w", font=FONTS["main"], text_color=COLORS["text_dim"]).pack(side="left")
            entry = ctk.CTkEntry(f, height=28, placeholder_text=placeholder) # 높이 약간 줄임
            entry.pack(side="left", fill="x", expand=True)
            setattr(self, var_name, entry)
            return entry

        # Helper for ComboBox in grid
        def create_grid_combo(parent, row, col, label, values, cmd=None):
            f = ctk.CTkFrame(parent, fg_color="transparent")
            f.grid(row=row, column=col, sticky="ew", padx=2, pady=2)
            ctk.CTkLabel(f, text=label, width=60, anchor="w", font=FONTS["main"], text_color=COLORS["text_dim"]).pack(side="left")
            combo = ctk.CTkComboBox(f, values=values, command=cmd, height=28)
            combo.pack(side="left", fill="x", expand=True)
            return combo

        info_grid.columnconfigure(0, weight=1)
        info_grid.columnconfigure(1, weight=1)
        # Row 0: 고객사 (Full Width)
        f_client = ctk.CTkFrame(info_grid, fg_color="transparent")
        f_client.grid(row=0, column=0, columnspan=2, sticky="ew", padx=2, pady=2)
        ctk.CTkLabel(f_client, text="고객사", width=60, anchor="w", font=FONTS["main"], text_color=COLORS["text_dim"]).pack(side="left")
        
        # [변경] 위젯 경로 수정
        from ui.widgets.autocomplete_entry import AutocompleteEntry
        
        self.entry_client = AutocompleteEntry(f_client, font=FONTS["main"], height=28,
                                            completevalues=self.dm.df_clients["업체명"].unique().tolist(),
                                            command=self._on_client_select,
                                            on_focus_out=self._on_client_select)
        self.entry_client.pack(side="left", fill="x", expand=True)
        self.entry_client.set_completion_list(self.dm.df_clients["업체명"].unique().tolist())
        
        # 직접 입력 후 엔터 시에도 업데이트 (FocusOut은 AutocompleteEntry 내부에서 처리)
        self.entry_client.bind("<Return>", lambda e: self._on_client_select(self.entry_client.get()))

        # Row 1: 프로젝트 (Full Width)
        create_grid_input(info_grid, 1, 0, "프로젝트", "entry_project").master.grid(columnspan=2)
        
        # Row 2: 주문일자 | 발주서No
        date_entry = create_grid_input(info_grid, 2, 0, "주문일자", "entry_date")
        # date_entry.insert(0, datetime.now().strftime("%Y-%m-%d")) # __init__에서 처리됨
        create_grid_input(info_grid, 2, 1, "발주서No", "entry_po_no")
        
        # Row 3: 구분 | 통화
        self.combo_type = create_grid_combo(info_grid, 3, 0, "구분", ["내수", "수출"], self.on_type_change)
        self.combo_type.set("내수")
        self.combo_currency = create_grid_combo(info_grid, 3, 1, "통화", ["KRW", "USD", "EUR", "CNY", "JPY"], self.on_currency_change)
        self.combo_currency.set("KRW")
        
        # Row 4: 세율 | (Empty)
        tax_entry = create_grid_input(info_grid, 4, 0, "세율(%)", "entry_tax_rate")
        tax_entry.insert(0, "10")
        tax_entry.bind("<KeyRelease>", lambda e: self._calculate_totals())

        ctk.CTkFrame(main_frame, height=1, fg_color=COLORS["border"]).pack(fill="x", pady=5)

        # 2. 추가 정보
        self.lbl_client_note = ctk.CTkLabel(main_frame, text="업체 특이사항: -", font=FONTS["main"], text_color=COLORS["danger"], anchor="w")
        self.lbl_client_note.pack(fill="x", pady=(0, 2))
        
        note_grid = ctk.CTkFrame(main_frame, fg_color="transparent")
        note_grid.pack(fill="x", pady=(0, 5))
        note_grid.columnconfigure(0, weight=1)
        
        create_grid_input(note_grid, 0, 0, "주문요청", "entry_req")
        create_grid_input(note_grid, 1, 0, "비고", "entry_note")

        ctk.CTkFrame(main_frame, height=1, fg_color=COLORS["border"]).pack(fill="x", pady=5)

        # 3. 서류 발행 (가로 배치)
        ctk.CTkLabel(main_frame, text="서류 발행", font=FONTS["header"]).pack(anchor="w", pady=(0, 5))
        doc_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        doc_frame.pack(fill="x")
        
        ctk.CTkButton(doc_frame, text="📄 PI", command=self.export_pi, height=30, width=80,
                      fg_color=COLORS["bg_light"], hover_color=COLORS["primary_hover"], 
                      text_color=COLORS["text"], font=FONTS["main_bold"]).pack(side="left", fill="x", expand=True, padx=(0, 2))
                      
        ctk.CTkButton(doc_frame, text="📄 출고요청서", command=self.export_order_request, height=30, width=80,
                      fg_color=COLORS["bg_light"], hover_color=COLORS["primary_hover"], 
                      text_color=COLORS["text"], font=FONTS["main_bold"]).pack(side="left", fill="x", expand=True, padx=(2, 0))

        ctk.CTkFrame(main_frame, height=1, fg_color=COLORS["border"]).pack(fill="x", pady=10)

        # 발주서 파일 입력 (Standardized UI)
        self.entry_order_file, _, _ = self.create_file_input_row(main_frame, "발주서 파일", "발주서경로")



        
        # Update row calcs if tax rate changed
        # (Optional: iterate and recalculate all rows if tax rate changed globally)

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
        self.entry_req.delete(0, "end"); self.entry_req.insert(0, str(first.get("주문요청사항", "")).replace("nan", ""))
        self.entry_note.delete(0, "end"); self.entry_note.insert(0, str(first.get("비고", "")))
        
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
        
        self.entry_req.delete(0, "end"); self.entry_req.insert(0, str(first.get("주문요청사항", "")).replace("nan", ""))
        self.entry_note.delete(0, "end"); self.entry_note.insert(0, str(first.get("비고", "")))
        
        self._on_client_select(client_name)
        for _, row in rows.iterrows(): self._add_item_row(row)
        
        self.title(f"주문 복사 등록 (원본: {self.copy_src_no}) - Sales Manager")



    # ==========================================================================
    # 저장 및 삭제
    # ==========================================================================
    def save(self):
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
        req_note_val = self.entry_req.get()
        
        new_rows = []
        req_note_val = self.entry_req.get()
        
        # File Save Logic
        order_file_path = ""
        success, msg, new_path = self.file_manager.save_file(
             "발주서경로", "발주서", "PO", client
        )
        if success:
             order_file_path = new_path
        else:
             messagebox.showwarning("파일 저장 실패", f"파일 저장에 실패했습니다. 기존 경로를 유지합니다.\n{msg}", parent=self)
             # If save failed, maybe still proceed but with warning? or abort?
             # For now, if failed, we assume path is empty or original path if it was open error.
             # Actually save_file returns info_text as path if "Already in place".
             # If "File not found", it returns false.
             # If we proceed without file, maybe that's intended if file was optional.
             # But if user provided a file and it failed, they should know.
             if self.entry_order_file.get().strip(): # Attempted to provide file
                  pass # Warning shown.

        if not order_file_path: # Fallback to existing or entry if save failed (though save_file handles most)
             order_file_path = self.full_paths.get("발주서경로", "")
             if not order_file_path and self.entry_order_file:
                  order_file_path = self.entry_order_file.get().strip()

        common_data = {
            "관리번호": mgmt_no,
            "구분": self.combo_type.get(),
            "업체명": client,
            "프로젝트명": self.entry_project.get(),
            "통화": self.combo_currency.get(),
            "환율": 1, 
            "세율(%)": tax_rate_val,
            "주문요청사항": req_note_val,
            "비고": self.entry_note.get(),
            "Status": self.combo_status.get(),
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

        def update_logic(dfs):
            if self.mgmt_no:
                mask = dfs["data"]["관리번호"] == self.mgmt_no
                existing_rows = dfs["data"][mask]
                if not existing_rows.empty:
                    first_exist = existing_rows.iloc[0]
                    # Preserve columns that are NOT edited in this popup but might exist
                    preserve_cols = ["출고예정일", "출고일", "입금완료일", 
                                     "세금계산서발행일", "계산서번호", "수출신고번호"]
                    for row in new_rows:
                        for col in preserve_cols:
                            row[col] = first_exist.get(col, "-")
                        
                dfs["data"] = dfs["data"][~mask]
            
            new_df = pd.DataFrame(new_rows)
            dfs["data"] = pd.concat([dfs["data"], new_df], ignore_index=True)
            
            if self.copy_mode:
                action = "복사 등록"
                log_msg = f"주문 복사: [{self.copy_src_no}] -> [{mgmt_no}] / 업체 [{client}]"
            else:
                action = "수정" if self.mgmt_no else "등록"
                log_msg = f"주문 {action}: 번호 [{mgmt_no}] / 업체 [{client}]"
                
            new_log = self.dm._create_log_entry(f"주문 {action}", log_msg)
            dfs["log"] = pd.concat([dfs["log"], pd.DataFrame([new_log])], ignore_index=True)
            
            return True, ""

        success, msg = self.dm._execute_transaction(update_logic)
        
        if success:
            messagebox.showinfo("완료", "저장되었습니다.", parent=self)
            self.refresh_callback()
            self.destroy()
        else:
            messagebox.showerror("실패", msg, parent=self)


    # BasePopup 추상 메서드 구현 (사용 안함)
    def _generate_new_id(self):
        new_id = super()._generate_new_id("O", "수주일") # 주문일자 기준
        
        if hasattr(self, 'entry_id'):
            self.entry_id.configure(state="normal")
            self.entry_id.delete(0, "end")
            self.entry_id.insert(0, new_id)
            



    # delete는 BasePopup 사용
    # def delete(self): ...

    # ==========================================================================
    # Export
    # ==========================================================================
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
            "req_note": self.entry_req.get(),
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