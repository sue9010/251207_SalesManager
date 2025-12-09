import tkinter as tk
from tkinter import messagebox, ttk

import customtkinter as ctk
import pandas as pd

from src.config import Config
from src.styles import COLORS, FONT_FAMILY, FONTS


class AfterSalesView(ctk.CTkFrame):
    def __init__(self, parent, data_manager, popup_manager):
        super().__init__(parent, fg_color="transparent")
        self.dm = data_manager
        self.pm = popup_manager

        # 입금 뷰와 동일한 컬럼 구성
        self.display_cols = ["관리번호", "업체명", "합계금액", "기수금액", "미수금액", "출고일", "Status"]
        
        self.create_widgets()
        self.style_treeview()
        self.refresh_data()

    def create_widgets(self):
        toolbar = ctk.CTkFrame(self, height=50, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(toolbar, text="🔧 사후처리 (A/S)", font=FONTS["title"], text_color=COLORS["text"]).pack(side="left")

        ctk.CTkButton(toolbar, text="새로고침", width=80, command=self.refresh_data,
                      fg_color=COLORS["bg_medium"], hover_color=COLORS["bg_light"], text_color=COLORS["text"]).pack(side="right", padx=(0, 10))

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
            if "금액" in col: width = 120 
            self.tree.column(col, width=width, anchor="center")

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
        
        style.map("Treeview", background=[('selected', COLORS["primary"][1])])

    def refresh_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        df = self.dm.df_data
        if df.empty: return

        try:
            # Status가 "완료"인 항목만 필터링
            target_df = df[df["Status"] == "완료"].copy()
            
        except Exception:
            target_df = pd.DataFrame()

        if target_df.empty: return
        
        target_df = target_df.sort_values(by="출고일", ascending=False)

        for idx, row in target_df.iterrows():
            total = float(row.get("합계금액", 0) or 0)
            paid = float(row.get("기수금액", 0) or 0)
            unpaid = float(row.get("미수금액", 0) or 0)
            
            values = [
                row.get("관리번호"),
                row.get("업체명"),
                f"{total:,.0f}",
                f"{paid:,.0f}",
                f"{unpaid:,.0f}",
                row.get("출고일"),
                row.get("Status")
            ]
            
            self.tree.insert("", "end", iid=idx, values=values)
