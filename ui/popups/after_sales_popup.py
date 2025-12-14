import os
import shutil
import tkinter as tk
from datetime import datetime
from tkinter import messagebox
import getpass


import customtkinter as ctk
import pandas as pd

from src.config import Config
from ui.popups.base_popup import BasePopup
from src.styles import COLORS, FONTS

class AfterSalesPopup(BasePopup):
    def __init__(self, parent, data_manager, refresh_callback, mgmt_nos):
        if isinstance(mgmt_nos, list):
            self.mgmt_nos = mgmt_nos
        else:
            self.mgmt_nos = [mgmt_nos]

        if not self.mgmt_nos:
            messagebox.showerror("오류", "처리할 대상이 지정되지 않았습니다.", parent=parent)
            self.destroy()
            return
            
        super().__init__(parent, data_manager, refresh_callback, popup_title="사후처리", mgmt_no=self.mgmt_nos[0])
        self.geometry("1300x850")


    def _create_header(self, parent):
        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 10))
        
        # 상단: ID 및 상태
        top_row = ctk.CTkFrame(header_frame, fg_color="transparent")
        top_row.pack(fill="x", anchor="w")
        
        # ID 표시
        id_text = self.mgmt_nos[0]
        if len(self.mgmt_nos) > 1:
            id_text += f" 외 {len(self.mgmt_nos)-1}건"
            
        self.entry_id = ctk.CTkEntry(top_row, width=200, font=FONTS["main_bold"], text_color=COLORS["text_dim"])
        self.entry_id.pack(side="left")
        self.entry_id.insert(0, id_text)
        self.entry_id.configure(state="readonly")

    def _setup_info_panel(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(1, weight=1)

        # Row 0: Tax Date (Full Width)
        f_date = ctk.CTkFrame(parent, fg_color="transparent")
        f_date.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        ctk.CTkLabel(f_date, text="세금계산서 발행일", width=120, anchor="w", font=FONTS["main"], text_color=COLORS["text_dim"]).pack(side="left")
        self.entry_tax_date = ctk.CTkEntry(f_date, height=28, placeholder_text="YYYY-MM-DD",
                                           fg_color=COLORS["entry_bg"], border_color=COLORS["entry_border"], border_width=2)
        self.entry_tax_date.pack(side="left", fill="x", expand=True)

        # Row 1: Tax Invoice No
        f_tax_no = ctk.CTkFrame(parent, fg_color="transparent")
        f_tax_no.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        ctk.CTkLabel(f_tax_no, text="세금계산서 번호", width=120, anchor="w", font=FONTS["main"], text_color=COLORS["text_dim"]).pack(side="left")
        self.entry_tax_no = ctk.CTkEntry(f_tax_no, height=28, fg_color=COLORS["entry_bg"], border_color=COLORS["entry_border"], border_width=2)
        self.entry_tax_no.pack(side="left", fill="x", expand=True)

        # Row 2: Export Declaration No
        f_export_no = ctk.CTkFrame(parent, fg_color="transparent")
        f_export_no.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        ctk.CTkLabel(f_export_no, text="수출신고번호", width=120, anchor="w", font=FONTS["main"], text_color=COLORS["text_dim"]).pack(side="left")
        self.entry_export_no = ctk.CTkEntry(f_export_no, height=28, fg_color=COLORS["entry_bg"], border_color=COLORS["entry_border"], border_width=2)
        self.entry_export_no.pack(side="left", fill="x", expand=True)

        # Row 3: Export Declaration File
        f_file = ctk.CTkFrame(parent, fg_color="transparent")
        f_file.grid(row=3, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        self.entry_file_export, _, _, _ = self.create_file_input_row(f_file, "수출신고필증", "수출신고필증경로")

    def _setup_items_panel(self, parent):
        # 타이틀
        top_frame = ctk.CTkFrame(parent, fg_color="transparent")
        top_frame.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(top_frame, text="관련 품목 리스트 (Read Only)", font=FONTS["header"]).pack(side="left")
        
        # 헤더 (BasePopup.COL_CONFIG 사용)
        configs = [
            self.COL_CONFIG["item"], self.COL_CONFIG["model"], self.COL_CONFIG["desc"],
            self.COL_CONFIG["qty"], self.COL_CONFIG["price"], self.COL_CONFIG["supply"],
            self.COL_CONFIG["tax"], self.COL_CONFIG["total"]
        ]
        
        header_frame = ctk.CTkFrame(parent, height=35, fg_color=COLORS["bg_dark"])
        header_frame.pack(fill="x", padx=15)
        
        for conf in configs:
            ctk.CTkLabel(header_frame, text=conf["header"], width=conf["width"], font=FONTS["main_bold"]).pack(side="left", padx=2)
            
        # 스크롤 리스트
        self.scroll_items = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        self.scroll_items.pack(fill="both", expand=True, padx=10, pady=5)

    def _create_footer(self, parent):
        footer_frame = ctk.CTkFrame(parent, fg_color="transparent")
        footer_frame.pack(fill="x", pady=(10, 0))
        
        ctk.CTkButton(footer_frame, text="닫기", command=self.destroy, width=100, height=45,
                      fg_color=COLORS["bg_light"], hover_color=COLORS["bg_light_hover"], 
                      text_color=COLORS["text"]).pack(side="left")
                      
        ctk.CTkButton(footer_frame, text="저장", command=self.save, width=200, height=45,
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"], 
                      font=FONTS["header"]).pack(side="right")

    def _add_item_row(self, item_data=None):
        # BasePopup._add_item_row를 사용하되, 버튼 제거 및 ReadOnly 처리
        row_widgets = super()._add_item_row(item_data)
        
        # 삭제 버튼 제거 (있다면)
        try:
            for child in row_widgets["frame"].winfo_children():
                if isinstance(child, ctk.CTkButton): child.destroy()
        except: pass
        
        if item_data is not None:
            def set_val(key, val, is_num=False):
                if is_num:
                    try: val = f"{float(str(val).replace(',', '')):,.0f}"
                    except: val = "0"
                else:
                    val = str(val)
                    if val == "nan": val = ""
                
                w = row_widgets[key]
                w.configure(state="normal")
                w.delete(0, "end")
                w.insert(0, val)
                w.configure(state="readonly")

            set_val("item", item_data.get("품목명", ""))
            set_val("model", item_data.get("모델명", ""))
            set_val("desc", item_data.get("Description", ""))
            set_val("qty", item_data.get("수량", 0), is_num=True)
            set_val("price", item_data.get("단가", 0), is_num=True)
            set_val("supply", item_data.get("공급가액", 0), is_num=True)
            set_val("tax", item_data.get("세액", 0), is_num=True)
            set_val("total", item_data.get("합계금액", 0), is_num=True)
                
        return row_widgets

    def _load_data(self):
        df = self.dm.df_data
        rows = df[df["관리번호"].isin(self.mgmt_nos)].copy()
        
        if rows.empty: return

        first = rows.iloc[0]
        
        # 기존 데이터 로드
        self.entry_tax_date.insert(0, str(first.get("세금계산서발행일", "")).replace("nan", "").replace("-", ""))
        self.entry_tax_no.insert(0, str(first.get("계산서번호", "")).replace("nan", "").replace("-", ""))
        self.entry_export_no.insert(0, str(first.get("수출신고번호", "")).replace("nan", "").replace("-", ""))
        
        # 파일 경로 로드 (첫 번째 항목 기준)
        path = str(first.get("수출신고필증경로", "")).replace("nan", "").replace("-", "")
        if path:
            self.entry_file_export.delete(0, "end")
            self.entry_file_export.insert(0, path)

        for _, row in rows.iterrows():
            self._add_item_row(row)

    def save(self):
        tax_date = self.entry_tax_date.get()
        tax_no = self.entry_tax_no.get()
        export_no = self.entry_export_no.get()

        # File Saving Logic
        saved_paths = {}
        try:
            client_name = self.dm.df_data.loc[self.dm.df_data["관리번호"] == self.mgmt_nos[0], "업체명"].values[0]
        except: client_name = "Unknown"
        
        info_text = f"{client_name}_{self.mgmt_nos[0]}"

        file_inputs = [
            ("수출신고필증경로", "ExportDeclaration")
        ]

        for col, prefix in file_inputs:
            success, msg, path = self.file_manager.save_file(col, "사후처리", prefix, info_text)
            if success and path:
                saved_paths[col] = path
            elif not success and msg:
                print(f"File save warning ({col}): {msg}") 

        success, msg = self.dm.process_after_sales(
            self.mgmt_nos,
            tax_date,
            tax_no,
            export_no,
            saved_paths
        )

        if success:
            messagebox.showinfo("성공", "사후처리 정보가 저장되었습니다.", parent=self)
            self.refresh_callback()
            self.destroy()
        else:
            messagebox.showerror("실패", f"저장에 실패했습니다: {msg}", parent=self)
    
    # BasePopup 추상 메서드 구현 (사용 안함)
    def _generate_new_id(self): pass
    def delete(self): pass
    def _on_client_select(self, client_name): pass
