import tkinter as tk
from tkinter import ttk
from datetime import datetime
import customtkinter as ctk
import pandas as pd
from tkinter import messagebox

from src.styles import COLORS, FONT_FAMILY, FONTS
from ui.components.context_menu import ContextMenu

# Dropdown 클래스는 필요 시 공통 모듈로 분리 권장 (여기서는 포함 유지)
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

# -----------------------------------------------------------
# [중요] PurchaseTableView 클래스
# -----------------------------------------------------------
class PurchaseTableView(ctk.CTkFrame):
    def __init__(self, parent, data_manager, popup_manager):
        super().__init__(parent, fg_color="transparent")
        self.dm = data_manager
        self.pm = popup_manager
        
        # 구매 관리용 상태
        self.all_statuses = [
            "발주", "입고대기", "입고중", "입고완료/지급대기", 
            "입고완료/지급완료", "종료", "취소", "보류"
        ]
        
        self.default_statuses = [s for s in self.all_statuses if s not in ["종료", "취소", "보류"]]
        
        self.sort_col = "발주일"
        self.sort_reverse = True
        
        self.context_menu = ContextMenu(self)
        
        self.create_widgets()
        self.refresh_data()

    def create_widgets(self):
        # [수정] 상단바: 검색과 필터만 포함 (타이틀/메인버튼 제외)
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=(10, 10))
        
        # 보기 모드 (품목별/발주별)
        self.view_mode_var = ctk.StringVar(value="품목별")
        self.view_filter = ctk.CTkSegmentedButton(
            header_frame,
            values=["품목별", "발주별"],
            variable=self.view_mode_var,
            command=lambda x: self.refresh_data(),
            width=150,
            font=FONTS["main_bold"]
        )
        self.view_filter.pack(side="left", padx=(0, 10)) 

        # 상태 필터
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
                
        # 새로고침 / 검색 버튼
        ctk.CTkButton(header_frame, text="새로고침", command=self.refresh_data, width=80, 
                      fg_color=COLORS["bg_medium"], hover_color=COLORS["bg_light"], text_color=COLORS["text"], font=FONTS["main"]).pack(side="right")

        ctk.CTkButton(header_frame, text="검색", command=self.refresh_data, width=60, 
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"], font=FONTS["main"]).pack(side="right", padx=5)
        
        # 검색어 입력
        self.search_entry = ctk.CTkEntry(header_frame, placeholder_text="검색 (발주번호, 매입처, 모델명)", width=250, font=FONTS["main"])
        self.search_entry.pack(side="right", padx=5)
        self.search_entry.bind("<Return>", lambda e: self.refresh_data())

        # Treeview 스타일
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
        
        # 테이블 영역
        table_frame = ctk.CTkFrame(self, fg_color="transparent")
        table_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        columns = ("관리번호", "Status", "업체명", "모델명", "수량", "공급가액", "발주일", "입고예정일", "입고일")
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", selectmode="extended")
        
        col_widths = {
            "관리번호": 100, "Status": 80, "업체명": 120, "모델명": 150, 
            "수량": 60, "공급가액": 100, "발주일": 90, "입고예정일": 90, "입고일": 90
        }
        
        for col in columns:
            self.tree.heading(col, text=col, command=lambda c=col: self.sort_column(c))
            self.tree.column(col, width=col_widths.get(col, 100), anchor="center" if col in ["관리번호","업체명","모델명", "Status", "수량", "발주일", "입고예정일", "입고일"] else "w")
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
            
        for c in self.tree["columns"]:
            text = c
            if c == self.sort_col:
                text += " ▼" if self.sort_reverse else " ▲"
            self.tree.heading(c, text=text)
            
        self.refresh_data()

    def refresh_data(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        # [중요] df_purchase 데이터 사용
        df = self.dm.df_purchase
        if df is None or df.empty: return
        
        selected_statuses = self.status_filter.get_selected()
        search_text = self.search_entry.get().lower().strip()
        view_mode = self.view_mode_var.get()
        
        filtered_rows = []
        
        for _, row in df.iterrows():
            status = str(row.get("Status", "")).strip()
            # 필터링
            if status not in selected_statuses and "All" not in selected_statuses:
                if not (len(selected_statuses) == len(self.all_statuses)):
                     if status not in selected_statuses: continue

            if search_text:
                mgmt_no = str(row.get("관리번호", "")).lower()
                client = str(row.get("업체명", "")).lower()
                model = str(row.get("모델명", "")).lower()
                
                if (search_text not in mgmt_no and 
                    search_text not in client and 
                    search_text not in model):
                    continue
            
            filtered_rows.append(row)

        if view_mode == "발주별":
            grouped_data = {}
            for row in filtered_rows:
                mgmt_no = row.get("관리번호", "")
                if mgmt_no not in grouped_data:
                    grouped_data[mgmt_no] = []
                grouped_data[mgmt_no].append(row)
            
            aggregated_rows = []
            for mgmt_no, items in grouped_data.items():
                if not items: continue
                base_item = items[0]
                new_row = base_item.copy()
                
                if len(items) > 1:
                    first_model = str(base_item.get("모델명", ""))
                    new_row["모델명"] = f"{first_model} 외 {len(items)-1}건"
                    try:
                        total_qty = sum(float(str(item.get("수량", "0")).replace(",", "") or 0) for item in items)
                        new_row["수량"] = f"{int(total_qty):,}"
                        
                        total_price = sum(float(str(item.get("공급가액", "0")).replace(",", "") or 0) for item in items)
                        new_row["공급가액"] = f"{total_price:,.0f}"
                    except: pass
                
                aggregated_rows.append(new_row)
            filtered_rows = aggregated_rows

        def sort_key(x):
            val = x.get(self.sort_col, "")
            if self.sort_col in ["수량", "공급가액"]:
                try: return float(str(val).replace(",", ""))
                except: return 0
            if "일" in self.sort_col:
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
                row.get("발주일", ""),
                row.get("입고예정일", ""),
                row.get("입고일", "")
            )
            self.tree.insert("", "end", values=values)

    def on_double_click(self, event):
        item = self.tree.selection()
        if not item: return
        
        values = self.tree.item(item[0], "values")
        mgmt_no = values[0]
        # 구매 팝업 호출
        self.pm.open_purchase_popup(mgmt_no=mgmt_no)

    def on_right_click(self, event):
        item = self.tree.identify_row(event.y)
        if not item: return
        
        self.tree.selection_set(item)
        values = self.tree.item(item, "values")
        mgmt_no = values[0]
        status = values[1]
        
        self.context_menu.clear()
        
        if status == "발주":
            self.context_menu.add_command("발주 복사", lambda: self.pm.open_purchase_popup(mgmt_no=mgmt_no, copy_mode=True))
            self.context_menu.add_command("취소 전환", lambda: self.update_status(mgmt_no, "취소"))

        # 필요 시 다른 상태 메뉴 추가
            
        if self.context_menu.buttons:
            self.context_menu.show(event.x_root, event.y_root)

    def update_status(self, mgmt_no, new_status):
        messagebox.showinfo("알림", f"상태 변경({new_status})은 추후 DB 연동 후 구현됩니다.")