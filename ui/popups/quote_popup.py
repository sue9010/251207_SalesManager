
import tkinter as tk
from datetime import datetime, timedelta
from tkinter import messagebox
import customtkinter as ctk
import pandas as pd

from ui.popups.base_popup import BasePopup
from src.styles import COLORS, FONTS
from managers.export_manager import ExportManager
from ui.widgets.autocomplete_entry import AutocompleteEntry

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
        self.geometry("1350x920") # Height increased for multiline note

        # 신규 등록(또는 복사)일 때 기본값 설정
        if not real_mgmt_no:
            self.entry_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
            self.combo_status.set("견적")
            self.combo_currency.set("KRW")
            self.entry_tax_rate.insert(0, "10")
            self._generate_new_id()
            
        # [신규] 복사 모드라면 원본 데이터 로드하여 필드 채우기
        if self.copy_mode and self.copy_src_no:
            self._load_copied_data()

    def _create_header(self, parent):
        # 공통 헤더 사용 (Title + ID)
        header_frame = self._create_common_header(parent, "견적서 작성/수정", self.mgmt_no)
        
        extra_frame = ctk.CTkFrame(parent, fg_color="transparent")
        extra_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        ctk.CTkLabel(extra_frame, text="상태:", font=FONTS["main_bold"]).pack(side="left")
        self.combo_status = ctk.CTkComboBox(extra_frame, values=["견적", "진행중", "완료", "취소"], 
                                          width=100, font=FONTS["main"], state="readonly")
        self.combo_status.pack(side="left", padx=5)
        self.combo_status.set("견적")
        
        # 견적번호 표시
        ctk.CTkLabel(extra_frame, text="견적번호:", font=FONTS["main_bold"]).pack(side="left", padx=(20, 5))
        self.entry_id = ctk.CTkEntry(extra_frame, width=120) 
        self.entry_id.pack(side="left")
        if self.mgmt_no: self.entry_id.insert(0, self.mgmt_no)
        else: self.entry_id.insert(0, "NEW")
        self.entry_id.configure(state="readonly")
        
        # [신규] 업체 특이사항 라벨
        self.lbl_client_note = ctk.CTkLabel(extra_frame, text="", text_color=COLORS["danger"], font=FONTS["main_bold"])
        self.lbl_client_note.pack(side="left", padx=(20, 0))

    def _setup_info_panel(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(1, weight=1)

        # 1행: 견적일, 구분
        self.entry_date = self.create_grid_input(parent, 0, 0, "견적일", placeholder="YYYY-MM-DD")
        self.entry_date.bind("<FocusOut>", self._on_date_change) # 날짜 변경 시 유효기간 재계산
        self.combo_type = self.create_grid_combo(parent, 0, 1, "구분", ["내수", "수출"], command=self.on_type_change)

        # 2행: 통화, 세율
        self.combo_currency = self.create_grid_combo(parent, 1, 0, "통화", ["KRW", "USD", "EUR", "CNY", "JPY"], command=self.on_currency_change)
        self.entry_tax_rate = self.create_grid_input(parent, 1, 1, "세율(%)")
        self.entry_tax_rate.bind("<KeyRelease>", self._on_tax_change)

        # 3행: 프로젝트명 (Full Width)
        f_project = ctk.CTkFrame(parent, fg_color="transparent")
        f_project.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        ctk.CTkLabel(f_project, text="프로젝트명", width=60, anchor="w", font=FONTS["main"], text_color=COLORS["text_dim"]).pack(side="left")
        self.entry_project = ctk.CTkEntry(f_project, height=28, fg_color=COLORS["entry_bg"], border_color=COLORS["entry_border"], border_width=2)
        self.entry_project.pack(side="left", fill="x", expand=True)

        # 4행: 업체명 (Autocomplete) - Full Width
        f_client = ctk.CTkFrame(parent, fg_color="transparent")
        f_client.grid(row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        ctk.CTkLabel(f_client, text="업체명", width=60, anchor="w", font=FONTS["main"], text_color=COLORS["text_dim"]).pack(side="left")
        
        client_names = self.dm.df_clients["업체명"].unique().tolist() if not self.dm.df_clients.empty else []
        self.entry_client = AutocompleteEntry(f_client, completevalues=client_names, command=self._on_client_select,
                                              height=28, fg_color=COLORS["entry_bg"], border_color=COLORS["entry_border"], border_width=2)
        self.entry_client.pack(side="left", fill="x", expand=True)

        # 5행: 유효기간 (견적일 + 30일)
        self.entry_valid_until = self.create_grid_input(parent, 4, 0, "유효기간", placeholder="YYYY-MM-DD")
        
        # 5행 우측: 결제조건 (Conditional) -> 6행으로 이동 요청되었으나 "5행: 유효기간, 5행: 결제조건"이라 표기됨. 
        # 요청사항: "5행: 유효기간", "5행: 결제조건" -> 같은 행에 배치.
        self.entry_payment_terms = self.create_grid_input(parent, 4, 1, "결제조건")

        # 6행: 지급조건
        self.entry_payment_cond = self.create_grid_input(parent, 5, 0, "지급조건")
        
        # 7행: 보증기간 (6행 우측이 비어있으므로 6행 우측에 넣을지, 7행으로 갈지? 요청은 "6행: 지급조건", "7행: 보증기간" 명시됨.
        # 하지만 5행이 2개였음. 
        # 1행: 견적일, 구분
        # 2행: 통화, 세율
        # 3행: 프로젝트명
        # 4행: 업체명
        # 5행: 유효기간
        # 5행: 결제조건 (같은 5행으로 해석)
        # 6행: 지급조건
        # 7행: 보증기간
        # 9행: 비고 (8행 건너뜀?)
        # 순서대로 배치하겠습니다.
        
        # 수정 제안: 6행에 지급조건, 보증기간을 같이 넣겠습니다. (공간 활용)
        # 만약 사용자가 엄격하게 행을 구분하길 원한다면 수정하겠습니다. 
        # 일단 6행: 지급조건, 보증기간 (Grid 5,0 / 5,1) 로 배치하여 밸런스를 맞춥니다.
        self.entry_warranty = self.create_grid_input(parent, 5, 1, "보증기간")

        # 9행: 비고 (Grid 6, 0~1)
        f_note = ctk.CTkFrame(parent, fg_color="transparent")
        f_note.grid(row=6, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        ctk.CTkLabel(f_note, text="비고", width=60, anchor="w", font=FONTS["main"], text_color=COLORS["text_dim"]).pack(side="left", anchor="n", pady=5)
        self.entry_note = ctk.CTkTextbox(f_note, height=80, fg_color=COLORS["entry_bg"], border_color=COLORS["entry_border"], border_width=2)
        self.entry_note.pack(side="left", fill="x", expand=True)

        # PDF Export Button (Row 7)
        f_btn = ctk.CTkFrame(parent, fg_color="transparent")
        f_btn.grid(row=7, column=0, columnspan=2, sticky="ew", padx=5, pady=(20, 5))
        
        ctk.CTkButton(f_btn, text="📄 견적서 발행 (PDF)", command=self.export_quote, height=30,
                      fg_color=COLORS["bg_light"], hover_color=COLORS["primary_hover"], 
                      text_color=COLORS["text"], font=FONTS["main_bold"]).pack(fill="x")
        
        # 초기 유효기간 계산
        self._calculate_valid_until()

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

    def _on_tax_change(self, event=None):
        for row in self.item_rows:
            self.calculate_row(row)
        self._calculate_totals()

    def _on_date_change(self, event=None):
        self._calculate_valid_until()

    def _calculate_valid_until(self):
        date_str = self.entry_date.get()
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            valid_until = date_obj + timedelta(days=30)
            self.entry_valid_until.delete(0, "end")
            self.entry_valid_until.insert(0, valid_until.strftime("%Y-%m-%d"))
        except ValueError:
            pass # 날짜 형식이 올바르지 않으면 무시

    def _on_client_select(self, client_name):
        # 1. 업체 특이사항 표시
        client_row = self.dm.df_clients[self.dm.df_clients["업체명"] == client_name]
        if not client_row.empty:
            note = str(client_row.iloc[0].get("특이사항", ""))
            self.lbl_client_note.configure(text=f"※ {note}" if note else "")
            
            # 2. 국가 확인 및 조건부 필드 업데이트
            country = str(client_row.iloc[0].get("국가", ""))
            self._update_conditional_fields(country)
        else:
            self.lbl_client_note.configure(text="")
            # 클라이언트가 선택되지 않았거나 찾을 수 없을 경우 기본값으로 리셋
            self._update_conditional_fields("") # 빈 문자열을 넘겨 기본값으로 설정

    def _update_conditional_fields(self, country):
        # 국가가 KR/South Korea/Korea/대한민국/한국 인 경우
        korea_aliases = ["KR", "South Korea", "Korea", "대한민국", "한국"]
        is_korea = country in korea_aliases
        
        # 결제조건
        self.entry_payment_terms.delete(0, "end")
        self.entry_payment_terms.insert(0, "당사 공장 인도가" if is_korea else "EXW")
        
        # 지급조건
        self.entry_payment_cond.delete(0, "end")
        self.entry_payment_cond.insert(0, "납품 전 100%" if is_korea else "T/T in advance")
        
        # 보증기간
        self.entry_warranty.delete(0, "end")
        self.entry_warranty.insert(0, "2년" if is_korea else "2 years conditional")

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
        
        # New Fields
        self.entry_valid_until.delete(0, "end"); self.entry_valid_until.insert(0, str(first.get("유효기간", "")))
        self.entry_payment_terms.delete(0, "end"); self.entry_payment_terms.insert(0, str(first.get("결제조건", "")))
        self.entry_payment_cond.delete(0, "end"); self.entry_payment_cond.insert(0, str(first.get("지급조건", "")))
        self.entry_warranty.delete(0, "end"); self.entry_warranty.insert(0, str(first.get("보증기간", "")))
        
        # Note (Multiline)
        note_val = str(first.get("비고", ""))
        self.entry_note.delete("1.0", "end")
        self.entry_note.insert("1.0", note_val)
        
        current_status = str(first.get("Status", "견적"))
        self.combo_status.set(current_status)
        
        # _on_client_select 호출 시 조건부 필드가 덮어씌워질 수 있으므로, 
        # 저장된 값이 있다면 다시 복구해야 함. 
        # 하지만 로직상 클라이언트 선택 -> 자동채움 -> 사용자 수정 -> 저장 -> 로드 순서이므로
        # 로드 시에는 저장된 값을 우선해야 함.
        # 따라서 _on_client_select를 호출하되, 필드 값은 다시 설정
        self._on_client_select(client_name)
        
        # Restore saved values again just in case _on_client_select overwrote them with defaults
        if first.get("결제조건"): 
            self.entry_payment_terms.delete(0, "end"); self.entry_payment_terms.insert(0, str(first.get("결제조건")))
        if first.get("지급조건"):
            self.entry_payment_cond.delete(0, "end"); self.entry_payment_cond.insert(0, str(first.get("지급조건")))
        if first.get("보증기간"):
            self.entry_warranty.delete(0, "end"); self.entry_warranty.insert(0, str(first.get("보증기간")))
            
        # Load items
        for _, row in rows.iterrows():
            self._add_item_row(row)
        
        if self.copy_mode:
            self.title(f"견적 복사 등록 (원본: {self.copy_src_no}) - Sales Manager")
        else:
            self.title(f"견적 수정 ({self.mgmt_no}) - Sales Manager")

    def _load_copied_data(self):
        df = self.dm.df_data
        rows = df[df["관리번호"] == self.copy_src_no]
        if rows.empty: return
        
        first = rows.iloc[0]
        
        # ID is already generated as NEW in __init__
        
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
        
        # New Fields
        self.entry_valid_until.delete(0, "end"); self.entry_valid_until.insert(0, str(first.get("유효기간", "")))
        self.entry_payment_terms.delete(0, "end"); self.entry_payment_terms.insert(0, str(first.get("결제조건", "")))
        self.entry_payment_cond.delete(0, "end"); self.entry_payment_cond.insert(0, str(first.get("지급조건", "")))
        self.entry_warranty.delete(0, "end"); self.entry_warranty.insert(0, str(first.get("보증기간", "")))
        
        # Note (Multiline)
        note_val = str(first.get("비고", ""))
        self.entry_note.delete("1.0", "end")
        self.entry_note.insert("1.0", note_val)
        
        # Status should be reset to "견적" for new copy
        self.combo_status.set("견적")
        
        self._on_client_select(client_name)
        
        # Restore saved values again
        if first.get("결제조건"): 
            self.entry_payment_terms.delete(0, "end"); self.entry_payment_terms.insert(0, str(first.get("결제조건")))
        if first.get("지급조건"):
            self.entry_payment_cond.delete(0, "end"); self.entry_payment_cond.insert(0, str(first.get("지급조건")))
        if first.get("보증기간"):
            self.entry_warranty.delete(0, "end"); self.entry_warranty.insert(0, str(first.get("보증기간")))
            
        # Load items
        for _, row in rows.iterrows():
            self._add_item_row(row)
            
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
            "비고": self.entry_note.get("1.0", "end-1c"), # Multiline get
            "Status": self.combo_status.get(),
            "견적일": self.entry_date.get(),
            "유효기간": self.entry_valid_until.get(),
            "결제조건": self.entry_payment_terms.get(),
            "지급조건": self.entry_payment_cond.get(),
            "보증기간": self.entry_warranty.get()
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
            "note": self.entry_note.get("1.0", "end-1c") # Multiline get
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

    def _create_footer(self, parent):
        self.footer_frame = ctk.CTkFrame(parent, height=60, fg_color="transparent")
        self.footer_frame.pack(fill="x", pady=(10, 0), side="bottom")

        # 버튼 배치 순서 (우측부터): [취소] [수정] [주문 확정]
        
        # 취소 버튼
        self.btn_cancel = ctk.CTkButton(self.footer_frame, text="취소", command=self.destroy, width=80, height=40,
                      fg_color=COLORS["bg_light"], hover_color=COLORS["bg_light_hover"], text_color=COLORS["text"])
        self.btn_cancel.pack(side="right", padx=5)

        # 수정 버튼 (기존 저장 버튼 역할)
        self.btn_save = ctk.CTkButton(self.footer_frame, text="수정", command=self.save, width=120, height=40,
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"], font=FONTS["main_bold"])
        self.btn_save.pack(side="right", padx=5)

        # 주문 확정 버튼 (신규 추가)
        self.btn_confirm = ctk.CTkButton(self.footer_frame, text="주문 확정", command=self.confirm_order, width=120, height=40,
                      fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"], font=FONTS["main_bold"])
        self.btn_confirm.pack(side="right", padx=5)

    def confirm_order(self):
        messagebox.showinfo("알림", "주문 확정 기능은 준비 중입니다.", parent=self)