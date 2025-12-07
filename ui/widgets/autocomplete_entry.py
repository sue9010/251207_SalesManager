import tkinter as tk
import customtkinter as ctk

# [변경] 스타일 경로 수정
from src.styles import COLORS, FONT_FAMILY

class AutocompleteEntry(ctk.CTkEntry):
    """
    입력 시 자동완성 리스트를 보여주는 CTkEntry 위젯
    """
    def __init__(self, master, completevalues=None, command=None, on_focus_out=None, **kwargs):
        super().__init__(master, **kwargs)
        self.completevalues = completevalues or []
        self.command = command
        self.on_focus_out = on_focus_out
        self.listbox_window = None
        self.listbox = None
        
        self.bind("<KeyRelease>", self._on_key_release)
        self.bind("<Down>", self._on_down)
        self.bind("<FocusOut>", self._on_focus_out)

    def update_values(self, values):
        self.completevalues = values
        
    def set_value(self, value):
        self.delete(0, "end")
        self.insert(0, value)

    def set_completion_list(self, values):
        self.completevalues = values

    def _on_key_release(self, event):
        if event.keysym in ["Up", "Down", "Return", "Escape", "Tab"]: return
        self._update_listbox()

    def _update_listbox(self):
        typed = self.get()
        if not typed:
            data = self.completevalues
        else:
            data = [v for v in self.completevalues if typed.lower() in v.lower()]
            
        if not data:
            self._close_listbox()
            return
            
        if self.listbox_window is None:
            self.listbox_window = tk.Toplevel(self)
            self.listbox_window.wm_overrideredirect(True)
            self.listbox_window.attributes("-topmost", True)
            
            self.listbox = tk.Listbox(
                self.listbox_window, 
                font=(FONT_FAMILY, 11), 
                height=min(len(data), 8), 
                selectmode="browse",
                bg=COLORS["bg_medium"][1] if ctk.get_appearance_mode() == "Dark" else COLORS["bg_medium"][0],
                fg=COLORS["text"][1] if ctk.get_appearance_mode() == "Dark" else COLORS["text"][0],
                selectbackground=COLORS["primary"][1] if ctk.get_appearance_mode() == "Dark" else COLORS["primary"][0],
                selectforeground="white",
                relief="flat",
                borderwidth=1
            )
            self.listbox.pack(fill="both", expand=True)
            
            self.listbox.bind("<ButtonRelease-1>", self._on_select)
            self.listbox.bind("<Return>", self._on_select)
            self.listbox.bind("<Tab>", self._on_select)
            self.listbox.bind("<Right>", self._on_select)
            self.listbox.bind("<Escape>", lambda e: self._close_listbox())
            
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height() + 2
        w = self.winfo_width()
        
        h = min(len(data), 8) * 22 
        self.listbox_window.geometry(f"{w}x{h}+{x}+{y}")
        
        self.listbox.delete(0, "end")
        for item in data:
            self.listbox.insert("end", item)

    def _on_down(self, event):
        if self.listbox_window:
            self.listbox.focus_set()
            self.listbox.selection_set(0)
            
    def _on_select(self, event):
        if not self.listbox: return
        try:
            selection = self.listbox.curselection()
            if selection:
                value = self.listbox.get(selection[0])
                self.delete(0, "end")
                self.insert(0, value)
                self._close_listbox()
                self.focus_set() # Return focus to entry
                if self.command:
                    self.command(value)
        except: pass
        
    def _close_listbox(self):
        if self.listbox_window:
            self.listbox_window.destroy()
            self.listbox_window = None
            self.listbox = None
            
    def _on_focus_out(self, event):
        self.after(150, self._check_focus)
        
    def _check_focus(self):
        try:
            focus_widget = self.winfo_toplevel().focus_get()
            if self.listbox and focus_widget == self.listbox:
                return
            if focus_widget == self:
                return
            self._close_listbox()
            if self.on_focus_out:
                self.on_focus_out(self.get())
        except:
            self._close_listbox()