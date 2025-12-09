import tkinter as tk
from datetime import datetime
from tkinter import messagebox, filedialog
import customtkinter as ctk
import pandas as pd

from ui.popups.base_popup import BasePopup
from src.styles import COLORS, FONTS
# ExportManager는 추후 발주서 PDF 생성 시 사용
from managers.export_manager import ExportManager
from ui.widgets.autocomplete_entry import AutocompleteEntry

class PurchasePopup(BasePopup):
    def __init__(self, parent, data_manager, refresh_callback, mgmt_no=None, copy_mode=False):
        self.export_manager = ExportManager(data_manager)
        self.copy_mode = copy_mode
        self.copy_src_no = mgmt_no if copy_mode else None
        
        # 신규/수정 구분
        real_mgmt_no = None if copy_mode else mgmt_no
        
        self.item_widgets_map = {} # 위젯 추적용
        self.item_rows = [] # 데이터 추적용

        # BasePopup 초기화
        super().__init__(parent, data_manager, refresh_callback, popup_title="발주 등록", mgmt_no=real_mgmt_no)
        self.geometry("1350x920")

        # 신규 등록일 때 기본값 설정
        if not real_mgmt_no:
            self.entry_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
            self.combo_status.set("발주") # 기본 상태
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, filedialog
import customtkinter as ctk
import pandas as pd

from ui.popups.base_popup import BasePopup
from src.styles import COLORS, FONTS
# ExportManager는 추후 발주서 PDF 생성 시 사용
from managers.export_manager import ExportManager
from ui.widgets.autocomplete_entry import AutocompleteEntry

