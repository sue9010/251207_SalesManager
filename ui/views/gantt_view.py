import tkinter as tk

import customtkinter as ctk
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# [변경] 경로 수정
from src.styles import COLORS, FONT_FAMILY, FONTS, get_color_str


class GanttView(ctk.CTkFrame):
    def __init__(self, parent, data_manager, popup_manager):
        super().__init__(parent, fg_color="transparent")
        self.dm = data_manager
        self.pm = popup_manager

        plt.rcParams['font.family'] = FONT_FAMILY
        plt.rcParams['axes.unicode_minus'] = False

        self.create_widgets()
        self.refresh_data()

    def create_widgets(self):
        toolbar = ctk.CTkFrame(self, height=50, fg_color="transparent")
        toolbar.pack(fill="x", padx=20, pady=(10, 0))
        ctk.CTkLabel(toolbar, text="📈 프로젝트 일정 (Gantt)", font=FONTS["title"]).pack(side="left")
        ctk.CTkButton(toolbar, text="새로고침", width=80, command=self.refresh_data, 
                      fg_color=COLORS["bg_medium"], hover_color=COLORS["bg_light"], text_color=COLORS["text"]).pack(side="right")

        self.chart_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_dark"], corner_radius=10)
        self.chart_frame.pack(fill="both", expand=True, padx=10, pady=10)
        self.canvas = None

    def refresh_data(self):
        if self.canvas:
            self.canvas.get_tk_widget().destroy()
            self.canvas = None

        df = self.dm.df_data
        if df.empty: return

        df['start'] = pd.to_datetime(df['수주일'], errors='coerce', format='mixed')
        df['start'] = df['start'].fillna(pd.to_datetime(df['견적일'], errors='coerce', format='mixed'))
        
        df['end'] = pd.to_datetime(df['출고예정일'], errors='coerce', format='mixed')
        
        mask = df['start'].notna() & (~df['Status'].isin(['완료', '취소', '보류']))
        target_df = df[mask].copy()
        
        if target_df.empty: return
        
        mask_no_end = target_df['end'].isna()
        target_df.loc[mask_no_end, 'end'] = target_df.loc[mask_no_end, 'start'] + pd.Timedelta(days=3)
        
        target_df['duration'] = (target_df['end'] - target_df['start']).dt.days
        target_df.loc[target_df['duration'] < 1, 'duration'] = 1 
        
        target_df = target_df.sort_values(by='start')

        self.draw_chart(target_df)

    def draw_chart(self, df):
        bg_color = get_color_str("bg_dark")
        text_color = get_color_str("text")
        
        labels = [f"[{row['업체명']}] {row['모델명']}" for _, row in df.iterrows()]
        starts = mdates.date2num(df['start'])
        durations = df['duration'].tolist()
        
        height = max(4, len(df) * 0.5)
        fig, ax = plt.subplots(figsize=(10, height), dpi=100)
        fig.patch.set_facecolor(bg_color)
        ax.set_facecolor(bg_color)
        
        y_pos = range(len(labels))
        bars = ax.barh(y_pos, durations, left=starts, height=0.5, align='center', color=get_color_str("primary"))
        
        ax.set_yticks(y_pos)
        ax.set_yticklabels(labels, color=text_color)
        ax.xaxis_date()
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        ax.tick_params(axis='x', colors=text_color)
        ax.spines['bottom'].set_color(text_color)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['left'].set_visible(False)
        ax.grid(True, axis='x', linestyle='--', alpha=0.3)

        plt.tight_layout()

        self.canvas = FigureCanvasTkAgg(fig, master=self.chart_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill="both", expand=True)