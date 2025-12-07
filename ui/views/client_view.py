import tkinter as tk
from tkinter import messagebox, ttk

import customtkinter as ctk

# [변경] 경로 수정
from src.styles import COLORS, FONT_FAMILY, FONTS
from src.config import Config


class ClientView(ctk.CTkFrame):
    def __init__(self, parent, data_manager, popup_manager):
        super().__init__(parent, fg_color="transparent")
        self.dm = data_manager
        self.pm = popup_manager

        self.display_cols = ["업체명", "국가", "담당자", "전화번호", "이메일", "특이사항"]
        
        self.create_widgets()
        self.style_treeview()
        self.refresh_data()

    def create_widgets(self):
        toolbar = ctk.CTkFrame(self, height=50, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=(20, 10))

        ctk.CTkLabel(toolbar, text="🏢 업체 관리", font=FONTS["title"], text_color=COLORS["text"]).pack(side="left")

        self.entry_search = ctk.CTkEntry(toolbar, width=250, placeholder_text="업체명, 담당자 검색...")
        self.entry_search.pack(side="left", padx=(20, 10))
        self.entry_search.bind("<Return>", lambda e: self.refresh_data())

        ctk.CTkButton(toolbar, text="검색", width=60, command=self.refresh_data, 
                      fg_color=COLORS["bg_medium"], hover_color=COLORS["bg_light"], text_color=COLORS["text"]).pack(side="left")

        ctk.CTkButton(toolbar, text="+ 업체 등록", width=100, command=self.open_add_popup,
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"]).pack(side="right")
        
        ctk.CTkButton(toolbar, text="새로고침", width=80, command=self.refresh_data,
                      fg_color=COLORS["bg_medium"], hover_color=COLORS["bg_light"], text_color=COLORS["text"]).pack(side="right", padx=(0, 10))

        tree_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_medium"], corner_radius=10)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        scroll_y = ctk.CTkScrollbar(tree_frame, orientation="vertical")
        scroll_y.pack(side="right", fill="y", padx=(0, 5), pady=5)

        self.tree = ttk.Treeview(tree_frame, columns=self.display_cols, show="headings", yscrollcommand=scroll_y.set)
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)
        scroll_y.configure(command=self.tree.yview)

        for col in self.display_cols:
            self.tree.heading(col, text=col)
            width = 150 if col == "업체명" else 100
            if col == "이메일": width = 150
            if col == "특이사항": width = 200
            self.tree.column(col, width=width, anchor="center")

        self.tree.bind("<Double-1>", self.on_double_click)

    def style_treeview(self):
        style = ttk.Style()
        style.theme_use("default")
        
        bg = "#2b2b2b" if self.dm.current_theme == "Dark" else "#F5F5F5"
        fg = "white" if self.dm.current_theme == "Dark" else "black"
        
        style.configure("Treeview", background=bg, foreground=fg, fieldbackground=bg, rowheight=30, borderwidth=0, font=FONTS["main"])
        style.configure("Treeview.Heading", font=(FONT_FAMILY, 11, "bold"), background="#3a3a3a", foreground="white", relief="flat")
        style.map("Treeview", background=[('selected', COLORS["primary"][1])])

    def refresh_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

        df = self.dm.df_clients
        if df.empty: return

        keyword = self.entry_search.get().strip().lower()
        
        for _, row in df.iterrows():
            name = str(row.get("업체명", "")).lower()
            manager = str(row.get("담당자", "")).lower()
            
            if keyword and (keyword not in name and keyword not in manager):
                continue

            values = [row.get(col, "") for col in self.display_cols]
            self.tree.insert("", "end", values=values)

    def open_add_popup(self):
        self.pm.open_client_popup(client_name=None)

    def on_double_click(self, event):
        selected = self.tree.selection()
        if not selected: return
        
        item = self.tree.item(selected[0])
        values = item["values"]
        if values:
            client_name = values[0]
            self.pm.open_client_popup(client_name=client_name)