class PurchasePopup(BasePopup):
    def __init__(self, parent, data_manager, refresh_callback, mgmt_no=None, copy_mode=False):
        self.export_manager = ExportManager(data_manager)
        self.copy_mode = copy_mode
        self.copy_src_no = mgmt_no if copy_mode else None
        
        # 신규/수정 구분
        real_mgmt_no = None if copy_mode else mgmt_no
        
        self.item_widgets_map = {} # 위젯 추적용
        self.item_rows = [] # 데이터 추적용

        # BasePopup 초기화
        super().__init__(parent, data_manager, refresh_callback, popup_title="발주 등록", mgmt_no=real_mgmt_no)
        self.geometry("1350x920")

        # 신규 등록일 때 기본값 설정
        if not real_mgmt_no:
            self.entry_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
            # self.combo_status.set("발주") # 기본 상태 - REMOVED
            self._generate_new_id() # 신규 번호 생성
            # NEW: Set default for new status combos
            if hasattr(self, 'combo_receiving_status'):
                self.combo_receiving_status.set("미입고")
            if hasattr(self, 'combo_payment_status'):
                self.combo_payment_status.set("미지급")


        # 복사 모드일 때 데이터 로드
        if self.copy_mode and self.copy_src_no:
            self._load_copied_data()

    def _create_header(self, parent):
        # 헤더 생성 (타이틀 + 상태 + 번호)
        header_frame = self._create_common_header(parent, "발주서 작성/수정", self.mgmt_no)
        
        extra_frame = ctk.CTkFrame(parent, fg_color="transparent")
        extra_frame.pack(fill="x", padx=20, pady=(0, 10))
        
        # 입고 상태
        ctk.CTkLabel(extra_frame, text="입고:", font=FONTS["main_bold"]).pack(side="left")
        self.combo_receiving_status = ctk.CTkComboBox(extra_frame, values=["미입고", "입고중", "입고완료"], 
                                          width=90, font=FONTS["main"], state="readonly")
        self.combo_receiving_status.pack(side="left", padx=5)
        self.combo_receiving_status.set("미입고")

        # 지급 상태
        ctk.CTkLabel(extra_frame, text="지급:", font=FONTS["main_bold"]).pack(side="left", padx=(10, 0))
        self.combo_payment_status = ctk.CTkComboBox(extra_frame, values=["미지급", "지급완료"], 
                                          width=90, font=FONTS["main"], state="readonly")
        self.combo_payment_status.pack(side="left", padx=5)
        self.combo_payment_status.set("미지급")
        
        # 발주번호 표시
        ctk.CTkLabel(extra_frame, text="발주번호:", font=FONTS["main_bold"]).pack(side="left", padx=(20, 5))
        self.entry_id = ctk.CTkEntry(extra_frame, width=120) 
        self.entry_id.pack(side="left")
        
        if self.mgmt_no: self.entry_id.insert(0, self.mgmt_no)
        else: self.entry_id.insert(0, "NEW")
        self.entry_id.configure(state="readonly")

    def _setup_info_panel(self, parent):
        """
        좌측 패널 디자인 (6행 레이아웃 적용)
        """
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(1, weight=1)

        # --- 1행: 발주일, 구분 ---
        self.entry_date = self.create_grid_input(parent, 0, 0, "발주일", placeholder="YYYY-MM-DD")
        self.combo_type = self.create_grid_combo(parent, 0, 1, "구분", ["내수", "수입"], command=self.on_type_change)

        # --- 2행: 업체명 (매입처) - Full Width ---
        f_client = ctk.CTkFrame(parent, fg_color="transparent")
        f_client.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        ctk.CTkLabel(f_client, text="매입처", width=60, anchor="w", font=FONTS["main"], text_color=COLORS["text_dim"]).pack(side="left")
        
        client_names = self.dm.df_clients["업체명"].unique().tolist() if not self.dm.df_clients.empty else []
        self.entry_client = AutocompleteEntry(f_client, completevalues=client_names, command=self._on_client_select,
                                              height=28, fg_color=COLORS["entry_bg"], border_color=COLORS["entry_border"], border_width=2)
        self.entry_client.pack(side="left", fill="x", expand=True)

        # --- 3행: 통화, 세율 ---
        self.combo_currency = self.create_grid_combo(parent, 2, 0, "통화", ["KRW", "USD", "EUR", "CNY", "JPY"], command=self.on_currency_change)
        self.entry_tax_rate = self.create_grid_input(parent, 2, 1, "세율(%)")

        # --- 4행: 비고 (Multiline) - Full Width ---
        f_note = ctk.CTkFrame(parent, fg_color="transparent")
        f_note.grid(row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        ctk.CTkLabel(f_note, text="비고", width=60, anchor="w", font=FONTS["main"], text_color=COLORS["text_dim"]).pack(side="left", anchor="n", pady=5)
        self.entry_note = ctk.CTkTextbox(f_note, height=80, fg_color=COLORS["entry_bg"], border_color=COLORS["entry_border"], border_width=2)
        self.entry_note.pack(side="left", fill="x", expand=True)

        # --- 5행: 견적서 등록 (File Upload) - Full Width ---
        f_upload = ctk.CTkFrame(parent, fg_color="transparent")
        f_upload.grid(row=4, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        ctk.CTkLabel(f_upload, text="견적서", width=60, anchor="w", font=FONTS["main"], text_color=COLORS["text_dim"]).pack(side="left")
        
        self.entry_quote_file = ctk.CTkEntry(f_upload, placeholder_text="등록된 견적서 파일이 없습니다", 
                                             height=28, fg_color=COLORS["bg_dark"], state="readonly")
        self.entry_quote_file.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        ctk.CTkButton(f_upload, text="파일 선택", command=self.upload_quote_file, width=80, height=28,
                      fg_color=COLORS["bg_medium"], hover_color=COLORS["bg_light"], 
                      text_color=COLORS["text"]).pack(side="right")

        # --- 6행: 문서 생성 버튼들 (발주서, 기안서) - Full Width ---
        f_docs = ctk.CTkFrame(parent, fg_color="transparent")
        f_docs.grid(row=5, column=0, columnspan=2, sticky="ew", padx=5, pady=(20, 5))
        
        # 버튼 균등 배치를 위한 Grid 설정
        f_docs.grid_columnconfigure(0, weight=1)
        f_docs.grid_columnconfigure(1, weight=1)

        ctk.CTkButton(f_docs, text="발주서 생성", command=self.generate_po, height=35,
                      fg_color=COLORS["bg_light"], hover_color=COLORS["primary_hover"], 
                      text_color=COLORS["text"], font=FONTS["main_bold"]).grid(row=0, column=0, padx=(0, 5), sticky="ew")

        ctk.CTkButton(f_docs, text="기안서 생성", command=self.generate_draft, height=35,
                      fg_color=COLORS["bg_light"], hover_color=COLORS["primary_hover"], 
                      text_color=COLORS["text"], font=FONTS["main_bold"]).grid(row=0, column=1, padx=(5, 0), sticky="ew")


    def _setup_items_panel(self, parent):
        # 타이틀 & 추가 버튼
        title_frame = ctk.CTkFrame(parent, fg_color="transparent")
        title_frame.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(title_frame, text="발주 품목 리스트", font=FONTS["header"]).pack(side="left")
        
        ctk.CTkButton(title_frame, text="+ 품목 추가", command=self._add_item_row, width=100, height=30,
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"]).pack(side="right")
        
        # 헤더 (BasePopup의 COL_CONFIG 사용)
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

    def _setup_buttons(self, parent):
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent", height=50)
        btn_frame.pack(fill="x", side="bottom", padx=20, pady=20)
        
        ctk.CTkButton(btn_frame, text="저장", command=self.save, 
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
                      width=100, height=35, font=FONTS["main_bold"]).pack(side="right", padx=5)
                      
        ctk.CTkButton(btn_frame, text="취소", command=self.destroy,
                      fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
                      width=100, height=35, font=FONTS["main_bold"]).pack(side="right", padx=5)

    def on_type_change(self, type_val): self._calculate_totals()

    def on_currency_change(self, currency):
        if currency == "KRW":
            self.entry_tax_rate.delete(0, "end")
            self.entry_tax_rate.insert(0, "10")
            self.combo_type.set("내수")
        else:
            self.entry_tax_rate.delete(0, "end")
            self.entry_tax_rate.insert(0, "0")
            self.combo_type.set("수입")
        self._calculate_totals()
        
        # 모든 행 재계산
        for row in self.item_rows: self.calculate_row(row)

    # --- Dummy Handlers for UI ---
    def upload_quote_file(self):
        # 디자인만 구현 (기능 추후)
        filename = filedialog.askopenfilename(title="견적서 파일 선택", filetypes=[("PDF/Excel", "*.pdf *.xlsx *.xls"), ("All Files", "*.*")])
        if filename:
            self.entry_quote_file.configure(state="normal")
            self.entry_quote_file.delete(0, "end")
            self.entry_quote_file.insert(0, filename)
            self.entry_quote_file.configure(state="readonly")

    def generate_po(self):
        messagebox.showinfo("알림", "발주서 PDF 생성 기능은 추후 구현됩니다.")

    def generate_draft(self):
        messagebox.showinfo("알림", "기안서 생성 기능은 추후 구현됩니다.")

    def _load_data(self):
        if not self.mgmt_no: return
        
        df = self.dm.df_purchase
        if df.empty: return
        
        rows = df[df["관리번호"] == self.mgmt_no]
        if rows.empty:
            messagebox.showerror("오류", "데이터를 찾을 수 없습니다.", parent=self)
            self.destroy()
            return
            
        data = rows.iloc[0]
        
        self.entry_date.insert(0, data.get("발주일", ""))
        self.combo_type.set(data.get("구분", "내수"))
        self.entry_client.set_value(data.get("업체명", ""))
        self.combo_currency.set(data.get("통화", "KRW"))
        self.entry_tax_rate.delete(0, "end")
        self.entry_tax_rate.insert(0, str(data.get("세율(%)", "10")))
        self.entry_note.insert("1.0", str(data.get("비고", "")))
        
        # 상태 로드 (기존 Status 호환성 고려)
        status = data.get("Status", "")
        recv_status = data.get("입고상태", "미입고")
        pay_status = data.get("지급상태", "미지급")
        
        # 만약 기존 Status가 있고 새 컬럼이 비어있다면 매핑 시도 (간단히)
        if status and (pd.isna(recv_status) or recv_status == "nan"):
             if status == "완료": recv_status = "입고완료"
             elif status == "입고중": recv_status = "입고중"
             else: recv_status = "미입고"
             
        self.combo_receiving_status.set(recv_status)
        self.combo_payment_status.set(pay_status)
        
        quote_path = data.get("견적서경로", "")
        if quote_path and str(quote_path) != "nan":
            self.entry_quote_file.configure(state="normal")
            self.entry_quote_file.insert(0, quote_path)
            self.entry_quote_file.configure(state="readonly")
            
        for _, row in rows.iterrows():
            item_data = {
                "품목명": row.get("품목명", ""),
                "모델명": row.get("모델명", ""),
                "Description": row.get("Description", ""),
                "수량": row.get("수량", 0),
                "단가": row.get("단가", 0),
                "공급가액": row.get("공급가액", 0),
                "세액": row.get("세액", 0),
                "합계금액": row.get("합계금액", 0)
            }
            self._add_item_row(item_data)
            
        self._calculate_totals()

    def _load_copied_data(self):
        if not self.copy_src_no: return
        
        df = self.dm.df_purchase
        if df.empty: return
        
        rows = df[df["관리번호"] == self.copy_src_no]
        if rows.empty: return
            
        data = rows.iloc[0]
        
        self.combo_type.set(data.get("구분", "내수"))
        self.entry_client.set_value(data.get("업체명", ""))
        self.combo_currency.set(data.get("통화", "KRW"))
        self.entry_tax_rate.delete(0, "end")
        self.entry_tax_rate.insert(0, str(data.get("세율(%)", "10")))
        self.entry_note.insert("1.0", str(data.get("비고", "")))
        
        for _, row in rows.iterrows():
            item_data = {
                "품목명": row.get("품목명", ""),
                "모델명": row.get("모델명", ""),
                "Description": row.get("Description", ""),
                "수량": row.get("수량", 0),
                "단가": row.get("단가", 0),
                "공급가액": row.get("공급가액", 0),
                "세액": row.get("세액", 0),
                "합계금액": row.get("합계금액", 0)
            }
            self._add_item_row(item_data)
            
        self._calculate_totals()

    def save(self):
        mgmt_no = self.entry_id.get()
        client = self.entry_client.get()
        
        if not client:
            messagebox.showwarning("경고", "매입처를 선택해주세요.", parent=self)
            return
            
        common_data = {
            "관리번호": mgmt_no,
            "발주일": self.entry_date.get(),
            "구분": self.combo_type.get(),
            "업체명": client,
            "통화": self.combo_currency.get(),
            "세율(%)": self.entry_tax_rate.get(),
            "비고": self.entry_note.get("1.0", "end-1c").strip(),
            "입고상태": self.combo_receiving_status.get(),
            "지급상태": self.combo_payment_status.get(),
            "견적서경로": self.entry_quote_file.get()
        }
        
        rows_to_save = []
        if not self.item_rows:
            messagebox.showwarning("경고", "품목을 하나 이상 추가해주세요.", parent=self)
            return

        for row_widgets in self.item_rows:
            try:
                qty = float(row_widgets["qty"].get().replace(",", "") or 0)
                price = float(row_widgets["price"].get().replace(",", "") or 0)
                supply = float(row_widgets["supply"].get().replace(",", "") or 0)
                tax = float(row_widgets["tax"].get().replace(",", "") or 0)
                total = float(row_widgets["total"].get().replace(",", "") or 0)
            except:
                qty=0; price=0; supply=0; tax=0; total=0
            
            row_data = common_data.copy()
            row_data.update({
                "품목명": row_widgets["item"].get(),
                "모델명": row_widgets["model"].get(),
                "Description": row_widgets["desc"].get(),
                "수량": qty,
                "단가": price,
                "공급가액": supply,
                "세액": tax,
                "합계금액": total
            })
            rows_to_save.append(row_data)
            
        if self.mgmt_no and not self.copy_mode:
            success, msg = self.dm.update_purchase(mgmt_no, rows_to_save)
        else:
            success, msg = self.dm.add_purchase(rows_to_save)
            
        if success:
            messagebox.showinfo("알림", "저장되었습니다.", parent=self)
            if self.refresh_callback: self.refresh_callback()
            self.destroy()
        else:
            messagebox.showerror("오류", f"저장 실패: {msg}", parent=self)

    def delete(self):
        if messagebox.askyesno("삭제 확인", f"정말 이 발주({self.mgmt_no})를 삭제하시겠습니까?", parent=self):
            success, msg = self.dm.delete_purchase(self.mgmt_no)
            if success:
                messagebox.showinfo("알림", "삭제되었습니다.", parent=self)
                if self.refresh_callback: self.refresh_callback()
                self.destroy()
            else:
                messagebox.showerror("오류", f"삭제 실패: {msg}", parent=self)

    def _generate_new_id(self):
        new_id = self.dm.get_next_purchase_id()
        
        if hasattr(self, 'entry_id'):
            self.entry_id.configure(state="normal")
            self.entry_id.delete(0, "end")
            self.entry_id.insert(0, new_id)
            self.entry_id.configure(state="readonly")