import customtkinter as ctk
from src.styles import COLORS, FONTS

class PlaceholderView(ctk.CTkFrame):
    def __init__(self, parent, title="준비 중"):
        super().__init__(parent, fg_color="transparent")
        
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.grid(row=0, column=0)
        
        ctk.CTkLabel(
            container, 
            text=title, 
            font=FONTS["title"], 
            text_color=COLORS["text"]
        ).pack(pady=(0, 20))
        
        ctk.CTkLabel(
            container, 
            text="현재 준비 중인 기능입니다.", 
            font=FONTS["main"], 
            text_color=COLORS["text_dim"]
        ).pack()
