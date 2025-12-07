import os
import tkinter as tk
from tkinter import messagebox

import customtkinter as ctk
import pandas as pd

# [변경] 경로 수정
from ui.popups.base_popup import BasePopup
from src.styles import COLORS, FONTS
from src.config import Config

class CompletePopup(BasePopup):
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

        self.geometry("1200x900")

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

    def _setup_items_tab(self, parent):
        # 헤더 설정 (시리얼 번호 포함)
        headers = ["품명", "모델명", "시리얼 번호", "Description", "수량", "단가", "공급가액", "세액", "합계금액"]
        widths = [150, 150, 120, 200, 60, 100, 100, 80, 100]
        
        header_frame = ctk.CTkFrame(parent, height=30, fg_color=COLORS["bg_light"])
        header_frame.pack(fill="x", padx=5, pady=5)
        
        for h, w in zip(headers, widths):
            ctk.CTkLabel(header_frame, text=h, width=w, font=FONTS["main_bold"]).pack(side="left", padx=2)
            
        self.scroll_items = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        self.scroll_items.pack(fill="both", expand=True, padx=5, pady=5)

    def _setup_payment_history_tab(self, parent):
        headers = ["일시", "구분", "입금액", "통화", "작업자", "비고"]
        widths = [150, 100, 120, 60, 100, 200]
        
        header_frame = ctk.CTkFrame(parent, height=30, fg_color=COLORS["bg_light"])
        header_frame.pack(fill="x", padx=5, pady=5)
        
        for h, w in zip(headers, widths):
            ctk.CTkLabel(header_frame, text=h, width=w, font=FONTS["main_bold"]).pack(side="left", padx=2)
            
        self.scroll_payment = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        self.scroll_payment.pack(fill="both", expand=True, padx=5, pady=5)

    def _setup_delivery_history_tab(self, parent):
        headers = ["처리일시", "출고일", "품목명", "출고수량", "송장번호", "운송방법", "비고"]
        widths = [150, 100, 200, 80, 120, 100, 150]
        
        header_frame = ctk.CTkFrame(parent, height=30, fg_color=COLORS["bg_light"])
        header_frame.pack(fill="x", padx=5, pady=5)
        
        for h, w in zip(headers, widths):
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

    def _load_data(self):
        df = self.dm.df_data
        rows = df[df["관리번호"].astype(str) == str(self.mgmt_no)]
        if rows.empty: return

        # [수정] Delivery 시트 데이터 로드
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
            
            # [수정] Delivery 시트에서 해당 품목의 시리얼 번호 찾기
            serial = "-"
            if not current_deliveries.empty:
                # 품목명이 일치하고 시리얼 번호가 있는 행 필터링
                target_del = current_deliveries[
                    (current_deliveries["품목명"].astype(str).str.strip() == item_name) & 
                    (current_deliveries["시리얼번호"].notna()) & 
                    (current_deliveries["시리얼번호"].astype(str) != "-") &
                    (current_deliveries["시리얼번호"].astype(str) != "")
                ]
                
                if not target_del.empty:
                    # 모든 시리얼 번호를 쉼표로 연결 (중복 제거)
                    serials = sorted(list(set(target_del["시리얼번호"].astype(str).tolist())))
                    serial = ", ".join(serials)

            # 아이템 데이터에 시리얼 추가
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

        # 5. 파일 리스트 로드
        for widget in self.files_scroll.winfo_children(): widget.destroy()
        has_files = False
        
        # 5-1. Data 시트의 파일들
        if self._add_file_row("주문서(발주서)", first.get("발주서경로")): has_files = True
        if self._add_file_row("운송장", first.get("운송장경로")): has_files = True
        
        # 5-2. Payment 시트의 파일들
        added_paths = set()
        
        if not self.dm.df_payment.empty:
            p_rows = self.dm.df_payment[self.dm.df_payment["관리번호"].astype(str) == str(self.mgmt_no)]
            for _, prow in p_rows.iterrows():
                f_path = str(prow.get("외화입금증빙경로", "")).strip()
                if f_path and f_path.lower() != "nan" and f_path != "-" and f_path not in added_paths:
                    if self._add_file_row("외국환 거래 계산서", f_path): 
                        has_files = True
                        added_paths.add(f_path)
                
                r_path = str(prow.get("송금상세경로", "")).strip()
                if r_path and r_path.lower() != "nan" and r_path != "-" and r_path not in added_paths:
                    if self._add_file_row("Remittance Detail", r_path): 
                        has_files = True
                        added_paths.add(r_path)

        # 5-3. Delivery 시트의 운송장
        if not self.dm.df_delivery.empty:
            d_rows = self.dm.df_delivery[self.dm.df_delivery["관리번호"].astype(str) == str(self.mgmt_no)]
            for _, drow in d_rows.iterrows():
                d_path = str(drow.get("운송장경로", "")).strip()
                if d_path and d_path.lower() != "nan" and d_path != "-" and d_path not in added_paths:
                    deliv_no = str(drow.get("출고번호", ""))
                    label = f"운송장 ({deliv_no})" if deliv_no and deliv_no != "-" else "운송장"
                    if self._add_file_row(label, d_path):
                        has_files = True
                        added_paths.add(d_path)

        # 5-4. 사업자등록증
        client_name = str(first.get("업체명", ""))
        client_row = self.dm.df_clients[self.dm.df_clients["업체명"] == client_name]
        if not client_row.empty:
            if self._add_file_row("사업자등록증", client_row.iloc[0].get("사업자등록증경로")): has_files = True
                
        if not has_files:
            ctk.CTkLabel(self.files_scroll, text="첨부 파일 없음", font=FONTS["small"], text_color=COLORS["text_dim"]).pack(pady=20)

    # 행 추가 헬퍼 메서드들
    def _create_cell(self, parent, val, width, justify="left", is_num=False, is_bold=False):
        if is_num:
            try: val = f"{float(val):,.0f}"
            except: val = "0"
        
        font = FONTS["main_bold"] if is_bold else FONTS["main"]
        lbl = ctk.CTkLabel(parent, text=str(val), width=width, font=font, 
                           anchor="e" if justify=="right" else "w" if justify=="left" else "center")
        lbl.pack(side="left", padx=2)

    def _add_item_row(self, item_data):
        row_frame = ctk.CTkFrame(self.scroll_items, fg_color="transparent", height=30)
        row_frame.pack(fill="x", pady=2)
        
        self._create_cell(row_frame, item_data.get("품목명", ""), 150, is_bold=True)
        self._create_cell(row_frame, item_data.get("모델명", ""), 150)
        
        # [수정] 시리얼 번호 셀 추가
        serial = str(item_data.get("시리얼번호", "-"))
        ctk.CTkLabel(row_frame, text=serial, width=120, font=FONTS["main"], anchor="center", text_color=COLORS["primary"]).pack(side="left", padx=2)
        
        self._create_cell(row_frame, item_data.get("Description", ""), 200)
        self._create_cell(row_frame, item_data.get("수량", 0), 60, "center", True)
        self._create_cell(row_frame, item_data.get("단가", 0), 100, "right", True)
        self._create_cell(row_frame, item_data.get("공급가액", 0), 100, "right", True)
        self._create_cell(row_frame, item_data.get("세액", 0), 80, "right", True)
        self._create_cell(row_frame, item_data.get("합계금액", 0), 100, "right", True)

    def _add_payment_row(self, row):
        row_frame = ctk.CTkFrame(self.scroll_payment, fg_color="transparent", height=30)
        row_frame.pack(fill="x", pady=2)
        
        self._create_cell(row_frame, row.get("일시", ""), 150)
        self._create_cell(row_frame, row.get("구분", ""), 100, "center")
        self._create_cell(row_frame, row.get("입금액", 0), 120, "right", True)
        self._create_cell(row_frame, row.get("통화", ""), 60, "center")
        self._create_cell(row_frame, row.get("작업자", ""), 100)
        self._create_cell(row_frame, row.get("비고", ""), 200)

    def _add_delivery_row(self, row):
        row_frame = ctk.CTkFrame(self.scroll_delivery, fg_color="transparent", height=30)
        row_frame.pack(fill="x", pady=2)
        
        self._create_cell(row_frame, row.get("일시", ""), 150)
        self._create_cell(row_frame, row.get("출고일", ""), 100, "center")
        self._create_cell(row_frame, row.get("품목명", ""), 200)
        self._create_cell(row_frame, row.get("출고수량", 0), 80, "center", True)
        self._create_cell(row_frame, row.get("송장번호", ""), 120)
        self._create_cell(row_frame, row.get("운송방법", ""), 100)
        self._create_cell(row_frame, row.get("비고", ""), 150)

    def _add_file_row(self, title, path):
        if path is None: path = ""
        path = str(path).strip()
        if not path or path == "-" or path.lower() == "nan" or path.lower() == "none":
            return False
            
        row = ctk.CTkFrame(self.files_scroll, fg_color="transparent")
        row.pack(fill="x", pady=2)
        
        ctk.CTkLabel(row, text="📄", font=FONTS["main"]).pack(side="left", padx=(10, 5))
        ctk.CTkLabel(row, text=title, font=FONTS["main_bold"], width=150, anchor="w").pack(side="left")
        
        file_name = os.path.basename(path)
        ctk.CTkLabel(row, text=file_name, font=FONTS["small"], text_color=COLORS["text_dim"]).pack(side="left", padx=10)
        
        ctk.CTkButton(row, text="열기", width=50, height=24,
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
                      command=lambda p=path: self.open_file(p)).pack(side="right", padx=10)
        return True

    def open_file(self, path):
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