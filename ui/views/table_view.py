import tkinter as tk
from tkinter import ttk
from datetime import datetime
import customtkinter as ctk
import pandas as pd

# [변경] 경로 수정
from src.styles import COLORS, FONT_FAMILY, FONTS
from ui.components.context_menu import ContextMenu
from tkinter import messagebox

class MultiSelectDropdown(ctk.CTkFrame):
    def __init__(self, parent, values, default_values=None, command=None, width=200, height=30, dropdown_height=300, dropdown_width=200):
        super().__init__(parent, fg_color="transparent")
        self.values = values
        self.command = command
        self.vars = {}
        self.dropdown_height = dropdown_height
        self.dropdown_width = dropdown_width
        self.dropdown_window = None
        
        if default_values is None:
            default_values = values
        
        for val in values:
            self.vars[val] = ctk.BooleanVar(value=(val in default_values))
            
        self.btn_text = ctk.StringVar(value=self._get_button_text())
        self.button = ctk.CTkButton(self, textvariable=self.btn_text, command=self.toggle_dropdown, 
                                    width=width, height=height, fg_color=COLORS["bg_light"], text_color=COLORS["text"],
                                    hover_color=COLORS["bg_light_hover"], font=FONTS["main"])
        self.button.pack(fill="both", expand=True)
        
    def _get_button_text(self):
        selected_count = sum([v.get() for v in self.vars.values()])
        if selected_count == len(self.values):
            return "모든 상태 (All)"
        elif selected_count == 0:
            return "선택 안함"
        else:
            return f"{selected_count}개 상태 선택됨"

    def toggle_all(self):
        state = self.all_var.get()
        for var in self.vars.values():
            var.set(state)
        self.on_change()

    def toggle_dropdown(self):
        if self.dropdown_window and self.dropdown_window.winfo_exists():
            self.dropdown_window.destroy()
            self.dropdown_window = None
            return
            
        self.dropdown_window = ctk.CTkToplevel(self)
        self.dropdown_window.wm_overrideredirect(True)
        self.dropdown_window.attributes("-topmost", True)
        self.dropdown_window.attributes("-alpha", 0.95)
        
        x = self.button.winfo_rootx()
        y = self.button.winfo_rooty() + self.button.winfo_height() + 5
        self.dropdown_window.geometry(f"+{x}+{y}")
        
        frame = ctk.CTkFrame(self.dropdown_window, fg_color=COLORS["bg_medium"], border_width=1, border_color=COLORS["border"])
        frame.pack(fill="both", expand=True)
        
        scroll = ctk.CTkScrollableFrame(frame, width=self.dropdown_width, height=self.dropdown_height, fg_color="transparent")
        scroll.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Add "All" checkbox
        self.all_var = ctk.BooleanVar(value=all(v.get() for v in self.vars.values()))
        ctk.CTkCheckBox(scroll, text="All", variable=self.all_var, command=self.toggle_all,
                        font=FONTS["main_bold"], text_color=COLORS["text"]).pack(anchor="w", pady=(2, 5))
        
        for val in self.values:
            chk = ctk.CTkCheckBox(scroll, text=val, variable=self.vars[val], command=self.on_change,
                                  font=FONTS["main"], text_color=COLORS["text"])
            chk.pack(anchor="w", pady=2)
            
        ctk.CTkButton(frame, text="닫기", command=self.close_dropdown, height=25, 
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"]).pack(fill="x", padx=5, pady=5)
                      
        self.dropdown_window.bind("<FocusOut>", lambda e: self.close_dropdown() if str(e.widget) == str(self.dropdown_window) else None)

    def on_change(self):
        self.btn_text.set(self._get_button_text())
        if hasattr(self, 'all_var'):
             self.all_var.set(all(v.get() for v in self.vars.values()))
        if self.command:
            self.command()

    def close_dropdown(self):
        if self.dropdown_window:
            self.dropdown_window.destroy()
            self.dropdown_window = None
            
    def get_selected(self):
        return [val for val, var in self.vars.items() if var.get()]


class TableView(ctk.CTkFrame):
    def __init__(self, parent, data_manager, popup_manager):
        super().__init__(parent, fg_color="transparent")
        self.dm = data_manager
        self.pm = popup_manager
        
        self.all_statuses = [
            "견적", "주문", "생산중", "납품대기", 
            "납품완료/입금대기", "납품대기/입금완료", 
            "납품완료/입금완료", "종료","취소", "보류"
        ]
        
        self.default_statuses = [s for s in self.all_statuses if s not in ["종료", "취소","보류"]]
        
        self.sort_col = "출고예정일"
        self.sort_reverse = False
        
        self.context_menu = ContextMenu(self)
        
        self.create_widgets()
        self.refresh_data()

    def create_widgets(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        ctk.CTkLabel(header_frame, text="상태 필터:", font=FONTS["main_bold"], text_color=COLORS["text"]).pack(side="left", padx=(0, 10))
        
        self.status_filter = MultiSelectDropdown(
            header_frame, 
            values=self.all_statuses, 
            default_values=self.default_statuses,
            command=self.refresh_data,
            width=150,
            dropdown_height=280,
            dropdown_width=200
        )
        self.status_filter.pack(side="left", padx=5)
                
        ctk.CTkButton(header_frame, text="새로고침", command=self.refresh_data, width=80, 
                      fg_color=COLORS["bg_medium"], hover_color=COLORS["bg_light"], text_color=COLORS["text"], font=FONTS["main"]).pack(side="right")

        ctk.CTkButton(header_frame, text="검색", command=self.refresh_data, width=60, 
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"], font=FONTS["main"]).pack(side="right", padx=5)
        
        # Search Entry
        self.search_entry = ctk.CTkEntry(header_frame, placeholder_text="검색 (관리번호, 업체명, 모델명)", width=250, font=FONTS["main"])
        self.search_entry.pack(side="right", padx=5)
        self.search_entry.bind("<Return>", lambda e: self.refresh_data())

        style = ttk.Style()
        style.theme_use("default")
        
        mode = ctk.get_appearance_mode()
        bg_color = COLORS["bg_dark"][1] if mode == "Dark" else COLORS["bg_dark"][0]
        text_color = COLORS["text"][1] if mode == "Dark" else COLORS["text"][0]
        header_bg = COLORS["bg_medium"][1] if mode == "Dark" else COLORS["bg_medium"][0]
        
        style.configure("Treeview", 
                        background=bg_color, 
                        foreground=text_color, 
                        fieldbackground=bg_color,
                        rowheight=30,
                        font=(FONT_FAMILY, 11))
        
        style.configure("Treeview.Heading", 
                        background=header_bg, 
                        foreground=text_color, 
                        font=(FONT_FAMILY, 11, "bold"))
        
        style.map("Treeview", background=[("selected", COLORS["primary"][1] if mode == "Dark" else COLORS["primary"][0])], 
                  foreground=[("selected", "white")])
        
        table_frame = ctk.CTkFrame(self, fg_color="transparent")
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        columns = ("관리번호", "Status", "업체명", "모델명", "수량", "공급가액", "수주일", "출고예정일", "출고일")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="extended")
        
        col_widths = {
            "관리번호": 100, "Status": 80, "업체명": 120, "모델명": 150, 
            "수량": 60, "공급가액": 100, "수주일": 90, "출고예정일": 90, "출고일": 90
        }
        
        for col in columns:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_column(c))
            self.tree.column(col, width=col_widths.get(col, 100), anchor="center" if col in ["관리번호", "Status", "수량", "수주일", "출고예정일", "출고일"] else "w")
            if col == "공급가액":
                self.tree.column(col, anchor="e")
            
        scrollbar = ctk.CTkScrollbar(table_frame, orientation="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<Button-3>", self.on_right_click)

    def sort_column(self, col):
        if self.sort_col == col:
            self.sort_reverse = not self.sort_reverse
        else:
            self.sort_col = col
            self.sort_reverse = False
            
        # Update header text to show sort indicator
        for c in self.tree["columns"]:
            text = c
            if c == self.sort_col:
                text += " ▼" if self.sort_reverse else " ▲"
            self.tree.heading(c, text=text)
            
        self.refresh_data()

    def refresh_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        df = self.dm.df_data
        if df.empty: return
        
        selected_statuses = self.status_filter.get_selected()
        search_text = self.search_entry.get().lower().strip()
        
        filtered_rows = []
        for _, row in df.iterrows():
            # Status Filter
            status = str(row.get("Status", "")).strip()
            if status not in selected_statuses:
                continue
                
            # Search Filter
            if search_text:
                mgmt_no = str(row.get("관리번호", "")).lower()
                client = str(row.get("업체명", "")).lower()
                model = str(row.get("모델명", "")).lower()
                
                if (search_text not in mgmt_no and 
                    search_text not in client and 
                    search_text not in model):
                    continue
            
            filtered_rows.append(row)
        
        def sort_key(x):
            val = x.get(self.sort_col, "")
            
            # Numeric sort for Quantity and Price
            if self.sort_col in ["수량", "공급가액"]:
                try: return float(str(val).replace(",", ""))
                except: return 0
            
            # Date sort
            if "일" in self.sort_col or "Date" in self.sort_col:
                date_str = str(val).strip()
                if not date_str or date_str == "-":
                    return "9999-99-99" if not self.sort_reverse else "0000-00-00"
                return date_str
                
            return str(val)
            
        filtered_rows.sort(key=sort_key, reverse=self.sort_reverse)
        
        for row in filtered_rows:
            values = (
                row.get("관리번호", ""),
                row.get("Status", ""),
                row.get("업체명", ""),
                row.get("모델명", ""),
                row.get("수량", ""),
                row.get("공급가액", ""),
                row.get("수주일", ""),
                row.get("출고예정일", ""),
                row.get("출고일", "")
            )
            self.tree.insert("", "end", values=values)

    def on_double_click(self, event):
        item = self.tree.selection()
        if not item: return
        
        values = self.tree.item(item[0], "values")
        mgmt_no = values[0]
        status = values[1]  # Status is now at index 1
        
        if status == "납품완료/입금완료":
            self.pm.open_complete_popup(mgmt_no)
        elif str(mgmt_no).startswith("Q"):
            self.pm.open_quote_popup(mgmt_no)
        else:
            self.pm.open_order_popup(mgmt_no)

    def on_right_click(self, event):
        item = self.tree.identify_row(event.y)
        if not item: return
        
        self.tree.selection_set(item)
        values = self.tree.item(item, "values")
        mgmt_no = values[0]
        status = values[1] # Status is now at index 1
        
        self.context_menu.clear()
        
        if status == "견적":
            self.context_menu.add_command("견적 복사", lambda: self.pm.open_quote_popup(mgmt_no, copy_mode=True))
            self.context_menu.add_command("주문 전환", lambda: self.update_status(mgmt_no, "주문"))
            self.context_menu.add_command("대기 전환", lambda: self.update_status(mgmt_no, "보류"))
            self.context_menu.add_command("취소 전환", lambda: self.update_status(mgmt_no, "취소"))
            
        elif status == "주문":
            self.context_menu.add_command("주문 복사", lambda: self.pm.open_order_popup(mgmt_no, copy_mode=True))
            self.context_menu.add_command("생산 전환", lambda: self.update_status(mgmt_no, "생산중"))
            self.context_menu.add_command("대기 전환", lambda: self.update_status(mgmt_no, "보류"))
            self.context_menu.add_command("취소 전환", lambda: self.update_status(mgmt_no, "취소"))
            
        elif status == "생산중":
            self.context_menu.add_command("납품대기 전환", lambda: self.update_status(mgmt_no, "납품대기"))
            
        if self.context_menu.buttons:
            self.context_menu.show(event.x_root, event.y_root)

    def update_status(self, mgmt_no, new_status):
        success, msg = self.dm.update_order_status(mgmt_no, new_status)
        if success:
            self.refresh_data()
        else:
            messagebox.showerror("오류", msg)