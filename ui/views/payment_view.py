import tkinter as tk
from tkinter import messagebox, ttk

import customtkinter as ctk
import pandas as pd

# [변경] 경로 수정
from src.config import Config
from src.styles import COLORS, FONT_FAMILY, FONTS


class PaymentView(ctk.CTkFrame):
    def __init__(self, parent, data_manager, popup_manager):
        super().__init__(parent, fg_color="transparent")
        self.dm = data_manager
        self.pm = popup_manager

        self.display_cols = ["관리번호", "업체명", "합계금액", "기수금액", "미수금액", "출고일", "Status"]
        
        self.create_widgets()
        self.style_treeview()
        self.refresh_data()

    def create_widgets(self):
        toolbar = ctk.CTkFrame(self, height=50, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(toolbar, text="💰 입금 관리 (수금)", font=FONTS["title"], text_color=COLORS["text"]).pack(side="left")

        ctk.CTkButton(toolbar, text="새로고침", width=80, command=self.refresh_data,
                      fg_color=COLORS["bg_medium"], hover_color=COLORS["bg_light"], text_color=COLORS["text"]).pack(side="right", padx=(0, 10))

        ctk.CTkButton(toolbar, text="💵 선택 항목 일괄 입금", width=150, command=self.on_process_payment,
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"]).pack(side="right", padx=(0, 10))

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

        self.tree.tag_configure("unpaid", foreground="#FF5252")

        self.tree.bind("<Double-1>", lambda e: self.on_process_payment())

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
            df["_unpaid"] = pd.to_numeric(df["미수금액"], errors='coerce').fillna(0)
            
            target_statuses = ["주문", "생산중", "납품대기", "납품완료/입금대기"]
            
            mask_unpaid = df["_unpaid"] > 0
            mask_status = df["Status"].astype(str).isin(target_statuses)
            
            target_df = df[mask_unpaid & mask_status].copy()
            
        except Exception:
            target_df = df

        if target_df.empty: return
        
        target_df = target_df.sort_values(by="출고일", ascending=False)

        for idx, row in target_df.iterrows():
            total = float(row.get("합계금액", 0) or 0)
            paid = float(row.get("기수금액", 0) or 0)
            unpaid = float(row.get("미수금액", 0) or 0)
            
            row_tags = ("unpaid",) if unpaid > 0 else ()

            values = [
                row.get("관리번호"),
                row.get("업체명"),
                f"{total:,.0f}",
                f"{paid:,.0f}",
                f"{unpaid:,.0f}",
                row.get("출고일"),
                row.get("Status")
            ]
            
            self.tree.insert("", "end", iid=idx, values=values, tags=row_tags)

    def on_process_payment(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("경고", "입금 처리할 항목을 하나 이상 선택해주세요.")
            return
        
        first_idx = int(selected_items[0])
        try:
            first_client = self.dm.df_data.loc[first_idx, "업체명"]
        except KeyError:
            messagebox.showerror("오류", "선택된 항목의 정보를 찾을 수 없습니다.")
            return
        
        target_mgmt_nos = set()

        for item in selected_items:
            idx = int(item)
            try:
                client = self.dm.df_data.loc[idx, "업체명"]
                mgmt_no = self.dm.df_data.loc[idx, "관리번호"]
            except KeyError: continue
            
            if client != first_client:
                messagebox.showwarning("주의", "동일한 업체의 항목들만 일괄 입금 처리가 가능합니다.")
                return
            
            target_mgmt_nos.add(mgmt_no)

        self.pm.open_payment_popup(list(target_mgmt_nos))