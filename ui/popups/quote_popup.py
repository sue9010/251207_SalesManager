import tkinter as tk
from datetime import datetime
from tkinter import messagebox
import customtkinter as ctk
import pandas as pd

# [변경] 경로 수정
from ui.popups.base_popup import BasePopup
from src.styles import COLORS, FONTS
from managers.export_manager import ExportManager

class QuotePopup(BasePopup):
    def __init__(self, parent, data_manager, refresh_callback, mgmt_no=None, copy_mode=False):
        self.export_manager = ExportManager(data_manager)
        self.copy_mode = copy_mode
        self.copy_src_no = mgmt_no if copy_mode else None
        
        # [수정] 복사 모드일 경우, 부모 클래스에는 mgmt_no를 None(신규)으로 전달하여 새 번호를 따게 함
        real_mgmt_no = None if copy_mode else mgmt_no
        
        self.item_widgets_map = {} # 위젯 추적용
        self.item_rows = [] # 데이터 추적용 (BasePopup 호환)

        super().__init__(parent, data_manager, refresh_callback, popup_title="견적", mgmt_no=real_mgmt_no)
        self.geometry("1350x650")

        # 신규 등록(또는 복사)일 때 기본값 설정
        if not real_mgmt_no:
            self.entry_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
            self.combo_status.set("견적")
            self._generate_new_id()
            
        # [신규] 복사 모드라면 원본 데이터 로드하여 필드 채우기
        if self.copy_mode and self.copy_src_no:
            self._load_copied_data()
    

    def _create_header(self, parent):
        # 공통 헤더 사용 (Title + ID)
        header_frame = self._create_common_header(parent, "견적서 작성/수정", self.mgmt_no)
        
        # ID 위젯 참조 가져오기 (BasePopup에서 생성한 라벨을 덮어쓰거나 별도 처리?)
        # _create_common_header는 라벨만 생성하므로, ID Entry 기능을 쓰려면 커스텀해야 함.
        # 하지만 QuotePopup은 ID가 'NEW'로 시작했다가 저장 시 바뀌고, Status 콤보도 있음.
        # BasePopup의 공통 헤더는 단순 라벨용이므로 QuotePopup의 복잡한 헤더와 안 맞을 수 있음.
        # 일단 Status 콤보박스를 위해 별도 프레임 추가
        
        extra_frame = ctk.CTkFrame(parent, fg_color="transparent")
        extra_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(extra_frame, text="상태:", font=FONTS["main_bold"]).pack(side="left")
        self.combo_status = ctk.CTkComboBox(extra_frame, values=["견적", "진행중", "완료", "취소"], 
                                          width=100, font=FONTS["main"], state="readonly")
        self.combo_status.pack(side="left", padx=5)
        self.combo_status.set("견적")
        
        # ID는 _create_common_header에서 그려진 라벨로 대체하거나, 
        # QuotePopup 특성상 Entry가 필요하다면 _create_common_header를 쓰지 말아야 할 수도 있음.
        # 여기서는 self.entry_id 가 코드 곳곳에서 쓰이므로(저장 등), 이를 유지해야 함.
        # 따라서 _create_common_header 사용 보다는 독자 구현 유지가 나을 수도 있으나, 
        # 사용자 요청이 '중복 제거' 이므로 최대한 활용해봄.
        
        # BasePopup의 _create_common_header는 entry_id를 멤버변수로 만들지 않음.
        # Hack: entry_id를 안 보이게(hidden) 만들어서 로직 호환성 유지
        self.entry_id = ctk.CTkEntry(extra_frame, width=0) 
        if self.mgmt_no: self.entry_id.insert(0, self.mgmt_no)
        else: self.entry_id.insert(0, "NEW")

    def _setup_items_panel(self, parent):
        # 타이틀 & 추가 버튼
        title_frame = ctk.CTkFrame(parent, fg_color="transparent")
        title_frame.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(title_frame, text="견적 품목 리스트", font=FONTS["header"]).pack(side="left")
        
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
        
        # Row 2: 견적일자 | (Empty or something else)
        date_entry = create_grid_input(info_grid, 2, 0, "견적일자", "entry_date")
        # date_entry.insert(0, datetime.now().strftime("%Y-%m-%d")) # __init__에서 처리됨
        
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
        
        create_grid_input(note_grid, 0, 0, "비고", "entry_note")

        ctk.CTkFrame(main_frame, height=1, fg_color=COLORS["border"]).pack(fill="x", pady=5)

        # 3. 서류 발행 (가로 배치)
        ctk.CTkLabel(main_frame, text="서류 발행", font=FONTS["header"]).pack(anchor="w", pady=(0, 5))
        doc_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        doc_frame.pack(fill="x")
        
        ctk.CTkButton(doc_frame, text="📄 견적서 발행 (PDF)", command=self.export_quote, height=30,
                      fg_color=COLORS["bg_light"], hover_color=COLORS["primary_hover"], 
                      text_color=COLORS["text"], font=FONTS["main_bold"]).pack(side="left", fill="x", expand=True)



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
        
        date_val = str(first.get("견적일", ""))
        self.entry_date.delete(0, "end"); self.entry_date.insert(0, date_val)

        self.combo_type.set(str(first.get("구분", "내수")))
        
        client_name = str(first.get("업체명", ""))
        self.entry_client.set_value(client_name)
        
        self.combo_currency.set(str(first.get("통화", "KRW")))
        
        saved_tax = first.get("세율(%)", "")
        if saved_tax != "" and saved_tax != "-": tax_rate = str(saved_tax)
        else:
            currency = str(first.get("통화", "KRW"))
            tax_rate = "10" if currency == "KRW" else "0"
        self.entry_tax_rate.delete(0, "end"); self.entry_tax_rate.insert(0, tax_rate)

        self.entry_project.delete(0, "end"); self.entry_project.insert(0, str(first.get("프로젝트명", "")))
        self.entry_note.delete(0, "end"); self.entry_note.insert(0, str(first.get("비고", "")))
        
        current_status = str(first.get("Status", "견적"))
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
        
        self.combo_currency.set(str(first.get("통화", "KRW")))
        
        saved_tax = first.get("세율(%)", "")
        if saved_tax != "" and saved_tax != "-": tax_rate = str(saved_tax)
        else:
            currency = str(first.get("통화", "KRW"))
            tax_rate = "10" if currency == "KRW" else "0"
        self.entry_tax_rate.delete(0, "end"); self.entry_tax_rate.insert(0, tax_rate)

        original_proj = str(first.get("프로젝트명", ""))
        self.entry_project.delete(0, "end"); self.entry_project.insert(0, f"{original_proj} (Copy)")
        
        self.entry_note.delete(0, "end"); self.entry_note.insert(0, str(first.get("비고", "")))
        
        self._on_client_select(client_name)
        for _, row in rows.iterrows(): self._add_item_row(row)
        
        self.title(f"견적 복사 등록 (원본: {self.copy_src_no}) - Sales Manager")

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
        
        common_data = {
            "관리번호": mgmt_no,
            "구분": self.combo_type.get(),
            "업체명": client,
            "프로젝트명": self.entry_project.get(),
            "통화": self.combo_currency.get(),
            "환율": 1, 
            "세율(%)": tax_rate_val,
            "주문요청사항": "", # 견적은 주문요청사항 없음
            "비고": self.entry_note.get(),
            "Status": self.combo_status.get(),
            "견적일": self.entry_date.get()
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
            success, msg = self.dm.update_quote(mgmt_no, new_rows, client)
        else:
            # Copy mode or New
            success, msg = self.dm.add_quote(new_rows, mgmt_no, client)
        
        if success:
            messagebox.showinfo("완료", "저장되었습니다.", parent=self)
            self.refresh_callback()
            self.destroy()
        else:
            messagebox.showerror("실패", msg, parent=self)

    def delete(self):
        if messagebox.askyesno("삭제 확인", f"정말 이 견적({self.mgmt_no})을 삭제하시겠습니까?", parent=self):
            success, msg = self.dm.delete_quote(self.mgmt_no)
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
            "req_note": "",
            "note": self.entry_note.get()
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

        success, result = self.export_manager.export_quote_to_pdf(
            client_row.iloc[0], quote_info, items
        )
        
        self.attributes("-topmost", False)
        if success:
            messagebox.showinfo("성공", f"견적서가 생성되었습니다.\n{result}", parent=self)
        else:
            messagebox.showerror("실패", result, parent=self)
        self.attributes("-topmost", True)

    def _generate_new_id(self):
        new_id = self.dm.get_next_quote_id()
        
        # UI 업데이트 (entry_id가 존재한다면)
        if hasattr(self, 'entry_id'):
            self.entry_id.configure(state="normal")
            self.entry_id.delete(0, "end")
            self.entry_id.insert(0, new_id)
            # self.entry_id.configure(state="readonly") # Entry가 hidden이거나 dummy일 수 있으므로 상태 제어 주의