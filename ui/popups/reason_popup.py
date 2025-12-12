import customtkinter as ctk
from src.styles import COLORS, FONTS

class ReasonPopup(ctk.CTkToplevel):
    def __init__(self, parent, title, callback):
        super().__init__(parent)
        self.callback = callback
        self.title(title)
        self.geometry("400x250")
        self.resizable(False, False)
        
        self.transient(parent)
        self.grab_set()
        
        self._create_widgets()
        self.center_window()

    def _create_widgets(self):
        # Main Frame
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Label
        ctk.CTkLabel(main_frame, text="사유를 입력해주세요:", font=FONTS["main_bold"]).pack(anchor="w", pady=(0, 10))
        
        # Text Entry
        self.txt_reason = ctk.CTkTextbox(main_frame, height=100)
        self.txt_reason.pack(fill="x", pady=(0, 20))
        self.txt_reason.focus_set()
        
        # Buttons
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", side="bottom")
        
        ctk.CTkButton(btn_frame, text="확인", command=self.on_confirm, width=100,
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"]).pack(side="right", padx=(10, 0))
                      
        ctk.CTkButton(btn_frame, text="취소", command=self.destroy, width=100,
                      fg_color=COLORS["bg_light"], hover_color=COLORS["bg_light_hover"], text_color=COLORS["text"]).pack(side="right")

    def on_confirm(self):
        reason = self.txt_reason.get("1.0", "end-1c").strip()
        if not reason:
            return # 빈 값 방지 (선택 사항)
            
        if self.callback:
            self.callback(reason)
        self.destroy()

    def center_window(self):
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'{width}x{height}+{x}+{y}')
