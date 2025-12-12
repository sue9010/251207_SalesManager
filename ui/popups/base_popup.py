import tkinter as tk
from datetime import datetime
from tkinter import messagebox
import os
import customtkinter as ctk
import pandas as pd

from src.styles import COLORS, FONT_FAMILY, FONTS
from utils.file_dnd import FileDnDManager

class BasePopup(ctk.CTkToplevel):
    def __init__(self, parent, data_manager, refresh_callback, popup_title="Popup", mgmt_no=None):
        super().__init__(parent)
        self.dm = data_manager
        self.refresh_callback = refresh_callback
        self.mgmt_no = mgmt_no
        self.popup_title = popup_title
        
        if mgmt_no:
            mode_text = f"{popup_title} 상세 정보 수정"
        else:
            mode_text = f"신규 {popup_title} 등록"
            
        self.title(f"{mode_text} - Sales Manager")
        self.geometry("1100x750")
        
        self.item_rows = []
        self.file_manager = FileDnDManager(self)
        
        self._create_widgets()
        
        if self.mgmt_no:
            self._load_data()
        
        self.transient(parent)
        self.grab_set()
        self.attributes("-topmost", True)
        
        self.bind("<Escape>", lambda e: self.destroy())

    def _create_widgets(self):
        self.configure(fg_color=COLORS["bg_dark"])
        
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        self._create_header(self.main_container)
        
        self.content_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, pady=10)
        
        self.info_panel = ctk.CTkFrame(self.content_frame, fg_color=COLORS["bg_medium"], corner_radius=10, width=400)
        self.info_panel.pack(side="left", fill="y", padx=(0, 10))
        self.info_panel.pack_propagate(False)
        self._setup_info_panel(self.info_panel)
        
        self.items_panel = ctk.CTkFrame(self.content_frame, fg_color=COLORS["bg_medium"], corner_radius=10)
        self.items_panel.pack(side="right", fill="both", expand=True)
        self._setup_items_panel(self.items_panel)
        
        self._create_footer(self.main_container)

    def _create_header(self, parent):
        self.header_frame = ctk.CTkFrame(parent, height=50, fg_color="transparent")
        self.header_frame.pack(fill="x", pady=(0, 10))
        title_text = f"{self.popup_title} #{self.mgmt_no}" if self.mgmt_no else f"새 {self.popup_title}"
        self.lbl_title = ctk.CTkLabel(self.header_frame, text=title_text, font=FONTS["header"])
        self.lbl_title.pack(side="left", padx=10)

    def _setup_info_panel(self, parent): raise NotImplementedError
    def _setup_items_panel(self, parent): raise NotImplementedError

    def _create_footer(self, parent):
        self.footer_frame = ctk.CTkFrame(parent, height=60, fg_color="transparent")
        self.footer_frame.pack(fill="x", pady=(10, 0), side="bottom")
        self.btn_save = ctk.CTkButton(self.footer_frame, text="저장", command=self.save, width=120, height=40,
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"], font=FONTS["main_bold"])
        self.btn_save.pack(side="right", padx=5)
        self.btn_cancel = ctk.CTkButton(self.footer_frame, text="취소", command=self.destroy, width=80, height=40,
                      fg_color=COLORS["bg_light"], hover_color=COLORS["bg_light_hover"], text_color=COLORS["text"])
        self.btn_cancel.pack(side="right", padx=5)

    def create_file_input_row(self, parent, label, col_name, placeholder="파일을 드래그하거나 열기 버튼을 클릭하세요"):
        return self.file_manager.create_file_input_row(parent, label, col_name, placeholder)
    def update_file_entry(self, col_name, full_path):
        self.file_manager.update_file_entry(col_name, full_path)
    def open_file(self, entry_widget, col_name):
        self.file_manager.open_file(col_name)
    def clear_entry(self, entry_widget, col_name):
        self.file_manager.clear_entry(col_name)
    @property
    def file_entries(self): return self.file_manager.file_entries
    @property
    def full_paths(self): return self.file_manager.full_paths

    def create_input_row(self, parent, label, readonly=False, placeholder=""):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", pady=5)
        ctk.CTkLabel(f, text=label, width=100, anchor="w", font=FONTS["main"], text_color=COLORS["text_dim"]).pack(side="left")
        entry = ctk.CTkEntry(f, height=30, placeholder_text=placeholder,
                             fg_color=COLORS["entry_bg"], border_color=COLORS["entry_border"], border_width=2)
        entry.pack(side="left", fill="x", expand=True)
        if readonly: entry.configure(state="readonly")
        return entry

    def create_combo_row(self, parent, label, values, command=None):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.pack(fill="x", pady=5)
        ctk.CTkLabel(f, text=label, width=100, anchor="w", font=FONTS["main"], text_color=COLORS["text_dim"]).pack(side="left")
        combo = ctk.CTkComboBox(f, values=values, command=command, height=30,
                                fg_color=COLORS["entry_bg"], border_color=COLORS["entry_border"], border_width=2, button_color=COLORS["entry_border"])
        combo.pack(side="left", fill="x", expand=True)
        return combo

    def create_grid_input(self, parent, row, col, label, placeholder="", width=None):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.grid(row=row, column=col, sticky="ew", padx=5, pady=5)
        ctk.CTkLabel(f, text=label, width=60, anchor="w", font=FONTS["main"], text_color=COLORS["text_dim"]).pack(side="left")
        entry = ctk.CTkEntry(f, height=28, placeholder_text=placeholder,
                             fg_color=COLORS["entry_bg"], border_color=COLORS["entry_border"], border_width=2)
        entry.pack(side="left", fill="x", expand=True)
        return entry

    def create_grid_combo(self, parent, row, col, label, values, command=None):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.grid(row=row, column=col, sticky="ew", padx=5, pady=5)
        ctk.CTkLabel(f, text=label, width=60, anchor="w", font=FONTS["main"], text_color=COLORS["text_dim"]).pack(side="left")
        combo = ctk.CTkComboBox(f, values=values, command=command, height=28,
                                fg_color=COLORS["entry_bg"], border_color=COLORS["entry_border"], border_width=2, button_color=COLORS["entry_border"])
        combo.pack(side="left", fill="x", expand=True)
        return combo

    def _on_client_select(self, client_name):
        if not client_name: return
        from ui.popups.client_popup import ClientPopup
        df = self.dm.df_clients
        if client_name not in df["업체명"].values:
            self.attributes("-topmost", False)
            if messagebox.askyesno("알림", f"'{client_name}'은(는) 등록되지 않은 업체입니다.\n신규 등록하시겠습니까?", parent=self):
                self.attributes("-topmost", True)
                def on_client_registered():
                    self._load_clients()
                    if hasattr(self, "entry_client"):
                        self.entry_client.set_completion_list(self.dm.df_clients["업체명"].unique().tolist())
                    self._on_client_select(client_name)
                ClientPopup(self, self.dm, on_client_registered, client_name=None)
            else:
                self.attributes("-topmost", True)
            return
        row = df[df["업체명"] == client_name]
        if not row.empty:
            currency = row.iloc[0].get("통화", "KRW")
            if hasattr(self, "combo_currency") and hasattr(self, "on_currency_change"):
                if currency and str(currency) != "nan":
                    self.combo_currency.set(currency)
                    self.on_currency_change(currency)
            note = str(row.iloc[0].get("특이사항", "-"))
            if note == "nan" or not note: note = "-"
            if hasattr(self, "lbl_client_note"):
                self.lbl_client_note.configure(text=f"업체 특이사항: {note}")

    def _load_clients(self): pass

    COL_CONFIG = {
        "item": {"header": "품명", "width": 120},
        "model": {"header": "모델명", "width": 120},
        "desc": {"header": "Description", "width": 150},
        "qty": {"header": "수량", "width": 50},
        "price": {"header": "단가", "width": 80},
        "supply": {"header": "공급가액", "width": 80},
        "tax": {"header": "세액", "width": 60},
        "total": {"header": "합계", "width": 80},
        "delete": {"header": "삭제", "width": 40},
    }

    def _add_item_row(self, item_data=None):
        if not hasattr(self, 'scroll_items'): return None
        row_frame = ctk.CTkFrame(self.scroll_items, fg_color="transparent", height=35)
        row_frame.pack(fill="x", pady=2)
        conf = self.COL_CONFIG
        
        e_item = ctk.CTkEntry(row_frame, width=conf["item"]["width"])
        e_item.pack(side="left", padx=2)
        e_model = ctk.CTkEntry(row_frame, width=conf["model"]["width"])
        e_model.pack(side="left", padx=2)
        e_desc = ctk.CTkEntry(row_frame, width=conf["desc"]["width"])
        e_desc.pack(side="left", padx=2)
        e_qty = ctk.CTkEntry(row_frame, width=conf["qty"]["width"], justify="center")
        e_qty.pack(side="left", padx=2)
        e_price = ctk.CTkEntry(row_frame, width=conf["price"]["width"], justify="right")
        e_price.pack(side="left", padx=2)
        e_supply = ctk.CTkEntry(row_frame, width=conf["supply"]["width"], justify="right", state="readonly")
        e_supply.pack(side="left", padx=2)
        e_tax = ctk.CTkEntry(row_frame, width=conf["tax"]["width"], justify="right", state="readonly")
        e_tax.pack(side="left", padx=2)
        e_total = ctk.CTkEntry(row_frame, width=conf["total"]["width"], justify="right", state="readonly")
        e_total.pack(side="left", padx=2)
        
        btn_del = ctk.CTkButton(row_frame, text="X", width=conf["delete"]["width"], fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
                                command=lambda f=row_frame: self._delete_item_row(f))
        btn_del.pack(side="left", padx=5)
        row_widgets = {
            "frame": row_frame, "item": e_item, "model": e_model, "desc": e_desc,
            "qty": e_qty, "price": e_price, "supply": e_supply, "tax": e_tax, "total": e_total
        }
        self.item_rows.append(row_widgets)
        e_qty.insert(0, "1")
        e_price.insert(0, "0")
        e_qty.bind("<KeyRelease>", lambda e: self.calculate_row(row_widgets))
        e_price.bind("<KeyRelease>", lambda e: self.on_price_change(e, e_price, row_widgets))
        
        if item_data is not None:
            e_item.insert(0, str(item_data.get("품목명", "")))
            e_model.insert(0, str(item_data.get("모델명", "")))
            e_desc.insert(0, str(item_data.get("Description", "")))
            q_val = item_data.get("수량", 0)
            e_qty.delete(0, "end"); e_qty.insert(0, str(q_val))
            try: price_val = float(item_data.get("단가", 0))
            except: price_val = 0
            e_price.delete(0, "end"); e_price.insert(0, f"{int(price_val):,}")
            self.calculate_row(row_widgets)
        else: self.calculate_row(row_widgets)
        return row_widgets

    def _delete_item_row(self, frame):
        for item in self.item_rows:
            if item["frame"] == frame:
                self.item_rows.remove(item)
                break
        frame.destroy()
        self._calculate_totals()

    def _on_add_item_shortcut(self, event=None):
        row_widgets = self._add_item_row()
        if row_widgets and "item" in row_widgets:
            row_widgets["item"].focus_set()

    def _create_common_header(self, parent, title_text, id_text):
        """공통 헤더 생성 로직"""
        top_frame = ctk.CTkFrame(parent, fg_color="transparent")
        top_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        # Title
        ctk.CTkLabel(top_frame, text=title_text, font=FONTS["header"], text_color=COLORS["text"]).pack(side="left")
        
        # ID (Right)
        if id_text:
            id_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
            id_frame.pack(side="right")
            ctk.CTkLabel(id_frame, text=f"No. {id_text}", font=FONTS["main_bold"], text_color=COLORS["primary"]).pack()
            
        return top_frame

    def on_price_change(self, event, widget, row_data):
        val = widget.get().replace(",", "")
        if val.isdigit():
            formatted = f"{int(val):,}"
            if widget.get() != formatted:
                widget.delete(0, "end")
                widget.insert(0, formatted)
        self.calculate_row(row_data)

    def calculate_row(self, row_data):
        try:
            qty = float(row_data["qty"].get().strip().replace(",","") or 0)
            price = float(row_data["price"].get().strip().replace(",","") or 0)
            supply = qty * price
            tax_rate = 0
            if hasattr(self, "entry_tax_rate"):
                try: tax_rate = float(self.entry_tax_rate.get().strip() or 0)
                except: tax_rate = 0
            tax = supply * (tax_rate / 100)
            total = supply + tax
            def update_entry(entry, val):
                entry.configure(state="normal")
                entry.delete(0, "end")
                entry.insert(0, f"{val:,.0f}")
                entry.configure(state="readonly")
            update_entry(row_data["supply"], supply)
            update_entry(row_data["tax"], tax)
            update_entry(row_data["total"], total)
        except ValueError: pass
        self._calculate_totals()

    def _calculate_totals(self):
        total_qty = 0
        total_amt = 0
        for row in self.item_rows:
            try:
                q = float(row["qty"].get().replace(",",""))
                t = float(row["total"].get().replace(",",""))
                total_qty += q
                total_amt += t
            except: pass
        if hasattr(self, "lbl_total_qty"):
            self.lbl_total_qty.configure(text=f"총 수량: {total_qty:,.0f}")
        if hasattr(self, "lbl_total_amt"):
            self.lbl_total_amt.configure(text=f"총 합계: {total_amt:,.0f}")

    def save(self): raise NotImplementedError
    def delete(self): raise NotImplementedError