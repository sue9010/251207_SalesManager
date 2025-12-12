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
        # Modern Sidebar Layout Size
        self.geometry("850x700")
        
        self._setup_shortcuts()

    def _setup_shortcuts(self):
        """네비게이션 단축키 설정 (F1~F4)"""
        self.bind("<F1>", lambda e: self.select_page("basic"))
        self.bind("<F2>", lambda e: self.select_page("finance"))
        self.bind("<F3>", lambda e: self.select_page("logistics"))
        self.bind("<F4>", lambda e: self.select_page("manage"))

    def _setup_items_panel(self, parent):
        # ClientPopup does not have an items list (products), so we hide or destroy the items panel
        # BasePopup creates self.items_panel. We can destroy it or just leave it empty.
        # Better: Hide the items panel and expand the info panel.
        
        # Accessing parent's parent (content_frame) to adjust layout
        # self.items_panel is 'parent' here.
        parent.pack_forget()
        
        # Expand info_panel to fill
        if hasattr(self, 'info_panel'):
            self.info_panel.configure(width=None, fg_color="transparent") # Transparent for better layering
            self.info_panel.pack(side="left", fill="both", expand=True, padx=0, pady=0)

    def _setup_info_panel(self, parent):
        # Parent is self.info_panel
        parent.pack_propagate(True)
        
        # Main Layout: Sidebar (Left) + Content (Right)
        parent.columnconfigure(0, weight=0) # Sidebar fixed width
        parent.columnconfigure(1, weight=1) # Content expands
        parent.rowconfigure(0, weight=1)
        
        # --- Sidebar ---
        self.sidebar_frame = ctk.CTkFrame(parent, width=200, corner_radius=10, fg_color=COLORS["bg_medium"])
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew", pady=20, padx=(20, 0))
        self.sidebar_frame.pack_propagate(False)
        
        ctk.CTkLabel(self.sidebar_frame, text="설정 메뉴", font=FONTS["header"], text_color=COLORS["text_dim"]).pack(anchor="w", padx=20, pady=(20, 10))
        
        self.nav_buttons = {}
        self.pages = {}
        
        # Navigation Buttons
        menus = [
            ("basic", "기본 정보(F1)"),
            ("finance", "금융 정보(F2)"),
            ("logistics", "물류/수출(F3)"),
            ("manage", "문서/기타(F4)")
        ]
        
        for key, text in menus:
            btn = ctk.CTkButton(self.sidebar_frame, text=text, height=40, corner_radius=6, anchor="w",
                                fg_color="transparent", text_color=COLORS["text"],
                                hover_color=COLORS["bg_light"],
                                font=FONTS["main"],
                                command=lambda k=key: self.select_page(k))
            btn.pack(fill="x", padx=10, pady=2)
            self.nav_buttons[key] = btn

        # --- Content Area ---
        self.content_area = ctk.CTkFrame(parent, fg_color="transparent")
        self.content_area.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.content_area.grid_rowconfigure(0, weight=1)
        self.content_area.grid_columnconfigure(0, weight=1)
        
        # Create Pages
        self._create_page_basic("basic")
        self._create_page_finance("finance")
        self._create_page_logistics("logistics")
        self._create_page_manage("manage")
        
        # Select first page by default
        self.select_page("basic")

    def select_page(self, page_key):
        # Show selected page
        for key, frame in self.pages.items():
            if key == page_key:
                frame.grid(row=0, column=0, sticky="nsew")
            else:
                frame.grid_forget()
                
        # Update button styles
        for key, btn in self.nav_buttons.items():
            if key == page_key:
                btn.configure(fg_color=COLORS["primary"], text_color="white", hover_color=COLORS["primary_hover"])
            else:
                btn.configure(fg_color="transparent", text_color=COLORS["text"], hover_color=COLORS["bg_light"])

    def _create_page_basic(self, key):
        frame = ctk.CTkFrame(self.content_area, fg_color=COLORS["bg_medium"], corner_radius=10)
        self.pages[key] = frame
        
        ctk.CTkLabel(frame, text="기본 정보", font=FONTS["header_large"], text_color=COLORS["text"]).pack(anchor="w", padx=20, pady=(20, 5))
        ctk.CTkLabel(frame, text="업체의 기본 식별 정보와 담당자 연락처를 관리합니다.", font=FONTS["sub"], text_color=COLORS["text_dim"]).pack(anchor="w", padx=20, pady=(0, 20))
        
        # Content Container
        content = ctk.CTkFrame(frame, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Section 1: Company Info
        self.entries["업체명"] = self.create_input_row(content, "업체명")
        self.entries["국가"] = self.create_input_row(content, "국가")
        self.entries["통화"] = self.create_combo_row(content, "통화", ["KRW", "USD", "EUR", "CNY", "JPY"])
        self.entries["주소"] = self.create_input_row(content, "주소")
        
        ctk.CTkFrame(content, height=2, fg_color=COLORS["bg_light"]).pack(fill="x", pady=20) # Divider
        
        # Section 2: Contact Info
        ctk.CTkLabel(content, text="담당자 정보", font=FONTS["header"], text_color=COLORS["primary"]).pack(anchor="w", pady=(0, 10))
        self.entries["담당자"] = self.create_input_row(content, "담당자")
        self.entries["전화번호"] = self.create_input_row(content, "전화번호")
        self.entries["이메일"] = self.create_input_row(content, "이메일")

    def _create_page_finance(self, key):
        frame = ctk.CTkFrame(self.content_area, fg_color=COLORS["bg_medium"], corner_radius=10)
        self.pages[key] = frame
        
        ctk.CTkLabel(frame, text="금융 정보", font=FONTS["header_large"], text_color=COLORS["text"]).pack(anchor="w", padx=20, pady=(20, 5))
        ctk.CTkLabel(frame, text="결제 및 계좌 정보를 관리합니다.", font=FONTS["sub"], text_color=COLORS["text_dim"]).pack(anchor="w", padx=20, pady=(0, 20))
        
        content = ctk.CTkFrame(frame, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        self.entries["결제방법"] = self.create_input_row(content, "결제방법")
        self.entries["예금주"] = self.create_input_row(content, "예금주")
        self.entries["계좌번호"] = self.create_input_row(content, "계좌번호")
        self.entries["은행명"] = self.create_input_row(content, "은행명")
        self.entries["은행주소"] = self.create_input_row(content, "은행주소")
        self.entries["Swift Code"] = self.create_input_row(content, "Swift Code")

    def _create_page_logistics(self, key):
        frame = ctk.CTkFrame(self.content_area, fg_color=COLORS["bg_medium"], corner_radius=10)
        self.pages[key] = frame
        
        ctk.CTkLabel(frame, text="물류/수출 정보", font=FONTS["header_large"], text_color=COLORS["text"]).pack(anchor="w", padx=20, pady=(20, 5))
        ctk.CTkLabel(frame, text="수출 허가 및 운송 관련 정보를 관리합니다.", font=FONTS["sub"], text_color=COLORS["text_dim"]).pack(anchor="w", padx=20, pady=(0, 20))
        
        content = ctk.CTkFrame(frame, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        self.entries["수출허가구분"] = self.create_input_row(content, "수출허가구분")
        self.entries["수출허가번호"] = self.create_input_row(content, "수출허가번호")
        self.entries["만료일"] = self.create_input_row(content, "만료일", placeholder="YYYY-MM-DD")
        self.entries["운송계정"] = self.create_input_row(content, "운송계정")
        self.entries["운송방법"] = self.create_input_row(content, "운송방법")

    def _create_page_manage(self, key):
        frame = ctk.CTkFrame(self.content_area, fg_color=COLORS["bg_medium"], corner_radius=10)
        self.pages[key] = frame
        
        ctk.CTkLabel(frame, text="문서 및 기타", font=FONTS["header_large"], text_color=COLORS["text"]).pack(anchor="w", padx=20, pady=(20, 5))
        ctk.CTkLabel(frame, text="관련 증빙 서류와 특이사항을 관리합니다.", font=FONTS["sub"], text_color=COLORS["text_dim"]).pack(anchor="w", padx=20, pady=(0, 20))
        
        content = ctk.CTkFrame(frame, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        ctk.CTkLabel(content, text="증빙 서류", font=FONTS["header"], text_color=COLORS["primary"]).pack(anchor="w", pady=(0, 10))
        
        entry, _, _ = self.create_file_input_row(content, "사업자등록증", "사업자등록증경로")
        self.entries["사업자등록증경로"] = entry

        entry_export, _, _ = self.create_file_input_row(content, "수출허가서", "수출허가서경로")
        self.entries["수출허가서경로"] = entry_export
        
        ctk.CTkFrame(content, height=2, fg_color=COLORS["bg_light"]).pack(fill="x", pady=20) # Divider
        
        ctk.CTkLabel(content, text="기타 특이사항", font=FONTS["header"], text_color=COLORS["primary"]).pack(anchor="w", pady=(0, 10))
        self.entry_note = ctk.CTkTextbox(content, height=100, border_width=2, 
                                         border_color=COLORS["entry_border"], fg_color=COLORS["entry_bg"])
        self.entry_note.pack(fill="both", expand=True)
        self.entries["특이사항"] = self.entry_note

    def _load_data(self):
        # BasePopup calls this if mgmt_no is set.
        # Here mgmt_no is client_name.
        df = self.dm.df_clients
        row = df[df["업체명"] == self.client_name].iloc[0]
        
        for key, widget in self.entries.items():
            val = str(row.get(key, ""))
            if val == "nan": val = ""
            
            if key in ["사업자등록증경로", "수출허가서경로"] and val:
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
            if key in ["사업자등록증경로", "수출허가서경로"]:
                data[key] = self.full_paths.get(key, "").strip()
            elif isinstance(widget, ctk.CTkTextbox):
                data[key] = widget.get("1.0", "end-1c").strip()
            else:
                data[key] = widget.get().strip()
            
        if not data.get("업체명"):
            messagebox.showwarning("경고", "업체명은 필수입니다.", parent=self)
            return

        # File Save Logic
        # 1. 사업자등록증
        success, msg, new_path = self.file_manager.save_file(
            "사업자등록증경로", "사업자등록증", f"사업자등록증_{data['업체명']}", ""
        )
        if success and new_path:
            data["사업자등록증경로"] = new_path
        elif not success:
            messagebox.showerror("파일 저장 실패", f"사업자등록증 저장 실패: {msg}", parent=self)
            return

        # 2. 수출허가서
        success, msg, new_path = self.file_manager.save_file(
            "수출허가서경로", "수출허가서", f"수출허가서_{data['업체명']}", ""
        )
        if success and new_path:
            data["수출허가서경로"] = new_path
        elif not success:
            messagebox.showerror("파일 저장 실패", f"수출허가서 저장 실패: {msg}", parent=self)
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
