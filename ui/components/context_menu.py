import customtkinter as ctk
from src.styles import COLORS, FONTS

class ContextMenu(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.withdraw()
        self.overrideredirect(True)
        self.attributes("-topmost", True)
        
        self.frame = ctk.CTkFrame(self, fg_color=COLORS["bg_medium"], border_width=1, border_color=COLORS["border"])
        self.frame.pack(fill="both", expand=True)
        
        self.buttons = []
        
        # Click outside to close
        self.bind("<FocusOut>", lambda e: self.hide())
        
    def add_command(self, label, command):
        btn = ctk.CTkButton(
            self.frame, 
            text=label, 
            command=lambda: [command(), self.hide()],
            fg_color="transparent", 
            text_color=COLORS["text"],
            hover_color=COLORS["primary"],
            anchor="w",
            height=28,
            font=FONTS["main"]
        )
        btn.pack(fill="x", padx=2, pady=2)
        self.buttons.append(btn)
        
    def show(self, x, y):
        self.update_idletasks()
        width = 150
        height = len(self.buttons) * 32 + 4
        
        # Adjust position if menu goes off-screen (basic check)
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        if x + width > screen_width: x -= width
        if y + height > screen_height: y -= height
            
        self.geometry(f"{width}x{height}+{x}+{y}")
        self.deiconify()
        self.focus_set()
        
    def hide(self):
        self.withdraw()
        
    def clear(self):
        for btn in self.buttons:
            btn.destroy()
        self.buttons = []
