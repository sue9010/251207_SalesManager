import os
import tkinter as tk
from tkinter import messagebox, filedialog
import shutil
import datetime

import customtkinter as ctk
import pandas as pd

from ui.popups.base_popup import BasePopup
from src.styles import COLORS, FONTS
from src.config import Config

class CompletePopup(BasePopup):
    # 컬럼 설정 정의 (헤더명, 너비)
    COL_SPECS = {
        "items": [
            ("모델명", 150), ("Description", 200), ("수량", 60), ("단가", 100), 
            ("공급가액", 100), ("세액", 80), ("합계금액", 100), ("시리얼 번호", 120)
        ],
        "payment": [
            ("일시", 150), ("구분", 80), ("입금액", 100), ("통화", 60), 
            ("작업자", 80), ("세금계산서번호", 120), ("발행일", 100), ("외화증빙", 80), ("송금상세", 80)
        ],
        "delivery": [
            ("처리일시", 150), ("출고일", 100), ("품목명", 200), ("출고수량", 80), 
            ("송장번호", 120), ("운송장파일", 80), ("수출신고필증", 80), ("CI", 50), ("PL", 50), ("비고", 150)
        ],
        "tax_invoice": [
            ("발행일", 120), ("금액", 100), ("세금계산서번호", 150), ("비고", 200)
        ]
    }

    def __init__(self, parent, data_manager, refresh_callback, mgmt_no):
        # 탭 뷰 참조 변수 초기화
        self.tabview = None
        super().__init__(parent, data_manager, refresh_callback, popup_title="완료 주문 상세", mgmt_no=mgmt_no)
        
    def _create_widgets(self):
        self.configure(fg_color=COLORS["bg_dark"])
        
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 1. 헤더 섹션
        self._create_header(self.main_container)
        
        # 2. 요약 대시보드
        self._create_summary_cards(self.main_container)
        
        # 3. 탭 뷰 (품목 / 입금 이력 / 납품 이력)
        self._create_tabs(self.main_container)
        
        # 4. 하단 섹션 (비고, 요청사항, 파일)
        self._create_footer(self.main_container)
        
        # 5. 닫기 버튼
        self._create_action_buttons_custom(self.main_container)

        self.geometry("1200x920")

    def _create_header(self, parent):
        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        
        top_row = ctk.CTkFrame(header_frame, fg_color="transparent")
        top_row.pack(fill="x", anchor="w")
        
        self.lbl_id = ctk.CTkLabel(top_row, text="MGMT-000000", font=FONTS["main"], text_color=COLORS["text_dim"])
        self.lbl_id.pack(side="left")
        
        self.status_badge = ctk.CTkLabel(top_row, text="Status", font=FONTS["small"], 
                                       fg_color=COLORS["primary"], text_color="white", corner_radius=10, width=80)
        self.status_badge.pack(side="left", padx=10)
        
        self.lbl_project = ctk.CTkLabel(header_frame, text="Project Name", font=FONTS["title"], anchor="w")
        self.lbl_project.pack(fill="x", pady=(5, 0))
        
        self.lbl_client = ctk.CTkLabel(header_frame, text="Client Name", font=FONTS["header"], text_color=COLORS["text_dim"], anchor="w")
        self.lbl_client.pack(fill="x")

    def _create_summary_cards(self, parent):
        card_frame = ctk.CTkFrame(parent, fg_color="transparent")
        card_frame.pack(fill="x", pady=(0, 20))
        
        card_frame.columnconfigure(0, weight=1)
        card_frame.columnconfigure(1, weight=1)
        card_frame.columnconfigure(2, weight=1)
        card_frame.columnconfigure(3, weight=1)
        
        def create_card(col, title, value_id, color=COLORS["bg_medium"], title_color=COLORS["text_dim"], value_color=COLORS["text"]):
            card = ctk.CTkFrame(card_frame, fg_color=color, corner_radius=10)
            card.grid(row=0, column=col, sticky="ew", padx=5)
            
            ctk.CTkLabel(card, text=title, font=FONTS["small"], text_color=title_color).pack(anchor="w", padx=15, pady=(10, 0))
            lbl_val = ctk.CTkLabel(card, text="-", font=FONTS["header"], text_color=value_color)
            lbl_val.pack(anchor="w", padx=15, pady=(0, 10))
            setattr(self, value_id, lbl_val)
            
        create_card(0, "총 합계금액", "lbl_amt_total", color=COLORS["bg_light"], value_color=COLORS["primary"])
        create_card(1, "실 입금액", "lbl_amt_paid", color=COLORS["bg_light"], value_color=COLORS["success"])
        create_card(2, "견적일 / 수주일", "lbl_date_qs")
        create_card(3, "출고일 / 입금완료일", "lbl_date_dp")

    def _create_tabs(self, parent):
        self.tabview = ctk.CTkTabview(parent, height=300)
        self.tabview.pack(fill="both", expand=True, pady=(0, 20))
        
        self.tabview.add("품목 리스트")
        self.tabview.add("입금 이력")
        self.tabview.add("납품 이력")
        
        self._setup_items_tab(self.tabview.tab("품목 리스트"))
        self._setup_payment_history_tab(self.tabview.tab("입금 이력"))
        self._setup_delivery_history_tab(self.tabview.tab("납품 이력"))
        
        self.tabview.add("세금계산서 이력")
        self._setup_tax_invoice_tab(self.tabview.tab("세금계산서 이력"))

    def _setup_items_tab(self, parent):
        header_frame = ctk.CTkFrame(parent, height=30, fg_color=COLORS["bg_light"])
        header_frame.pack(fill="x", padx=5, pady=5)
        
        for h, w in self.COL_SPECS["items"]:
            ctk.CTkLabel(header_frame, text=h, width=w, font=FONTS["main_bold"]).pack(side="left", padx=2)
            
        self.scroll_items = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        self.scroll_items.pack(fill="both", expand=True, padx=5, pady=5)

    def _setup_payment_history_tab(self, parent):
        header_frame = ctk.CTkFrame(parent, height=30, fg_color=COLORS["bg_light"])
        header_frame.pack(fill="x", padx=5, pady=5)
        
        for h, w in self.COL_SPECS["payment"]:
            ctk.CTkLabel(header_frame, text=h, width=w, font=FONTS["main_bold"]).pack(side="left", padx=2)
            
        self.scroll_payment = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        self.scroll_payment.pack(fill="both", expand=True, padx=5, pady=5)

    def _setup_delivery_history_tab(self, parent):
        header_frame = ctk.CTkFrame(parent, height=30, fg_color=COLORS["bg_light"])
        header_frame.pack(fill="x", padx=5, pady=5)
        
        for h, w in self.COL_SPECS["delivery"]:
            ctk.CTkLabel(header_frame, text=h, width=w, font=FONTS["main_bold"]).pack(side="left", padx=2)
            
        self.scroll_delivery = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        self.scroll_delivery.pack(fill="both", expand=True, padx=5, pady=5)

    def _create_footer(self, parent):
        footer_frame = ctk.CTkFrame(parent, fg_color="transparent")
        footer_frame.pack(fill="x", pady=(0, 10))
        
        footer_frame.columnconfigure(0, weight=3) 
        footer_frame.columnconfigure(1, weight=2) 
        
        left_col = ctk.CTkFrame(footer_frame, fg_color=COLORS["bg_medium"], corner_radius=10)
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        ctk.CTkLabel(left_col, text="비고", font=FONTS["main_bold"]).pack(anchor="w", padx=15, pady=(15, 5))
        self.entry_note = ctk.CTkEntry(left_col, fg_color=COLORS["bg_dark"], border_width=0, height=35)
        self.entry_note.pack(fill="x", padx=15, pady=(0, 10))
        
        ctk.CTkLabel(left_col, text="주문요청사항", font=FONTS["main_bold"]).pack(anchor="w", padx=15, pady=(5, 5))
        self.entry_req = ctk.CTkEntry(left_col, fg_color=COLORS["bg_dark"], border_width=0, height=35)
        self.entry_req.pack(fill="x", padx=15, pady=(0, 15))
        
        right_col = ctk.CTkFrame(footer_frame, fg_color=COLORS["bg_medium"], corner_radius=10)
        right_col.grid(row=0, column=1, sticky="nsew")
        self.configure(fg_color=COLORS["bg_dark"])
        
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 1. 헤더 섹션
        self._create_header(self.main_container)
        
        # 2. 요약 대시보드
        self._create_summary_cards(self.main_container)
        
        # 3. 탭 뷰 (품목 / 입금 이력 / 납품 이력)
        self._create_tabs(self.main_container)
        
        # 4. 하단 섹션 (비고, 요청사항, 파일)
        self._create_footer(self.main_container)
        
        # 5. 닫기 버튼
        self._create_action_buttons_custom(self.main_container)

        self.geometry("1200x920")

    def _create_header(self, parent):
        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        
        top_row = ctk.CTkFrame(header_frame, fg_color="transparent")
        top_row.pack(fill="x", anchor="w")
        
        self.lbl_id = ctk.CTkLabel(top_row, text="MGMT-000000", font=FONTS["main"], text_color=COLORS["text_dim"])
        self.lbl_id.pack(side="left")
        
        self.status_badge = ctk.CTkLabel(top_row, text="Status", font=FONTS["small"], 
                                       fg_color=COLORS["primary"], text_color="white", corner_radius=10, width=80)
        self.status_badge.pack(side="left", padx=10)
        
        self.lbl_project = ctk.CTkLabel(header_frame, text="Project Name", font=FONTS["title"], anchor="w")
        self.lbl_project.pack(fill="x", pady=(5, 0))
        
        self.lbl_client = ctk.CTkLabel(header_frame, text="Client Name", font=FONTS["header"], text_color=COLORS["text_dim"], anchor="w")
        self.lbl_client.pack(fill="x")

    def _create_summary_cards(self, parent):
        card_frame = ctk.CTkFrame(parent, fg_color="transparent")
        card_frame.pack(fill="x", pady=(0, 20))
        
        card_frame.columnconfigure(0, weight=1)
        card_frame.columnconfigure(1, weight=1)
        card_frame.columnconfigure(2, weight=1)
        card_frame.columnconfigure(3, weight=1)
        
        def create_card(col, title, value_id, color=COLORS["bg_medium"], title_color=COLORS["text_dim"], value_color=COLORS["text"]):
            card = ctk.CTkFrame(card_frame, fg_color=color, corner_radius=10)
            card.grid(row=0, column=col, sticky="ew", padx=5)
            
            ctk.CTkLabel(card, text=title, font=FONTS["small"], text_color=title_color).pack(anchor="w", padx=15, pady=(10, 0))
            lbl_val = ctk.CTkLabel(card, text="-", font=FONTS["header"], text_color=value_color)
            lbl_val.pack(anchor="w", padx=15, pady=(0, 10))
            setattr(self, value_id, lbl_val)
            
        create_card(0, "총 합계금액", "lbl_amt_total", color=COLORS["bg_light"], value_color=COLORS["primary"])
        create_card(1, "실 입금액", "lbl_amt_paid", color=COLORS["bg_light"], value_color=COLORS["success"])
        create_card(2, "견적일 / 수주일", "lbl_date_qs")
        create_card(3, "출고일 / 입금완료일", "lbl_date_dp")

    def _create_tabs(self, parent):
        self.tabview = ctk.CTkTabview(parent, height=300)
        self.tabview.pack(fill="both", expand=True, pady=(0, 20))
        
        self.tabview.add("품목 리스트")
        self.tabview.add("입금 이력")
        self.tabview.add("납품 이력")
        self.tabview.add("세금계산서 이력") # New tab
        
        self._setup_items_tab(self.tabview.tab("품목 리스트"))
        self._setup_payment_history_tab(self.tabview.tab("입금 이력"))
        self._setup_delivery_history_tab(self.tabview.tab("납품 이력"))
        self._setup_tax_invoice_tab(self.tabview.tab("세금계산서 이력")) # New setup call

    def _setup_items_tab(self, parent):
        header_frame = ctk.CTkFrame(parent, height=30, fg_color=COLORS["bg_light"])
        header_frame.pack(fill="x", padx=5, pady=5)
        
        for h, w in self.COL_SPECS["items"]:
            ctk.CTkLabel(header_frame, text=h, width=w, font=FONTS["main_bold"]).pack(side="left", padx=2)
            
        self.scroll_items = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        self.scroll_items.pack(fill="both", expand=True, padx=5, pady=5)

    def _setup_payment_history_tab(self, parent):
        header_frame = ctk.CTkFrame(parent, height=30, fg_color=COLORS["bg_light"])
        header_frame.pack(fill="x", padx=5, pady=5)
        
        for h, w in self.COL_SPECS["payment"]:
            ctk.CTkLabel(header_frame, text=h, width=w, font=FONTS["main_bold"]).pack(side="left", padx=2)
            
        self.scroll_payment = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        self.scroll_payment.pack(fill="both", expand=True, padx=5, pady=5)

    def _setup_delivery_history_tab(self, parent):
        header_frame = ctk.CTkFrame(parent, height=30, fg_color=COLORS["bg_light"])
        header_frame.pack(fill="x", padx=5, pady=5)
        
        for h, w in self.COL_SPECS["delivery"]:
            ctk.CTkLabel(header_frame, text=h, width=w, font=FONTS["main_bold"]).pack(side="left", padx=2)
            
        self.scroll_delivery = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        self.scroll_delivery.pack(fill="both", expand=True, padx=5, pady=5)

    def _create_footer(self, parent):
        footer_frame = ctk.CTkFrame(parent, fg_color="transparent")
        footer_frame.pack(fill="x", pady=(0, 10))
        
        footer_frame.columnconfigure(0, weight=3) 
        footer_frame.columnconfigure(1, weight=2) 
        
        left_col = ctk.CTkFrame(footer_frame, fg_color=COLORS["bg_medium"], corner_radius=10)
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        
        ctk.CTkLabel(left_col, text="비고", font=FONTS["main_bold"]).pack(anchor="w", padx=15, pady=(15, 5))
        self.entry_note = ctk.CTkEntry(left_col, fg_color=COLORS["bg_dark"], border_width=0, height=35)
        self.entry_note.pack(fill="x", padx=15, pady=(0, 10))
        
        ctk.CTkLabel(left_col, text="주문요청사항", font=FONTS["main_bold"]).pack(anchor="w", padx=15, pady=(5, 5))
        self.entry_req = ctk.CTkEntry(left_col, fg_color=COLORS["bg_dark"], border_width=0, height=35)
        self.entry_req.pack(fill="x", padx=15, pady=(0, 15))
        
        right_col = ctk.CTkFrame(footer_frame, fg_color=COLORS["bg_medium"], corner_radius=10)
        right_col.grid(row=0, column=1, sticky="nsew")
        
        ctk.CTkLabel(right_col, text="관련 문서", font=FONTS["main_bold"]).pack(anchor="w", padx=15, pady=15)
        self.files_scroll = ctk.CTkScrollableFrame(right_col, fg_color="transparent", height=100)
        self.files_scroll.pack(fill="both", expand=True, padx=5, pady=(0, 10))

    def _create_action_buttons_custom(self, parent):
        btn_frame = ctk.CTkFrame(parent, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(10, 0))
        
        ctk.CTkButton(btn_frame, text="닫기", command=self.destroy, width=120, height=40,
                      fg_color=COLORS["bg_light"], hover_color=COLORS["bg_light_hover"], 
                      text_color=COLORS["text"]).pack(side="right")

    def _setup_tax_invoice_tab(self, parent):
        header_frame = ctk.CTkFrame(parent, height=30, fg_color=COLORS["bg_light"])
        header_frame.pack(fill="x", padx=5, pady=5)
        
        for h, w in self.COL_SPECS["tax_invoice"]:
            ctk.CTkLabel(header_frame, text=h, width=w, font=FONTS["main_bold"]).pack(side="left", padx=2)
            
        self.scroll_tax_invoice = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        self.scroll_tax_invoice.pack(fill="both", expand=True, padx=5, pady=5)

    def _load_data(self):
        df = self.dm.df_data
        rows = df[df["관리번호"].astype(str) == str(self.mgmt_no)]
        if rows.empty: return

        # Delivery 시트 데이터 로드
        delivery_df = self.dm.df_delivery
        current_deliveries = pd.DataFrame()
        if not delivery_df.empty:
            current_deliveries = delivery_df[delivery_df["관리번호"].astype(str) == str(self.mgmt_no)]

        first = rows.iloc[0]

        # 헤더 & 배지
        self.lbl_id.configure(text=f"No. {first['관리번호']}")
        self.lbl_project.configure(text=first.get("프로젝트명", ""))
        self.lbl_client.configure(text=first.get("업체명", ""))
        
        status = str(first.get("Status", ""))
        self.status_badge.configure(text=status)
        if "완료" in status: self.status_badge.configure(fg_color=COLORS["success"])
        elif "취소" in status: self.status_badge.configure(fg_color=COLORS["danger"])
        else: self.status_badge.configure(fg_color=COLORS["primary"])

        # 통화 정보 확인 및 포맷팅 적용
        currency = str(first.get("통화", "KRW")).upper()
        
        try: total = pd.to_numeric(rows["합계금액"], errors='coerce').sum()
        except: total = 0
        try: paid = pd.to_numeric(rows["기수금액"], errors='coerce').sum()
        except: paid = 0
        
        self.lbl_amt_total.configure(text=f"{currency} {total:,.0f}")
        self.lbl_amt_paid.configure(text=f"{currency} {paid:,.0f}")
        
        q_date = str(first.get("견적일", "-"))
        s_date = str(first.get("수주일", "-"))
        d_date = str(first.get("출고일", "-"))
        p_date = str(first.get("입금완료일", "-"))
        
        self.lbl_date_qs.configure(text=f"{q_date} / {s_date}")
        self.lbl_date_dp.configure(text=f"{d_date} / {p_date}")

        # 텍스트 필드
        self.entry_note.configure(state="normal")
        self.entry_note.delete(0, "end")
        self.entry_note.insert(0, str(first.get("비고", "")))
        self.entry_note.configure(state="readonly")
        
        self.entry_req.configure(state="normal")
        self.entry_req.delete(0, "end")
        self.entry_req.insert(0, str(first.get("주문요청사항", "")))
        self.entry_req.configure(state="readonly")

        # 2. 품목 리스트 로드
        for widget in self.scroll_items.winfo_children(): widget.destroy()
        for _, row in rows.iterrows():
            item_name = str(row.get("품목명", "")).strip()
            
            # Delivery 시트에서 해당 품목의 시리얼 번호 찾기
            serial = "-"
            if not current_deliveries.empty:
                target_del = current_deliveries[
                    (current_deliveries["품목명"].astype(str).str.strip() == item_name) & 
                    (current_deliveries["시리얼번호"].notna()) & 
                    (current_deliveries["시리얼번호"].astype(str) != "-") &
                    (current_deliveries["시리얼번호"].astype(str) != "")
                ]
                
                if not target_del.empty:
                    serials = sorted(list(set(target_del["시리얼번호"].astype(str).tolist())))
                    serial = ", ".join(serials)

            item_data = row.to_dict()
            item_data["시리얼번호"] = serial
            
            self._add_item_row(item_data)

        # 3. 입금 이력 로드
        for widget in self.scroll_payment.winfo_children(): widget.destroy()
        if not self.dm.df_payment.empty:
            pay_rows = self.dm.df_payment[self.dm.df_payment["관리번호"].astype(str) == str(self.mgmt_no)]
            if not pay_rows.empty:
                pay_rows = pay_rows.sort_values(by="일시", ascending=False)
                for _, p_row in pay_rows.iterrows():
                    self._add_payment_row(p_row)
            else:
                ctk.CTkLabel(self.scroll_payment, text="입금 이력이 없습니다.", text_color=COLORS["text_dim"]).pack(pady=20)
        else:
            ctk.CTkLabel(self.scroll_payment, text="입금 이력이 없습니다.", text_color=COLORS["text_dim"]).pack(pady=20)

        # 4. 납품 이력 로드
        for widget in self.scroll_delivery.winfo_children(): widget.destroy()
        if not self.dm.df_delivery.empty:
            del_rows = self.dm.df_delivery[self.dm.df_delivery["관리번호"].astype(str) == str(self.mgmt_no)]
            if not del_rows.empty:
                del_rows = del_rows.sort_values(by="일시", ascending=False)
                for _, d_row in del_rows.iterrows():
                    self._add_delivery_row(d_row)
            else:
                ctk.CTkLabel(self.scroll_delivery, text="납품 이력이 없습니다.", text_color=COLORS["text_dim"]).pack(pady=20)
        else:
            ctk.CTkLabel(self.scroll_delivery, text="납품 이력이 없습니다.", text_color=COLORS["text_dim"]).pack(pady=20)

        # 5. 세금계산서 이력 로드
        for widget in self.scroll_tax_invoice.winfo_children(): widget.destroy()
        if hasattr(self.dm, 'df_tax_invoice') and not self.dm.df_tax_invoice.empty:
            tax_rows = self.dm.df_tax_invoice[self.dm.df_tax_invoice["관리번호"].astype(str) == str(self.mgmt_no)]
            if not tax_rows.empty:
                tax_rows = tax_rows.sort_values(by="발행일", ascending=False)
                for _, t_row in tax_rows.iterrows():
                    self._add_tax_invoice_row(t_row)
            else:
                ctk.CTkLabel(self.scroll_tax_invoice, text="세금계산서 발행 이력이 없습니다.", text_color=COLORS["text_dim"]).pack(pady=20)
        else:
            ctk.CTkLabel(self.scroll_tax_invoice, text="세금계산서 발행 이력이 없습니다.", text_color=COLORS["text_dim"]).pack(pady=20)

        # 6. 파일 리스트 로드 (주문서, 사업자등록증만)
        for widget in self.files_scroll.winfo_children(): widget.destroy()
        has_files = False
        
        # 6-1. Data 시트의 주문서
        if self._add_file_row("주문서(발주서)", first.get("발주서경로")): has_files = True
        
        # 6-2. 사업자등록증
        client_name = str(first.get("업체명", ""))
        client_row = self.dm.df_clients[self.dm.df_clients["업체명"] == client_name]
        if not client_row.empty:
            if self._add_file_row("사업자등록증", client_row.iloc[0].get("사업자등록증경로")): has_files = True

        # 6-3. 견적서, 출고요청서, PI (Data 시트)
        if self._add_file_row("견적서", first.get("견적서경로")): has_files = True
        if self._add_file_row("출고요청서", first.get("출고요청서경로")): has_files = True
        if self._add_file_row("Proforma Invoice", first.get("PI경로")): has_files = True

        # 6-4. CI, PL (Delivery 시트 - 최신순)
        if not current_deliveries.empty:
            # Sort by date desc
            sorted_del = current_deliveries.sort_values(by="일시", ascending=False)
            # Find first valid CI/PL
            ci_path = None
            pl_path = None
            for _, d_row in sorted_del.iterrows():
                if not ci_path and d_row.get("CI경로"): ci_path = d_row.get("CI경로")
                if not pl_path and d_row.get("PL경로"): pl_path = d_row.get("PL경로")
                if ci_path and pl_path: break
            
            if self._add_file_row("Commercial Invoice", ci_path): has_files = True
            if self._add_file_row("Packing List", pl_path): has_files = True
                
        if not has_files:
            ctk.CTkLabel(self.files_scroll, text="첨부 파일 없음", font=FONTS["small"], text_color=COLORS["text_dim"]).pack(pady=20)

    def _add_tax_invoice_row(self, row):
        row_frame = ctk.CTkFrame(self.scroll_tax_invoice, fg_color="transparent", height=30)
        row_frame.pack(fill="x", pady=2)
        row_frame.pack_propagate(False)
        
        widths = [w for _, w in self.COL_SPECS["tax_invoice"]]
        
        self._create_cell(row_frame, row.get("발행일", ""), widths[0], "center")
        self._create_cell(row_frame, row.get("금액", 0), widths[1], "right", True)
        self._create_cell(row_frame, row.get("세금계산서번호", ""), widths[2], "center")
        self._create_cell(row_frame, row.get("비고", ""), widths[3])

    # 행 추가 헬퍼 메서드들
    def _create_cell(self, parent, val, width, justify="left", is_num=False, is_bold=False):
        if is_num:
            try: val = f"{float(val):,.0f}"
            except: val = "0"
        
        font = FONTS["main_bold"] if is_bold else FONTS["main"]
        lbl = ctk.CTkLabel(parent, text=str(val), width=width, font=font, 
                           anchor="e" if justify=="right" else "w" if justify=="left" else "center")
        lbl.pack(side="left", padx=2)

    def _create_file_cell(self, parent, path, width, sheet_type=None, row_idx=None, col_name=None, extra_data=None):
        frame = ctk.CTkFrame(parent, width=width, fg_color="transparent")
        frame.pack(side="left", padx=2, fill="y")
        frame.pack_propagate(False)
        
        path = str(path).strip()
        if path and path.lower() != "nan" and path != "-":
            btn = ctk.CTkButton(frame, text="보기", width=50, height=24, 
                                fg_color=COLORS["primary"], font=FONTS["small"],
                                command=lambda p=path: self.open_file(p))
            btn.pack(expand=True)
        else:
            if sheet_type and row_idx is not None and col_name:
                btn = ctk.CTkButton(frame, text="업로드", width=50, height=24, 
                                    fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"], font=FONTS["small"],
                                    command=lambda: self.perform_upload(sheet_type, row_idx, col_name, extra_data))
                btn.pack(expand=True)
            else:
                ctk.CTkLabel(frame, text="-", font=FONTS["small"], text_color=COLORS["text_dim"]).pack(expand=True)

    def _add_item_row(self, item_data):
        row_frame = ctk.CTkFrame(self.scroll_items, fg_color="transparent", height=30)
        row_frame.pack(fill="x", pady=2)
        
        widths = [w for _, w in self.COL_SPECS["items"]]
        
        self._create_cell(row_frame, item_data.get("모델명", ""), widths[0], "center")
        self._create_cell(row_frame, item_data.get("Description", ""), widths[1], "center")
        self._create_cell(row_frame, item_data.get("수량", 0), widths[2], "center", True)
        self._create_cell(row_frame, item_data.get("단가", 0), widths[3], "right", True)
        self._create_cell(row_frame, item_data.get("공급가액", 0), widths[4], "right", True)
        self._create_cell(row_frame, item_data.get("세액", 0), widths[5], "right", True)
        self._create_cell(row_frame, item_data.get("합계금액", 0), widths[6], "right", True)

        serial = str(item_data.get("시리얼번호", "-"))
        ctk.CTkLabel(row_frame, text=serial, width=widths[7], font=FONTS["main"], anchor="center", text_color=COLORS["primary"]).pack(side="left", padx=2)

    def _add_payment_row(self, row):
        row_frame = ctk.CTkFrame(self.scroll_payment, fg_color="transparent", height=30)
        row_frame.pack(fill="x", pady=2)
        row_frame.pack_propagate(False)
        
        widths = [w for _, w in self.COL_SPECS["payment"]]
        
        self._create_cell(row_frame, row.get("일시", ""), widths[0], "center")
        self._create_cell(row_frame, row.get("구분", ""), widths[1], "center")
        self._create_cell(row_frame, row.get("입금액", 0), widths[2], "right", True)
        self._create_cell(row_frame, row.get("통화", ""), widths[3], "center")
        self._create_cell(row_frame, row.get("작업자", ""), widths[4], "center")
        self._create_cell(row_frame, row.get("세금계산서번호", ""), widths[5], "center")
        self._create_cell(row_frame, row.get("세금계산서발행일", ""), widths[6], "center")
        
        # extra_data 생성 (파일명용)
        # Payment: 업체명_관리번호_입금액
        try: amt = int(float(row.get("입금액", 0)))
        except: amt = 0
        extra_data = {
            "client": self.lbl_client.cget("text"), # 현재 팝업의 업체명
            "mgmt_no": self.mgmt_no,
            "amount": amt,
            "date": row.get("일시", datetime.datetime.now().strftime("%Y-%m-%d"))
        }

        self._create_file_cell(row_frame, row.get("외화입금증빙경로", ""), widths[7], "payment", row.name, "외화입금증빙경로", extra_data)
        self._create_file_cell(row_frame, row.get("송금상세경로", ""), widths[8],  "payment", row.name, "송금상세경로", extra_data)

    def _add_delivery_row(self, row):
        row_frame = ctk.CTkFrame(self.scroll_delivery, fg_color="transparent", height=30)
        row_frame.pack(fill="x", pady=2)
        row_frame.pack_propagate(False)
        
        widths = [w for _, w in self.COL_SPECS["delivery"]]
        
        self._create_cell(row_frame, row.get("일시", ""), widths[0], "center")
        self._create_cell(row_frame, row.get("출고일", ""), widths[1], "center")
        self._create_cell(row_frame, row.get("품목명", ""), widths[2], "center")
        self._create_cell(row_frame, row.get("출고수량", 0), widths[3], "center", True)
        self._create_cell(row_frame, row.get("송장번호", ""), widths[4], "center")
        
        # extra_data 생성 (파일명용)
        # Delivery: 업체명_관리번호_출고번호
        extra_data = {
            "client": self.lbl_client.cget("text"),
            "mgmt_no": self.mgmt_no,
            "delivery_no": row.get("출고번호", "")
        }
        
        self._create_file_cell(row_frame, row.get("운송장경로", ""), widths[5], "delivery", row.name, "운송장경로", extra_data)
        
        # [변경] 수출신고필증 (통일된 UI 사용)
        self._create_file_cell(row_frame, row.get("수출신고필증경로", ""), widths[6], "delivery", row.name, "수출신고필증경로", extra_data)

        # [신규] CI / PL
        self._create_file_cell(row_frame, row.get("CI경로", ""), widths[7], "delivery", row.name, "CI경로", extra_data)
        self._create_file_cell(row_frame, row.get("PL경로", ""), widths[8], "delivery", row.name, "PL경로", extra_data)

        self._create_cell(row_frame, row.get("비고", ""), widths[9])


    def _add_file_row(self, title, path):
        if path is None: path = ""
        path = str(path).strip()
        if not path or path == "-" or path.lower() == "nan" or path.lower() == "none":
            return False
            
        row = ctk.CTkFrame(self.files_scroll, fg_color="transparent")
        row.pack(fill="x", pady=2)
        
        # 1. 버튼 먼저 배치 (우측 고정)
        ctk.CTkButton(row, text="열기", width=50, height=24,
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
                      command=lambda p=os.path.normpath(path): self.open_file(p)).pack(side="right", padx=10)
        
        # 2. 아이콘 및 타이틀
        ctk.CTkLabel(row, text="📄", font=FONTS["main"]).pack(side="left", padx=(10, 5))
        ctk.CTkLabel(row, text=title, font=FONTS["main_bold"], width=150, anchor="w").pack(side="left")
        
        # 3. 파일명 축약 및 배치
        file_name = os.path.basename(path)
        if len(file_name) > 30:
            file_name = file_name[:27] + "..."
            
        ctk.CTkLabel(row, text=file_name, font=FONTS["small"], text_color=COLORS["text_dim"]).pack(side="left", padx=10)
        return True

    def perform_upload(self, sheet_type, row_idx, col_name, extra_data):
        file_path = filedialog.askopenfilename(title="파일 선택", filetypes=[("All Files", "*.*")])
        if not file_path: return
        
        try:
            # 타겟 디렉토리 및 파일명 생성
            base_filename = os.path.basename(file_path)
            _, ext = os.path.splitext(base_filename)
            timestamp = datetime.datetime.now().strftime("%y%m%d_%H%M%S")
            safe_client = str(extra_data.get("client", "")).replace("/", "_").replace("\\", "_")
            
            target_dir = ""
            new_filename = ""
            
            if sheet_type == "payment":
                target_dir = os.path.join(self.dm.attachment_root, "입금")
                # 파일명: 업체명_관리번호_입금액_timestamp
                new_filename = f"{safe_client}_{extra_data.get('mgmt_no')}_{extra_data.get('amount')}_{timestamp}{ext}"
            elif sheet_type == "delivery":
                if col_name == "수출신고필증경로":
                    target_dir = os.path.join(self.dm.attachment_root, "수출")
                    # 파일명: 업체명_관리번호_출고번호_Export_timestamp
                    d_no = extra_data.get("delivery_no", "")
                    if d_no and d_no != "-":
                         new_filename = f"{safe_client}_{extra_data.get('mgmt_no')}_{d_no}_Export_{timestamp}{ext}"
                    else:
                         new_filename = f"{safe_client}_{extra_data.get('mgmt_no')}_Export_{timestamp}{ext}"
                else:
                    target_dir = os.path.join(self.dm.attachment_root, "납품")
                    # 파일명: 업체명_관리번호_출고번호_timestamp (출고번호 없으면 그냥 timestamp)
                    d_no = extra_data.get("delivery_no", "")
                    if d_no and d_no != "-":
                         new_filename = f"{safe_client}_{extra_data.get('mgmt_no')}_{d_no}_{timestamp}{ext}"
                    else:
                         new_filename = f"{safe_client}_{extra_data.get('mgmt_no')}_{timestamp}{ext}"
            elif sheet_type == "tax_invoice": # New logic for tax invoice upload
                target_dir = os.path.join(self.dm.attachment_root, "세금계산서")
                # 파일명: 업체명_관리번호_세금계산서번호_timestamp
                tax_inv_no = extra_data.get("tax_invoice_no", "")
                if tax_inv_no and tax_inv_no != "-":
                    new_filename = f"{safe_client}_{extra_data.get('mgmt_no')}_{tax_inv_no}_{timestamp}{ext}"
                else:
                    new_filename = f"{safe_client}_{extra_data.get('mgmt_no')}_TaxInvoice_{timestamp}{ext}"
            
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
                
            target_path = os.path.join(target_dir, new_filename)
            
            # 파일 복사
            shutil.copy2(file_path, target_path)
            
            # 데이터 업데이트
            def update_logic(dfs):
                if sheet_type in dfs:
                    # 인덱스로 행 찾아서 업데이트
                    # 주의: dfs[sheet_type]의 인덱스가 보존되어 있어야 함
                    if row_idx in dfs[sheet_type].index:
                        dfs[sheet_type].at[row_idx, col_name] = target_path
                        return True, ""
                    else:
                        return False, "해당 데이터를 찾을 수 없습니다."
                return False, "시트를 찾을 수 없습니다."

            success, msg = self.dm._execute_transaction(update_logic)
            
            if success:
                messagebox.showinfo("성공", "파일이 업로드되었습니다.", parent=self)
                self.refresh_callback() # 팝업 닫힘 및 메인 갱신
                self.destroy()
            else:
                 messagebox.showerror("실패", f"저장 중 오류가 발생했습니다: {msg}", parent=self)

        except Exception as e:
            messagebox.showerror("오류", f"파일 업로드 중 오류 발생: {e}", parent=self)

    def open_file(self, path):
        if path:
            path = os.path.normpath(path)
        if path and os.path.exists(path):
            try: os.startfile(path)
            except Exception as e: messagebox.showerror("에러", f"파일을 열 수 없습니다.\n{e}", parent=self)
        else:
            messagebox.showwarning("경고", f"파일 경로가 유효하지 않습니다.\n경로: {path}", parent=self)

    # BasePopup 추상 메서드 (사용 안함)
    def _create_top_frame(self): pass
    def _create_items_frame(self): pass
    def _create_bottom_frame(self): pass

    def _add_item_row(self, item_data):
        row_frame = ctk.CTkFrame(self.scroll_items, fg_color="transparent", height=30)
        row_frame.pack(fill="x", pady=2)
        
        widths = [w for _, w in self.COL_SPECS["items"]]
        
        self._create_cell(row_frame, item_data.get("모델명", ""), widths[0], "center")
        self._create_cell(row_frame, item_data.get("Description", ""), widths[1], "center")
        self._create_cell(row_frame, item_data.get("수량", 0), widths[2], "center", True)
        self._create_cell(row_frame, item_data.get("단가", 0), widths[3], "right", True)
        self._create_cell(row_frame, item_data.get("공급가액", 0), widths[4], "right", True)
        self._create_cell(row_frame, item_data.get("세액", 0), widths[5], "right", True)
        self._create_cell(row_frame, item_data.get("합계금액", 0), widths[6], "right", True)

        serial = str(item_data.get("시리얼번호", "-"))
        ctk.CTkLabel(row_frame, text=serial, width=widths[7], font=FONTS["main"], anchor="center", text_color=COLORS["primary"]).pack(side="left", padx=2)

    def _add_payment_row(self, row):
        row_frame = ctk.CTkFrame(self.scroll_payment, fg_color="transparent", height=30)
        row_frame.pack(fill="x", pady=2)
        row_frame.pack_propagate(False)
        
        widths = [w for _, w in self.COL_SPECS["payment"]]
        
        self._create_cell(row_frame, row.get("일시", ""), widths[0], "center")
        self._create_cell(row_frame, row.get("구분", ""), widths[1], "center")
        self._create_cell(row_frame, row.get("입금액", 0), widths[2], "right", True)
        self._create_cell(row_frame, row.get("통화", ""), widths[3], "center")
        self._create_cell(row_frame, row.get("작업자", ""), widths[4], "center")
        self._create_cell(row_frame, row.get("세금계산서번호", ""), widths[5], "center")
        self._create_cell(row_frame, row.get("세금계산서발행일", ""), widths[6], "center")
        
        # extra_data 생성 (파일명용)
        # Payment: 업체명_관리번호_입금액
        try: amt = int(float(row.get("입금액", 0)))
        except: amt = 0
        extra_data = {
            "client": self.lbl_client.cget("text"), # 현재 팝업의 업체명
            "mgmt_no": self.mgmt_no,
            "amount": amt,
            "date": row.get("일시", datetime.datetime.now().strftime("%Y-%m-%d"))
        }

        self._create_file_cell(row_frame, row.get("외화입금증빙경로", ""), widths[7], "payment", row.name, "외화입금증빙경로", extra_data)
        self._create_file_cell(row_frame, row.get("송금상세경로", ""), widths[8],  "payment", row.name, "송금상세경로", extra_data)

    def _add_delivery_row(self, row):
        row_frame = ctk.CTkFrame(self.scroll_delivery, fg_color="transparent", height=30)
        row_frame.pack(fill="x", pady=2)
        row_frame.pack_propagate(False)
        
        widths = [w for _, w in self.COL_SPECS["delivery"]]
        
        self._create_cell(row_frame, row.get("일시", ""), widths[0], "center")
        self._create_cell(row_frame, row.get("출고일", ""), widths[1], "center")
        self._create_cell(row_frame, row.get("품목명", ""), widths[2], "center")
        self._create_cell(row_frame, row.get("출고수량", 0), widths[3], "center", True)
        self._create_cell(row_frame, row.get("송장번호", ""), widths[4], "center")
        
        # extra_data 생성 (파일명용)
        # Delivery: 업체명_관리번호_출고번호
        extra_data = {
            "client": self.lbl_client.cget("text"),
            "mgmt_no": self.mgmt_no,
            "delivery_no": row.get("출고번호", "")
        }
        
        self._create_file_cell(row_frame, row.get("운송장경로", ""), widths[5], "delivery", row.name, "운송장경로", extra_data)
        
        # [변경] 수출신고필증 (통일된 UI 사용)
        self._create_file_cell(row_frame, row.get("수출신고필증경로", ""), widths[6], "delivery", row.name, "수출신고필증경로", extra_data)

        # [신규] CI / PL
        self._create_file_cell(row_frame, row.get("CI경로", ""), widths[7], "delivery", row.name, "CI경로", extra_data)
        self._create_file_cell(row_frame, row.get("PL경로", ""), widths[8], "delivery", row.name, "PL경로", extra_data)

        self._create_cell(row_frame, row.get("비고", ""), widths[9])


    def _add_file_row(self, title, path):
        if path is None: path = ""
        path = str(path).strip()
        if not path or path == "-" or path.lower() == "nan" or path.lower() == "none":
            return False
            
        row = ctk.CTkFrame(self.files_scroll, fg_color="transparent")
        row.pack(fill="x", pady=2)
        
        # 1. 버튼 먼저 배치 (우측 고정)
        ctk.CTkButton(row, text="열기", width=50, height=24,
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
                      command=lambda p=os.path.normpath(path): self.open_file(p)).pack(side="right", padx=10)
        
        # 2. 아이콘 및 타이틀
        ctk.CTkLabel(row, text="📄", font=FONTS["main"]).pack(side="left", padx=(10, 5))
        ctk.CTkLabel(row, text=title, font=FONTS["main_bold"], width=150, anchor="w").pack(side="left")
        
        # 3. 파일명 축약 및 배치
        file_name = os.path.basename(path)
        if len(file_name) > 30:
            file_name = file_name[:27] + "..."
            
        ctk.CTkLabel(row, text=file_name, font=FONTS["small"], text_color=COLORS["text_dim"]).pack(side="left", padx=10)
        return True

    def perform_upload(self, sheet_type, row_idx, col_name, extra_data):
        file_path = filedialog.askopenfilename(title="파일 선택", filetypes=[("All Files", "*.*")])
        if not file_path: return
        
        try:
            # 타겟 디렉토리 및 파일명 생성
            base_filename = os.path.basename(file_path)
            _, ext = os.path.splitext(base_filename)
            timestamp = datetime.datetime.now().strftime("%y%m%d_%H%M%S")
            safe_client = str(extra_data.get("client", "")).replace("/", "_").replace("\\", "_")
            
            target_dir = ""
            new_filename = ""
            
            if sheet_type == "payment":
                target_dir = os.path.join(self.dm.attachment_root, "입금")
                # 파일명: 업체명_관리번호_입금액_timestamp
                new_filename = f"{safe_client}_{extra_data.get('mgmt_no')}_{extra_data.get('amount')}_{timestamp}{ext}"
            elif sheet_type == "delivery":
                if col_name == "수출신고필증경로":
                    target_dir = os.path.join(self.dm.attachment_root, "수출")
                    # 파일명: 업체명_관리번호_출고번호_Export_timestamp
                    d_no = extra_data.get("delivery_no", "")
                    if d_no and d_no != "-":
                         new_filename = f"{safe_client}_{extra_data.get('mgmt_no')}_{d_no}_Export_{timestamp}{ext}"
                    else:
                         new_filename = f"{safe_client}_{extra_data.get('mgmt_no')}_Export_{timestamp}{ext}"
                else:
                    target_dir = os.path.join(self.dm.attachment_root, "납품")
                    # 파일명: 업체명_관리번호_출고번호_timestamp (출고번호 없으면 그냥 timestamp)
                    d_no = extra_data.get("delivery_no", "")
                    if d_no and d_no != "-":
                         new_filename = f"{safe_client}_{extra_data.get('mgmt_no')}_{d_no}_{timestamp}{ext}"
                    else:
                         new_filename = f"{safe_client}_{extra_data.get('mgmt_no')}_{timestamp}{ext}"
            elif sheet_type == "tax_invoice": # New logic for tax invoice upload
                target_dir = os.path.join(self.dm.attachment_root, "세금계산서")
                # 파일명: 업체명_관리번호_세금계산서번호_timestamp
                tax_inv_no = extra_data.get("tax_invoice_no", "")
                if tax_inv_no and tax_inv_no != "-":
                    new_filename = f"{safe_client}_{extra_data.get('mgmt_no')}_{tax_inv_no}_{timestamp}{ext}"
                else:
                    new_filename = f"{safe_client}_{extra_data.get('mgmt_no')}_TaxInvoice_{timestamp}{ext}"
            
            if not os.path.exists(target_dir):
                os.makedirs(target_dir)
                
            target_path = os.path.join(target_dir, new_filename)
            
            # 파일 복사
            shutil.copy2(file_path, target_path)
            
            # 데이터 업데이트
            def update_logic(dfs):
                if sheet_type in dfs:
                    # 인덱스로 행 찾아서 업데이트
                    # 주의: dfs[sheet_type]의 인덱스가 보존되어 있어야 함
                    if row_idx in dfs[sheet_type].index:
                        dfs[sheet_type].at[row_idx, col_name] = target_path
                        return True, ""
                    else:
                        return False, "해당 데이터를 찾을 수 없습니다."
                return False, "시트를 찾을 수 없습니다."

            success, msg = self.dm._execute_transaction(update_logic)
            
            if success:
                messagebox.showinfo("성공", "파일이 업로드되었습니다.", parent=self)
                self.refresh_callback() # 팝업 닫힘 및 메인 갱신
                self.destroy()
            else:
                 messagebox.showerror("실패", f"저장 중 오류가 발생했습니다: {msg}", parent=self)

        except Exception as e:
            messagebox.showerror("오류", f"파일 업로드 중 오류 발생: {e}", parent=self)

    def open_file(self, path):
        if path:
            path = os.path.normpath(path)
        if path and os.path.exists(path):
            try: os.startfile(path)
            except Exception as e: messagebox.showerror("에러", f"파일을 열 수 없습니다.\n{e}", parent=self)
        else:
            messagebox.showwarning("경고", f"파일 경로가 유효하지 않습니다.\n경로: {path}", parent=self)

    # BasePopup 추상 메서드 (사용 안함)
    def _create_top_frame(self): pass
    def _create_items_frame(self): pass
    def _create_bottom_frame(self): pass
    def _create_files_frame(self): pass
    def _create_action_buttons(self): pass
    def save(self): pass
    def delete(self): pass
    def _generate_new_id(self): pass
    def _load_clients(self): pass