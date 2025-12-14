import tkinter as tk
from datetime import datetime
from tkinter import messagebox
import customtkinter as ctk

from src.styles import COLORS, FONTS
from utils.file_dnd import FileDnDManager

class MiniOrderPopup(ctk.CTkToplevel):
    def __init__(self, parent, data_manager, mgmt_no, on_confirm_callback):
        super().__init__(parent)
        self.dm = data_manager
        self.mgmt_no = mgmt_no
        self.on_confirm_callback = on_confirm_callback
        
        self.title("주문 확정")
        self.geometry("500x480")
        self.configure(fg_color=COLORS["bg_dark"])
        
        self.file_manager = FileDnDManager(self)
        
        self.transient(parent)
        self.grab_set()
        
        self._create_widgets()
        
        self.after(100, lambda: self.entry_po_no.focus_set())
    def _create_widgets(self):
        # Header
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=20, pady=20)
        ctk.CTkLabel(header_frame, text="주문 확정 정보 입력", font=FONTS["header"]).pack(side="left")
        
        # Content
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=20)
        
        # 1. 수주일 (Default Today)
        self.entry_order_date = self._create_input_row(content_frame, "수주일", placeholder="YYYY-MM-DD")
        self.entry_order_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        # 2. 발주서번호
        self.entry_po_no = self._create_input_row(content_frame, "발주서번호")
        
        # 3. 주문요청사항 (Multiline)
        ctk.CTkLabel(content_frame, text="주문요청사항", font=FONTS["main"], text_color=COLORS["text_dim"]).pack(anchor="w", pady=(10, 5))
        self.txt_req_note = ctk.CTkTextbox(content_frame, height=100, fg_color=COLORS["entry_bg"], border_color=COLORS["entry_border"], border_width=2)
        self.txt_req_note.pack(fill="x")
        
        # 4. 발주서경로 (DnD)
        self.file_manager.create_file_input_row(content_frame, "발주서 파일", "발주서경로", "파일을 드래그하거나 클릭하여 선택")
        
        # Footer (Buttons)
        footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        footer_frame.pack(fill="x", padx=20, pady=20, side="bottom")
        
        ctk.CTkButton(footer_frame, text="확인", command=self._on_confirm, width=100, height=35,
                      fg_color=COLORS["secondary"], hover_color=COLORS["secondary_hover"], font=FONTS["main_bold"]).pack(side="right", padx=5)
        ctk.CTkButton(footer_frame, text="취소", command=self.destroy, width=80, height=35,
                      fg_color=COLORS["bg_light"], hover_color=COLORS["bg_light_hover"], text_color=COLORS["text"]).pack(side="right", padx=5)

    def _create_input_row(self, parent, label, placeholder=""):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", pady=5)
        ctk.CTkLabel(f, text=label, width=100, anchor="w", font=FONTS["main"], text_color=COLORS["text_dim"]).pack(side="left")
        entry = ctk.CTkEntry(f, height=30, placeholder_text=placeholder,
                             fg_color=COLORS["entry_bg"], border_color=COLORS["entry_border"], border_width=2)
        entry.pack(side="left", fill="x", expand=True)
        return entry

    def _on_confirm(self):
        order_date = self.entry_order_date.get().strip()
        po_no = self.entry_po_no.get().strip()
        req_note = self.txt_req_note.get("1.0", "end-1c").strip()
        
        # Validation
        if not order_date:
            messagebox.showwarning("경고", "수주일을 입력해주세요.", parent=self)
            return
            
        # Prepare data
        confirm_data = {
            "수주일": order_date,
            "발주서번호": po_no,
            "주문요청사항": req_note
        }
        
        # File paths
        file_path = self.file_manager.full_paths.get("발주서경로")
        if not file_path and "발주서경로" in self.file_manager.file_entries:
            file_path = self.file_manager.file_entries["발주서경로"].get().strip()
            
        if file_path:
            confirm_data["발주서경로"] = file_path
            
        # Call callback
        self.on_confirm_callback(confirm_data)
        self.destroy()

    # File DnD delegates
    def update_file_entry(self, col_name, full_path):
        self.file_manager.update_file_entry(col_name, full_path)
    def open_file(self, entry_widget, col_name):
        self.file_manager.open_file(col_name)
    def clear_entry(self, entry_widget, col_name):
        self.file_manager.clear_entry(col_name)
