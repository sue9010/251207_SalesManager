import tkinter as tk

import customtkinter as ctk
import pandas as pd

# [변경] 경로 수정
from src.styles import COLORS, FONT_FAMILY, FONTS


class KanbanView(ctk.CTkFrame):
    def __init__(self, parent, data_manager, popup_manager):
        super().__init__(parent, fg_color="transparent")
        self.dm = data_manager
        self.pm = popup_manager

        self.columns = {
            "견적": {"color": COLORS["text_dim"], "bg": COLORS["bg_dark"]},
            "주문": {"color": COLORS["primary"], "bg": COLORS["bg_dark"]},
            "생산중": {"color": COLORS["warning"], "bg": COLORS["bg_dark"]},
            "납품/입금": {"color": COLORS["success"], "bg": COLORS["bg_dark"]}, 
            "완료": {"color": COLORS["text"], "bg": COLORS["bg_dark"]}
        }
        
        self.column_frames = {}
        self.drag_data = {"item": None, "mgmt_no": None, "text": None, "window": None, "start_status": None}
        self.drag_started = False
        self.click_timer = None

        self.create_widgets()
        self.refresh_data()

    def destroy(self):
        if self.click_timer: self.after_cancel(self.click_timer)
        super().destroy()

    def create_widgets(self):
        toolbar = ctk.CTkFrame(self, height=50, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=(10, 0))
        ctk.CTkLabel(toolbar, text="📋 영업 파이프라인 (Kanban)", font=FONTS["title"]).pack(side="left")
        ctk.CTkButton(toolbar, text="새로고침", width=80, command=self.refresh_data, 
                      fg_color=COLORS["bg_medium"], hover_color=COLORS["bg_light"], text_color=COLORS["text"]).pack(side="right")

        self.board_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.board_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.board_frame.grid_rowconfigure(0, weight=1)

        for i, (status, style) in enumerate(self.columns.items()):
            self.board_frame.grid_columnconfigure(i, weight=1, uniform="col")
            col_container = ctk.CTkFrame(self.board_frame, fg_color=style["bg"], corner_radius=10, border_width=1, border_color=COLORS["border"])
            col_container.grid(row=0, column=i, sticky="nsew", padx=5, pady=5)
            col_container.status_tag = status
            header = ctk.CTkFrame(col_container, height=40, fg_color="transparent")
            header.pack(fill="x", padx=10, pady=5)
            ctk.CTkLabel(header, text="●", text_color=style["color"]).pack(side="left", padx=(0, 5))
            ctk.CTkLabel(header, text=status, font=FONTS["header"]).pack(side="left")
            count_badge = ctk.CTkLabel(header, text="0", width=24, height=24, fg_color=COLORS["bg_medium"], corner_radius=12)
            count_badge.pack(side="right")
            scroll = ctk.CTkScrollableFrame(col_container, fg_color="transparent")
            scroll.pack(fill="both", expand=True, padx=5, pady=5)
            self.column_frames[status] = {"frame": scroll, "badge": count_badge}

    def refresh_data(self):
        df = self.dm.df_data
        if df.empty: return
        for status in self.column_frames:
            for w in self.column_frames[status]["frame"].winfo_children(): w.destroy()
            self.column_frames[status]["badge"].configure(text="0")
            
        processing_statuses = ["납품완료/입금대기", "납품대기/입금완료", "납품대기"]
        
        # [변경] 관리번호 및 업체명 기준으로 그룹화
        if "관리번호" in df.columns and "업체명" in df.columns:
            grouped = df.groupby(["관리번호", "업체명"])
            
            for (mgmt_no, client_name), group in grouped:
                # 대표 상태 결정 (빈도수 기준)
                statuses = group["Status"].tolist()
                main_status = max(set(statuses), key=statuses.count)
                
                target_col = None
                if main_status in self.columns: target_col = main_status
                else:
                    for ps in processing_statuses:
                        if ps in main_status: target_col = "납품/입금"; break
                
                if target_col and target_col in self.column_frames:
                    # 카드 데이터 구성
                    try: total_amt = group["합계금액"].sum()
                    except: total_amt = 0
                    
                    item_count = len(group)
                    first_model = group.iloc[0].get("모델명", "")
                    
                    model_display = first_model
                    if item_count > 1:
                        model_display = f"{first_model} 외 {item_count-1}건"
                        
                    card_data = {
                        "mgmt_no": mgmt_no,
                        "client_name": client_name,
                        "model": model_display,
                        "total_amt": total_amt,
                        "status": main_status,
                        "item_count": item_count
                    }
                    self.create_card(target_col, card_data)
        
        for status in self.column_frames:
            cnt = len(self.column_frames[status]["frame"].winfo_children())
            self.column_frames[status]["badge"].configure(text=str(cnt))

    def create_card(self, col_name, data):
        parent = self.column_frames[col_name]["frame"]
        card = ctk.CTkFrame(parent, fg_color=COLORS["bg_medium"], corner_radius=6)
        card.pack(fill="x", pady=4, padx=2)
        
        comp = data["client_name"]
        model = data["model"]
        amt = data["total_amt"]
        
        try: amt_str = f"{float(amt):,.0f}"
        except: amt_str = str(amt)
        
        ctk.CTkLabel(card, text=comp, font=(FONT_FAMILY, 11, "bold"), text_color=COLORS["primary"]).pack(anchor="w", padx=8, pady=(5,0))
        ctk.CTkLabel(card, text=model, font=(FONT_FAMILY, 11)).pack(anchor="w", padx=8)
        ctk.CTkLabel(card, text=f"₩ {amt_str}", font=(FONT_FAMILY, 10), text_color=COLORS["text_dim"]).pack(anchor="e", padx=8, pady=(0,5))
        
        mgmt_no = data["mgmt_no"]
        status = data["status"]
        count_str = f" ({data['item_count']} items)" if data['item_count'] > 1 else ""
        drag_text = f"[{mgmt_no}] {comp}{count_str}"
        
        for w in [card] + card.winfo_children():
            w.bind("<Button-1>", lambda e, r=mgmt_no, s=col_name, t=drag_text, wi=card: self.start_drag(e, r, s, t, wi))
            w.bind("<B1-Motion>", self.do_drag)
            w.bind("<ButtonRelease-1>", self.stop_drag)
            
            w.bind("<Double-1>", lambda e, r=mgmt_no, s=status: self._on_card_double_click(r, s))

    def _on_card_double_click(self, mgmt_no, status):
        if status in ["완료", "취소", "보류"]:
            self.pm.open_complete_popup(mgmt_no)
            return

        if str(mgmt_no).startswith("Q") or status == "견적":
            self.pm.open_quote_popup(mgmt_no)
            return

        if status in ["수주", "주문", "주문 접수"]:
            self.pm.open_order_popup(mgmt_no)
            return

        if status in ["생산중", "납품대기", "납품대기/입금완료"]:
            self.pm.open_production_popup(mgmt_no)
            return

        if status == "납품완료/입금대기":
            self.pm.open_payment_popup(mgmt_no)
            return

        self.pm.open_order_popup(mgmt_no)

    def start_drag(self, event, mgmt_no, status, text, widget):
        self.drag_data.update({"item": widget, "mgmt_no": mgmt_no, "start_status": status, "text": text})
        self.drag_started = False
        if self.click_timer: self.after_cancel(self.click_timer)
        self.click_timer = self.after(150, lambda: self._start_drag_window(text))

    def _start_drag_window(self, text):
        self.drag_started = True
        if self.drag_data["window"] is None:
            self.drag_data["window"] = ctk.CTkToplevel(self)
            self.drag_data["window"].overrideredirect(True)
            self.drag_data["window"].attributes("-topmost", True)
            self.drag_data["window"].attributes("-alpha", 0.7)
            ctk.CTkLabel(self.drag_data["window"], text=text, fg_color=COLORS["primary"], text_color="white", corner_radius=5, padx=10, pady=5).pack()
        x, y = self.winfo_pointerxy()
        self.drag_data["window"].geometry(f"+{x+15}+{y+15}")

    def do_drag(self, event):
        if self.drag_started and self.drag_data["window"]:
            x, y = self.winfo_pointerxy()
            self.drag_data["window"].geometry(f"+{x+15}+{y+15}")

    def stop_drag(self, event):
        if self.click_timer:
            self.after_cancel(self.click_timer)
            self.click_timer = None

        if self.drag_started:
            if self.drag_data["window"]:
                self.drag_data["window"].destroy()
                self.drag_data["window"] = None
            
            x, y = self.winfo_pointerxy()
            target_widget = self.winfo_containing(x, y)
            target_col = self.find_target_column(target_widget)
            
            mgmt_no = self.drag_data["mgmt_no"]
            start_col = self.drag_data["start_status"]

            if target_col and target_col != start_col:
                new_status = target_col
                if target_col == "납품/입금": new_status = "납품대기"
                
                def update_logic(dfs):
                    mask = dfs["data"]["관리번호"] == mgmt_no
                    if mask.any():
                        dfs["data"].loc[mask, "Status"] = new_status
                        new_log = self.dm._create_log_entry(f"상태변경({new_status})", f"번호 [{mgmt_no}] - 칸반 이동")
                        dfs["log"] = pd.concat([dfs["log"], pd.DataFrame([new_log])], ignore_index=True)
                        return True, ""
                    return False, "데이터 없음"

                success, _ = self.dm._execute_transaction(update_logic)
                if success:
                    self.refresh_data()
        
        self.drag_started = False

    def find_target_column(self, widget):
        current = widget
        while current:
            if hasattr(current, "status_tag"): return current.status_tag
            try:
                current = current.master
                if current == self or current is None: break
            except: break
        return None