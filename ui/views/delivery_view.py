import tkinter as tk
from tkinter import messagebox, ttk

import customtkinter as ctk
import pandas as pd

# [변경] 경로 수정
from src.config import Config
from src.styles import COLORS, FONT_FAMILY, FONTS


class DeliveryView(ctk.CTkFrame):
    def __init__(self, parent, data_manager, popup_manager):
        super().__init__(parent, fg_color="transparent")
        self.dm = data_manager
        self.pm = popup_manager

        self.display_cols = ["관리번호", "업체명", "모델명", "수량", "단가", "출고예정일", "생산상태", "Status"]
        
        self.create_widgets()
        self.style_treeview()
        self.refresh_data()

    def create_widgets(self):
        toolbar = ctk.CTkFrame(self, height=50, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(toolbar, text="🚚 납품 관리 (출고)", font=FONTS["title"], text_color=COLORS["text"]).pack(side="left")

        self.entry_search = ctk.CTkEntry(toolbar, width=250, placeholder_text="관리번호, 업체명, 모델명...")
        self.entry_search.pack(side="left", padx=(20, 10))
        self.entry_search.bind("<Return>", lambda e: self.refresh_data())

        ctk.CTkButton(toolbar, text="검색", width=60, command=self.refresh_data, 
                      fg_color=COLORS["bg_medium"], hover_color=COLORS["bg_light"], text_color=COLORS["text"]).pack(side="left")

        ctk.CTkButton(toolbar, text="📦 선택 항목 일괄 출고", width=150, command=self.on_process_delivery,
                      fg_color=COLORS["success"], hover_color="#26A65B").pack(side="right", padx=(0, 10))
        
        ctk.CTkButton(toolbar, text="새로고침", width=80, command=self.refresh_data,
                      fg_color=COLORS["bg_medium"], hover_color=COLORS["bg_light"], text_color=COLORS["text"]).pack(side="right")

        tree_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_medium"], corner_radius=10)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        scroll_y = ctk.CTkScrollbar(tree_frame, orientation="vertical")
        scroll_y.pack(side="right", fill="y", padx=(0, 5), pady=5)

        self.tree = ttk.Treeview(tree_frame, columns=self.display_cols, show="headings", yscrollcommand=scroll_y.set, selectmode="extended")
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)
        scroll_y.configure(command=self.tree.yview)

        for col in self.display_cols:
            self.tree.heading(col, text=col)
            width = 100
            if col == "관리번호": width = 120
            if col == "업체명": width = 150
            if col == "모델명": width = 200
            if col == "생산상태": width = 100
            self.tree.column(col, width=width, anchor="center")

        self.tree.bind("<Double-1>", lambda e: self.on_process_delivery())

    def style_treeview(self):
        style = ttk.Style()
        style.theme_use("default")
        
        bg_color = "#2b2b2b" if self.dm.current_theme == "Dark" else "#F5F5F5"
        fg_color = "white" if self.dm.current_theme == "Dark" else "black"
        header_bg = "#3a3a3a" if self.dm.current_theme == "Dark" else "#E0E0E0"
        header_fg = "white" if self.dm.current_theme == "Dark" else "black"
        
        style.configure("Treeview", 
                        background=bg_color, 
                        foreground=fg_color, 
                        fieldbackground=bg_color, 
                        rowheight=30, 
                        borderwidth=0, 
                        font=FONTS["main"])
        
        style.configure("Treeview.Heading", 
                        font=(FONT_FAMILY, 11, "bold"), 
                        background=header_bg, 
                        foreground=header_fg, 
                        relief="flat")
        
        style.map("Treeview", background=[('selected', COLORS["success"][1])])

    def refresh_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        df = self.dm.df_data
        if df.empty: return

        prod_status_map = self.dm.get_production_status_map()

        keyword = self.entry_search.get().strip().lower()
        target_status = ["생산중", "납품대기", "납품대기/입금완료","납품완료/입금대기"]
        target_df = df[df["Status"].astype(str).isin(target_status)]
        
        if target_df.empty: return
        target_df = target_df.sort_values(by="출고예정일")

        for idx, row in target_df.iterrows():
            if keyword:
                matched = False
                for col in Config.SEARCH_TARGET_COLS:
                    if keyword in str(row.get(col, "")).lower():
                        matched = True
                        break
                if not matched: continue

            try:
                price = float(row.get("단가", 0))
                fmt_price = f"{price:,.0f}"
            except:
                fmt_price = str(row.get("단가", 0))

            mgmt_no = str(row.get("관리번호", ""))
            prod_status = prod_status_map.get(mgmt_no, "-")

            values = [
                mgmt_no,
                row.get("업체명"),
                row.get("모델명"),
                row.get("수량"),
                fmt_price,
                row.get("출고예정일"),
                prod_status,
                row.get("Status")
            ]
            self.tree.insert("", "end", iid=idx, values=values)

    def on_process_delivery(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("경고", "출고 처리할 항목을 하나 이상 선택해주세요.")
            return
        
        first_item_idx = int(selected_items[0])
        try:
            first_client = self.dm.df_data.loc[first_item_idx, "업체명"]
        except:
            messagebox.showerror("오류", "선택된 데이터의 정보를 찾을 수 없습니다.")
            return
        
        target_mgmt_nos = set()

        for item in selected_items:
            item_idx = int(item)
            try:
                client = self.dm.df_data.loc[item_idx, "업체명"]
                mgmt_no = self.dm.df_data.loc[item_idx, "관리번호"]
            except: continue
            
            if client != first_client:
                messagebox.showwarning("주의", "동일한 업체의 항목들만 일괄 출고 처리가 가능합니다.")
                return
            
            target_mgmt_nos.add(mgmt_no)

        self.pm.open_delivery_popup(list(target_mgmt_nos))