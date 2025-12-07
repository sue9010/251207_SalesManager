import tkinter as tk
from datetime import datetime
from tkinter import messagebox, simpledialog, ttk
import pandas as pd

import customtkinter as ctk

# [변경] 경로 수정
from src.config import Config
from src.styles import COLORS, FONT_FAMILY, FONTS


class OrderView(ctk.CTkFrame):
    def __init__(self, parent, data_manager, popup_manager):
        super().__init__(parent, fg_color="transparent")
        self.dm = data_manager
        self.pm = popup_manager

        self.display_cols = ["관리번호", "업체명", "모델명", "수량", "합계금액", "수주일", "출고예정일", "Status"]
        
        self.create_widgets()
        self.style_treeview()
        self.refresh_data()


    def create_widgets(self):
        toolbar = ctk.CTkFrame(self, height=50, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=(20, 10))
        ctk.CTkLabel(toolbar, text="🛒 주문 관리 (수주)", font=FONTS["title"], text_color=COLORS["text"]).pack(side="left")
        self.entry_search = ctk.CTkEntry(toolbar, width=250, placeholder_text="관리번호, 업체명...")
        self.entry_search.pack(side="left", padx=(20, 10))
        self.entry_search.bind("<Return>", lambda e: self.refresh_data())
        ctk.CTkButton(toolbar, text="검색", width=60, command=self.refresh_data, fg_color=COLORS["bg_medium"], hover_color=COLORS["bg_light"], text_color=COLORS["text"]).pack(side="left")
        
        ctk.CTkButton(toolbar, text="+ 신규 주문", width=100, command=self.open_add_popup, fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"]).pack(side="right")
        
        ctk.CTkButton(toolbar, text="새로고침", width=80, command=self.refresh_data, fg_color=COLORS["bg_medium"], hover_color=COLORS["bg_light"], text_color=COLORS["text"]).pack(side="right", padx=(0, 10))

        tree_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_medium"], corner_radius=10)
        tree_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        scroll_y = ctk.CTkScrollbar(tree_frame, orientation="vertical")
        scroll_y.pack(side="right", fill="y", padx=(0, 5), pady=5)
        self.tree = ttk.Treeview(tree_frame, columns=self.display_cols, show="headings", yscrollcommand=scroll_y.set)
        self.tree.pack(fill="both", expand=True, padx=5, pady=5)
        scroll_y.configure(command=self.tree.yview)

        for col in self.display_cols:
            self.tree.heading(col, text=col)
            width = 100
            if col == "관리번호": width = 120
            if col == "업체명": width = 150
            if col == "모델명": width = 200
            self.tree.column(col, width=width, anchor="center")

        self.tree.bind("<Double-1>", self.on_double_click)
        self.tree.bind("<Button-3>", self.on_right_click)
        
        self.context_menu = tk.Menu(self, tearoff=0)
        self.context_menu.add_command(label="상세 정보 수정", command=self.on_edit)
        self.context_menu.add_command(label="📋 주문 복사", command=self.on_context_copy)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="📦 생산/준비 시작", command=self.on_start_production)
        self.context_menu.add_command(label="🚚 납품 대기 처리", command=self.on_ready_delivery)

    def style_treeview(self):
        style = ttk.Style()
        style.theme_use("default")
        bg = "#2b2b2b" if self.dm.current_theme == "Dark" else "#F5F5F5"
        fg = "white" if self.dm.current_theme == "Dark" else "black"
        style.configure("Treeview", background=bg, foreground=fg, fieldbackground=bg, rowheight=30, borderwidth=0, font=FONTS["main"])
        style.configure("Treeview.Heading", font=(FONT_FAMILY, 11, "bold"), background="#3a3a3a", foreground="white", relief="flat")
        style.map("Treeview", background=[('selected', COLORS["primary"][1])])

    def refresh_data(self):
        self.dm.sync_production_dates()
        
        for item in self.tree.get_children(): self.tree.delete(item)
        df = self.dm.df_data
        if df.empty: return
        
        keyword = self.entry_search.get().strip().lower()
        target_status = ["주문", "생산중"]
        target_df = df[df["Status"].isin(target_status)]
        
        if target_df.empty: return
        target_df = target_df.sort_values(by="수주일", ascending=False)
        
        for _, row in target_df.iterrows():
            if keyword:
                matched = False
                for col in Config.SEARCH_TARGET_COLS:
                    if keyword in str(row.get(col, "")).lower():
                        matched = True; break
                if not matched: continue
            try:
                amt = float(str(row.get("합계금액", 0)).replace(",",""))
                fmt_amt = f"{amt:,.0f}"
            except: fmt_amt = str(row.get("합계금액", "-"))
            
            values = [
                row.get("관리번호"), 
                row.get("업체명"), 
                row.get("모델명"), 
                row.get("수량"), 
                fmt_amt, 
                row.get("수주일"), 
                row.get("출고예정일"),
                row.get("Status")
            ]
            self.tree.insert("", "end", values=values)

    def open_add_popup(self): 
        self.pm.open_order_popup(None)
        
    def on_double_click(self, event): self.on_edit()
    def on_right_click(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def on_edit(self):
        selected = self.tree.selection()
        if not selected: return
        item = self.tree.item(selected[0])
        mgmt_no = item["values"][0]
        self.pm.open_order_popup(mgmt_no)

    def on_context_copy(self):
        selected = self.tree.selection()
        if not selected: return
        item = self.tree.item(selected[0])
        mgmt_no = item["values"][0]
        self.pm.open_order_popup(mgmt_no, copy_mode=True)

    def on_start_production(self):
        self._update_status("생산중", "생산/준비 단계로 변경되었습니다.")

    def on_ready_delivery(self):
        self._update_status("납품대기", "납품 대기 상태로 변경되었습니다.\n'납품 관리' 메뉴에서 확인 가능합니다.")

    def _update_status(self, new_status, success_msg):
        selected = self.tree.selection()
        if not selected: return
        
        item = self.tree.item(selected[0])
        mgmt_no = item["values"][0]
        
        if messagebox.askyesno("상태 변경", f"관리번호 [{mgmt_no}] 및 관련 항목들의 상태를 '{new_status}'(으)로 변경하시겠습니까?"):
            
            if new_status == "생산중":
                df = self.dm.df_data
                mask = df["관리번호"] == mgmt_no
                if mask.any():
                    target_rows = df.loc[mask].to_dict('records')
                    export_success, export_msg = self.dm.export_to_production_request(target_rows)
                    
                    if export_success:
                        success_msg += f"\n\n[생산팀 전달 성공]\n{export_msg}"
                    else:
                        if not messagebox.askyesno("전송 실패", f"생산팀 요청 파일 전송에 실패했습니다.\n사유: {export_msg}\n\n계속 진행하시겠습니까? (상태만 변경됨)"):
                            return

            def update_logic(dfs):
                mask = dfs["data"]["관리번호"] == mgmt_no
                if mask.any():
                    if new_status == "생산중":
                        dfs["data"].loc[mask, "출고예정일"] = "-"
                    
                    dfs["data"].loc[mask, "Status"] = new_status
                    
                    new_log = self.dm._create_log_entry(f"상태변경({new_status})", f"번호 [{mgmt_no}] - 일괄 처리")
                    dfs["log"] = pd.concat([dfs["log"], pd.DataFrame([new_log])], ignore_index=True)
                    return True, ""
                return False, "데이터를 찾을 수 없습니다."

            success, msg = self.dm._execute_transaction(update_logic)
            if success:
                messagebox.showinfo("완료", success_msg)
                self.refresh_data()
            else:
                messagebox.showerror("오류", f"데이터 저장에 실패했습니다.\n{msg}")