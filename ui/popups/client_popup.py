import os
import tkinter as tk
from datetime import datetime
from tkinter import filedialog, messagebox
import customtkinter as ctk
import pandas as pd

# [변경] 경로 수정
from src.config import Config
from src.styles import COLORS, FONT_FAMILY, FONTS
from utils.file_dnd import FileDnDManager

from ui.popups.base_popup import BasePopup
from src.styles import COLORS, FONTS

class ClientPopup(BasePopup):
    def __init__(self, parent, data_manager, refresh_callback, client_name=None):
        self.client_name = client_name
        self.entries = {}
        
        # BasePopup expects mgmt_no for title logic, but ClientPopup uses client_name.
        # We'll pass None for mgmt_no and handle title manually or override _create_header if needed.
        # Actually BasePopup logic: if mgmt_no: "Edit", else "New". 
        # We can treat client_name as mgmt_no for the purpose of title generation if we want, 
        # but BasePopup uses it for ID display too.
        # Let's pass mgmt_no=client_name so BasePopup sets title to "업체 상세 정보 수정" or "신규 업체 등록".
        
        super().__init__(parent, data_manager, refresh_callback, popup_title="업체", mgmt_no=client_name)
        
        # Override geometry if needed, BasePopup is 1100x750, ClientPopup was 900x660
        self.geometry("900x700")

    def _setup_items_panel(self, parent):
        # ClientPopup does not have an items list (products), so we hide or destroy the items panel
        # BasePopup creates self.items_panel. We can destroy it or just leave it empty.
        # Better: Hide the items panel and expand the info panel.
        
        # Accessing parent's parent (content_frame) to adjust layout
        # self.items_panel is 'parent' here.
        parent.pack_forget()
        
        # Expand info_panel to fill
        if hasattr(self, 'info_panel'):
            self.info_panel.configure(width=None) # Allow expansion
            self.info_panel.pack(side="left", fill="both", expand=True, padx=10)

    def _setup_info_panel(self, parent):
        # Parent is self.info_panel
        parent.pack_propagate(True) # Re-enable propagation to let children dictate size if needed, though we expand it.
        
        # Use two columns within the info panel
        parent.columnconfigure(0, weight=1)
        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(0, weight=1) # Columns row
        parent.rowconfigure(1, weight=0) # Notes row
        
        left_col = ctk.CTkFrame(parent, fg_color="transparent")
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=10)
        
        right_col = ctk.CTkFrame(parent, fg_color="transparent")
        right_col.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=10)
        
        # --- Left Column ---
        ctk.CTkLabel(left_col, text="기본 정보", font=FONTS["header"], text_color=COLORS["primary"]).pack(anchor="w", pady=(0, 5))
        basic_frame = ctk.CTkFrame(left_col, fg_color=COLORS["bg_medium"], corner_radius=6)
        basic_frame.pack(fill="x", pady=(0, 15))
        
        self.entries["업체명"] = self.create_input_row(basic_frame, "업체명")
        self.entries["국가"] = self.create_input_row(basic_frame, "국가")
        self.entries["통화"] = self.create_combo_row(basic_frame, "통화", ["KRW", "USD", "EUR", "CNY", "JPY"])
        self.entries["주소"] = self.create_input_row(basic_frame, "주소")

        ctk.CTkLabel(left_col, text="담당자 정보", font=FONTS["header"], text_color=COLORS["primary"]).pack(anchor="w", pady=(0, 5))
        contact_frame = ctk.CTkFrame(left_col, fg_color=COLORS["bg_medium"], corner_radius=6)
        contact_frame.pack(fill="x", pady=(0, 15))
        
        self.entries["담당자"] = self.create_input_row(contact_frame, "담당자")
        self.entries["전화번호"] = self.create_input_row(contact_frame, "전화번호")
        self.entries["이메일"] = self.create_input_row(contact_frame, "이메일")

        # --- Right Column ---
        ctk.CTkLabel(right_col, text="수출/물류 정보", font=FONTS["header"], text_color=COLORS["primary"]).pack(anchor="w", pady=(0, 5))
        logistics_frame = ctk.CTkFrame(right_col, fg_color=COLORS["bg_medium"], corner_radius=6)
        logistics_frame.pack(fill="x", pady=(0, 15))
        
        self.entries["수출허가구분"] = self.create_input_row(logistics_frame, "수출허가구분")
        self.entries["수출허가번호"] = self.create_input_row(logistics_frame, "수출허가번호")
        self.entries["수출허가만료일"] = self.create_input_row(logistics_frame, "만료일", placeholder="YYYY-MM-DD")
        self.entries["운송계정"] = self.create_input_row(logistics_frame, "운송계정")
        self.entries["운송방법"] = self.create_input_row(logistics_frame, "운송방법")

        ctk.CTkLabel(right_col, text="증빙 서류", font=FONTS["header"], text_color=COLORS["primary"]).pack(anchor="w", pady=(0, 5))
        doc_frame = ctk.CTkFrame(right_col, fg_color=COLORS["bg_medium"], corner_radius=6)
        doc_frame.pack(fill="x", pady=(0, 5))
        
        entry, _, _ = self.create_file_input_row(doc_frame, "사업자등록증", "사업자등록증경로")
        self.entries["사업자등록증경로"] = entry

        # --- Bottom (Notes) ---
        # We need to add this to the parent (info_panel) below the columns, 
        # but we used grid for columns.
        # Let's put columns in a container frame first? 
        # Actually, parent is info_panel. We can use grid row 1 for notes.
        
        note_container = ctk.CTkFrame(parent, fg_color="transparent")
        note_container.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        
        ctk.CTkLabel(note_container, text="기타 특이사항", font=FONTS["header"], text_color=COLORS["primary"]).pack(anchor="w", pady=(0, 5))
        note_frame = ctk.CTkFrame(note_container, fg_color=COLORS["bg_medium"], corner_radius=6)
        note_frame.pack(fill="x")
        
        # Match CTkEntry style using centralized styles
        self.entry_note = ctk.CTkTextbox(note_frame, height=100, border_width=2, 
                                         border_color=COLORS["entry_border"], fg_color=COLORS["entry_bg"])
        self.entry_note.pack(fill="x", padx=5, pady=5)
        self.entries["특이사항"] = self.entry_note

    def _load_data(self):
        # BasePopup calls this if mgmt_no is set.
        # Here mgmt_no is client_name.
        df = self.dm.df_clients
        row = df[df["업체명"] == self.client_name].iloc[0]
        
        for key, widget in self.entries.items():
            val = str(row.get(key, ""))
            if val == "nan": val = ""
            
            if key == "사업자등록증경로" and val:
                self.update_file_entry(key, val)
            else:
                if isinstance(widget, ctk.CTkComboBox):
                    widget.set(val)
                elif isinstance(widget, ctk.CTkTextbox):
                    widget.delete("1.0", "end")
                    widget.insert("1.0", val)
                else:
                    widget.delete(0, "end")
                    widget.insert(0, val)
                    
        if "업체명" in self.entries:
            self.entries["업체명"].configure(state="disabled")

    def save(self):
        data = {}
        for key, widget in self.entries.items():
            if key == "사업자등록증경로":
                data[key] = self.full_paths.get(key, "").strip()
            elif isinstance(widget, ctk.CTkTextbox):
                data[key] = widget.get("1.0", "end-1c").strip()
            else:
                data[key] = widget.get().strip()
            
        if not data.get("업체명"):
            messagebox.showwarning("경고", "업체명은 필수입니다.", parent=self)
            return

        # File Save Logic
        success, msg, new_path = self.file_manager.save_file(
            "사업자등록증경로", "사업자등록증", f"사업자등록증_{data['업체명']}", ""
        )
        if success and new_path:
            data["사업자등록증경로"] = new_path
        elif not success:
            messagebox.showerror("파일 저장 실패", msg, parent=self)
            return

        if self.client_name: # Edit
            success, msg = self.dm.update_client(self.client_name, data)
        else: # New
            success, msg = self.dm.add_client(data)
        
        if success:
            messagebox.showinfo("성공", "저장되었습니다.", parent=self)
            self.refresh_callback()
            self.destroy()
        else:
            messagebox.showerror("실패", msg, parent=self)

    def delete(self):
        if messagebox.askyesno("삭제 확인", f"정말 '{self.client_name}' 업체를 삭제하시겠습니까?", parent=self):
            success, msg = self.dm.delete_client(self.client_name)
            if success:
                messagebox.showinfo("삭제", "삭제되었습니다.", parent=self)
                self.refresh_callback()
                self.destroy()
            else:
                messagebox.showerror("실패", msg, parent=self)
