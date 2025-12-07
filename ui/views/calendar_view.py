import tkinter as tk
from datetime import datetime, timedelta
from tkinter import messagebox

import customtkinter as ctk
import pandas as pd

from src.styles import COLORS, FONT_FAMILY, FONTS


class CalendarView(ctk.CTkFrame):
    def __init__(self, parent, data_manager, popup_manager):
        super().__init__(parent, fg_color="transparent")
        self.dm = data_manager
        self.pm = popup_manager

        self.base_date = datetime.now()

        # 드래그 앤 드롭 상태 저장
        self.drag_data = {
            "item": None, "mgmt_no": None, "text": None, "window": None, "origin_date": None
        }
        self.click_timer = None
        self.drag_started = False

        self.create_widgets()
        self.refresh_data()

    def destroy(self):
        if self.click_timer:
            self.after_cancel(self.click_timer)
            self.click_timer = None
        super().destroy()

    def create_widgets(self):
        # 상단 헤더 (날짜 이동)
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(pady=(10, 10), padx=10, fill="x", side="top")

        self.btn_prev = ctk.CTkButton(
            header_frame, text="< 이전 4주", command=self.prev_weeks, 
            fg_color=COLORS["bg_medium"], hover_color=COLORS["bg_light"], width=100, height=32,
            font=FONTS["main"], text_color=COLORS["text"]
        )
        self.btn_prev.pack(side="left")
        
        self.period_label = ctk.CTkLabel(header_frame, text="", font=FONTS["title"], text_color=COLORS["text"])
        self.period_label.pack(side="left", expand=True)
        
        self.btn_next = ctk.CTkButton(
            header_frame, text="다음 4주 >", command=self.next_weeks, 
            fg_color=COLORS["bg_medium"], hover_color=COLORS["bg_light"], width=100, height=32,
            font=FONTS["main"], text_color=COLORS["text"]
        )
        self.btn_next.pack(side="right")

        ctk.CTkButton(
            header_frame, text="🔄 새로고침", width=80, height=32,
            fg_color=COLORS["bg_medium"], hover_color=COLORS["bg_light"], 
            command=self.refresh_data, font=FONTS["main"], text_color=COLORS["text"]
        ).pack(side="right", padx=(0, 10))

        # 메인 컨텐츠 (달력 + 사이드바)
        content_container = ctk.CTkFrame(self, fg_color="transparent")
        content_container.pack(expand=True, fill="both", padx=5, pady=(0, 10))

        content_container.grid_columnconfigure(0, weight=1) 
        content_container.grid_columnconfigure(1, weight=0, minsize=300) 
        content_container.grid_rowconfigure(0, weight=1)

        # 달력 프레임
        self.calendar_frame = ctk.CTkFrame(content_container, fg_color=COLORS["bg_dark"], corner_radius=10)
        self.calendar_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 10))

        # 우측 사이드바 (일정 미정 목록 등)
        self.sidebar_frame = ctk.CTkFrame(content_container, width=300, fg_color=COLORS["bg_dark"], corner_radius=10)
        self.sidebar_frame.grid(row=0, column=1, sticky="nsew")
        self.sidebar_frame.grid_propagate(False)

        ctk.CTkLabel(self.sidebar_frame, text="📅 일정 미정 (납품대기)", font=FONTS["header"], text_color=COLORS["warning"]).pack(pady=(15, 5), padx=15, anchor="w")
        self.unscheduled_scroll = ctk.CTkScrollableFrame(self.sidebar_frame, fg_color=COLORS["bg_medium"], corner_radius=6)
        self.unscheduled_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def refresh_data(self):
        self.update_calendar()
        self.update_sidebar()

    def update_sidebar(self):
        for widget in self.unscheduled_scroll.winfo_children(): widget.destroy()

        df = self.dm.df_data
        if df.empty: return

        # 조건: '납품대기'가 포함된 상태이면서, 출고예정일이 없거나(-)인 경우
        # 또는 단순히 날짜가 미정인 '주문/생산중' 건도 포함 가능
        target_status = ["주문", "생산중", "납품대기"]
        
        # 출고예정일이 '-' 이거나 비어있는 데이터
        mask_date = (df['출고예정일'] == '-') | (df['출고예정일'] == '') | (df['출고예정일'].isna())
        mask_status = df['Status'].apply(lambda x: any(s in str(x) for s in target_status))
        
        target_df = df[mask_date & mask_status].copy()
        
        if target_df.empty:
            ctk.CTkLabel(self.unscheduled_scroll, text="데이터 없음", text_color=COLORS["text_dim"]).pack(pady=10)
            return

        for _, row in target_df.iterrows():
            self._create_sidebar_item(row)

    def _create_sidebar_item(self, row):
        card = ctk.CTkFrame(self.unscheduled_scroll, fg_color=COLORS["bg_dark"], corner_radius=5)
        card.pack(fill="x", pady=3, padx=5)
        
        mgmt_no = row['관리번호']
        title = f"[{row['업체명']}] {row['모델명']}"
        info = f"{row['수량']}개 | {row['Status']}"
        
        ctk.CTkLabel(card, text=title, font=(FONT_FAMILY, 11, "bold"), anchor="w").pack(fill="x", padx=5, pady=(5,0))
        ctk.CTkLabel(card, text=info, font=(FONT_FAMILY, 10), text_color=COLORS["text_dim"], anchor="w").pack(fill="x", padx=5, pady=(0,5))
        
        # 드래그 이벤트 연결
        drag_text = f"[{mgmt_no}] {row['업체명']}"
        for w in [card] + card.winfo_children():
            w.bind("<Button-1>", lambda e, r=mgmt_no, d=None, t=drag_text, w=card: self.start_drag(e, r, d, t, w))
            w.bind("<B1-Motion>", self.do_drag)
            w.bind("<ButtonRelease-1>", self.stop_drag)

    def update_calendar(self):
        for widget in self.calendar_frame.winfo_children(): widget.destroy()

        # 달력 날짜 계산 (4주)
        offset = (self.base_date.weekday() + 1) % 7
        start_date = self.base_date - timedelta(days=offset)
        calendar_days = [start_date + timedelta(days=i) for i in range(35)] # 5주 표시
        end_date = calendar_days[-1]

        self.period_label.configure(text=f"{start_date.strftime('%Y.%m.%d')} ~ {end_date.strftime('%Y.%m.%d')}")

        # 요일 헤더
        days_header = ["일", "월", "화", "수", "목", "금", "토"]
        for i, day in enumerate(days_header):
            color = COLORS["danger"] if i == 0 else (COLORS["primary"] if i == 6 else COLORS["text"])
            ctk.CTkLabel(self.calendar_frame, text=day, font=FONTS["main_bold"], text_color=color).grid(row=0, column=i, sticky="nsew", pady=5)

        for i in range(7): self.calendar_frame.grid_columnconfigure(i, weight=1, uniform="days")

        # 데이터 매핑
        df = self.dm.df_data
        events = {}
        if not df.empty:
            s_str = start_date.strftime("%Y-%m-%d")
            e_str = end_date.strftime("%Y-%m-%d")
            
            # 출고예정일이 범위 내에 있는 데이터
            mask = (df['출고예정일'] >= s_str) & (df['출고예정일'] <= e_str) & (df['출고예정일'] != '-')
            # 완료/취소 제외
            mask_status = ~df['Status'].isin(['완료', '취소', '보류'])
            
            target_df = df[mask & mask_status]
            
            for _, row in target_df.iterrows():
                d_str = row['출고예정일']
                if d_str not in events: events[d_str] = []
                events[d_str].append(row)

        # 달력 셀 그리기
        for i, curr_date in enumerate(calendar_days):
            r, c = (i // 7) + 1, i % 7
            self.calendar_frame.grid_rowconfigure(r, weight=1, uniform="weeks")
            
            cell = ctk.CTkFrame(self.calendar_frame, fg_color=COLORS["bg_medium"], border_width=1, border_color=COLORS["border"])
            cell.grid(row=r, column=c, sticky="nsew", padx=1, pady=1)
            
            date_str = curr_date.strftime("%Y-%m-%d")
            cell.target_date = date_str # 드래그 타겟용 속성
            
            # 오늘 날짜 강조
            if date_str == datetime.now().strftime("%Y-%m-%d"):
                cell.configure(border_color=COLORS["primary"], border_width=2)

            # 날짜 표시
            day_color = COLORS["danger"] if c == 0 else (COLORS["primary"] if c == 6 else COLORS["text"])
            if curr_date.month != self.base_date.month: day_color = COLORS["text_dim"] # 다른 달 날짜 흐리게
            
            day_lbl = ctk.CTkLabel(cell, text=str(curr_date.day), font=FONTS["small"], text_color=day_color)
            day_lbl.pack(anchor="nw", padx=5, pady=2)

            # 이벤트 표시 (스크롤 가능)
            if date_str in events:
                scroll = ctk.CTkScrollableFrame(cell, fg_color="transparent")
                scroll.pack(fill="both", expand=True, padx=2, pady=2)
                # 스크롤바 숨기기 Hack (필요시)
                
                for row in events[date_str]:
                    mgmt_no = row['관리번호']
                    comp = row['업체명']
                    txt = f"[{comp}] {row['모델명']}"
                    
                    lbl = ctk.CTkLabel(scroll, text=txt, font=(FONT_FAMILY, 10), anchor="w", fg_color=COLORS["bg_dark"], corner_radius=4)
                    lbl.pack(fill="x", pady=1)
                    
                    drag_text = f"[{mgmt_no}] {comp}"
                    lbl.bind("<Button-1>", lambda e, r=mgmt_no, d=date_str, t=drag_text, w=lbl: self.start_drag(e, r, d, t, w))
                    lbl.bind("<B1-Motion>", self.do_drag)
                    lbl.bind("<ButtonRelease-1>", self.stop_drag)
                    # 더블클릭 시 상세 (견적 팝업)
                    lbl.bind("<Double-1>", lambda e, r=mgmt_no: self.pm.open_quote_popup(r))

    # --- 드래그 앤 드롭 로직 (간소화) ---
    def _start_drag_window(self, text):
        self.drag_started = True
        if self.drag_data["window"] is None:
            self.drag_data["window"] = ctk.CTkToplevel(self)
            self.drag_data["window"].overrideredirect(True)
            self.drag_data["window"].attributes("-topmost", True)
            self.drag_data["window"].attributes("-alpha", 0.7)
            
            lbl = ctk.CTkLabel(self.drag_data["window"], text=text, fg_color=COLORS["primary"], text_color="white", corner_radius=5, padx=8, pady=4)
            lbl.pack()
            
        x, y = self.winfo_pointerxy()
        self.drag_data["window"].geometry(f"+{x+15}+{y+15}")

    def start_drag(self, event, mgmt_no, origin_date, text, widget):
        self.drag_data.update({"item": widget, "mgmt_no": mgmt_no, "origin_date": origin_date, "text": text})
        self.drag_started = False
        if self.click_timer: self.after_cancel(self.click_timer)
        self.click_timer = self.after(200, lambda: self._start_drag_window(text))

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
            
            # 드롭 위치 확인
            x, y = self.winfo_pointerxy()
            target_widget = self.winfo_containing(x, y)
            target_date = self.find_target_date(target_widget)
            
            mgmt_no = self.drag_data["mgmt_no"]
            origin_date = self.drag_data["origin_date"]

            if target_date and mgmt_no and target_date != origin_date:
                # 날짜 업데이트
                df = self.dm.df_data
                mask = df["관리번호"] == mgmt_no
                if mask.any():
                    self.dm.df_data.loc[mask, "출고예정일"] = target_date
                    # 사이드바에서 드래그했다면 상태 변경 (납품대기 -> 생산중 등) 고려 가능하나 여기선 날짜만
                    self.dm.save_to_excel()
                    self.refresh_data()
        
        self.drag_started = False

    def find_target_date(self, widget):
        current = widget
        while current:
            if hasattr(current, "target_date"): return current.target_date
            try:
                current = current.master
                if current == self or current is None: break
            except: break
        return None

    def prev_weeks(self):
        self.base_date -= timedelta(weeks=4)
        self.refresh_data()

    def next_weeks(self):
        self.base_date += timedelta(weeks=4)
        self.refresh_data()
