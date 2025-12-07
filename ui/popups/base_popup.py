import tkinter as tk
from datetime import datetime
from tkinter import messagebox
import os

import customtkinter as ctk

# [변경] 스타일 및 팝업 경로 수정
from src.styles import COLORS, FONT_FAMILY, FONTS
from ui.popups.client_popup import ClientPopup 

try:
    from tkinterdnd2 import DND_FILES
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False

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
        self.file_entries = {} # {col_name: entry_widget}
        self.full_paths = {}   # {col_name: full_path}
        
        self._create_widgets()

        
        if self.mgmt_no:
            self._load_data()
        else:
            self._generate_new_id()

        self.transient(parent)
        self.grab_set()
        self.attributes("-topmost", True)

    # ... (기존 _create_widgets, _create_header, _setup_info_panel 등은 변경 없음, 생략) ...
    def _create_widgets(self):
        """Standard Split View Layout: Header -> Split Content (Info + Items) -> Footer"""
        self.configure(fg_color=COLORS["bg_dark"])
        
        # Main Container
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 1. Header
        self._create_header(self.main_container)
        
        # 2. Main Content (Split View)
        self.content_frame = ctk.CTkFrame(self.main_container, fg_color="transparent")
        self.content_frame.pack(fill="both", expand=True, pady=10)
        
        # Left Panel (Info)
        self.info_panel = ctk.CTkFrame(self.content_frame, fg_color=COLORS["bg_medium"], corner_radius=10, width=400)
        self.info_panel.pack(side="left", fill="y", padx=(0, 10))
        self.info_panel.pack_propagate(False)
        self._setup_info_panel(self.info_panel)
        
        # Right Panel (Items)
        self.items_panel = ctk.CTkFrame(self.content_frame, fg_color=COLORS["bg_medium"], corner_radius=10)
        self.items_panel.pack(side="right", fill="both", expand=True)
        self._setup_items_panel(self.items_panel)
        
        # 3. Footer
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

    # ==========================================================================
    # File & DnD Helpers (tkinterdnd2 적용)
    # ==========================================================================
    def create_file_input_row(self, parent, label, col_name, placeholder="파일을 드래그하거나 열기 버튼을 클릭하세요"):
        if label:
            ctk.CTkLabel(parent, text=label, font=FONTS["main"], text_color=COLORS["text_dim"]).pack(anchor="w", pady=(5, 0))
        
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(2, 5))
        
        entry = ctk.CTkEntry(row, placeholder_text=placeholder, height=28)
        entry.pack(side="left", fill="x", expand=True)
        
        btn_open = ctk.CTkButton(row, text="열기", width=50, height=28,
                      command=lambda: self.open_file(entry, col_name),
                      fg_color=COLORS["bg_light"], text_color=COLORS["text"])
        btn_open.pack(side="left", padx=(5, 0))
                      
        btn_delete = ctk.CTkButton(row, text="삭제", width=50, height=28,
                      command=lambda: self.clear_entry(entry, col_name),
                      fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"])
        btn_delete.pack(side="left", padx=(5, 0))
        
        self.file_entries[col_name] = entry
        
        if DND_AVAILABLE:
            self._setup_dnd_hook(entry, col_name)
        
        return entry, btn_open, btn_delete

    def _setup_dnd_hook(self, widget, col_name):
        """[수정] tkinterdnd2 방식의 후킹"""
        def hook_wait():
            try:
                if widget.winfo_exists():
                    widget.drop_target_register(DND_FILES)
                    widget.dnd_bind('<<Drop>>', lambda e: self.on_drop(e, col_name))
                else:
                    self.after(200, hook_wait)
            except Exception as e:
                self.after(200, hook_wait)
        self.after(200, hook_wait)

    def on_drop(self, event, col_name):
        """[수정] tkinterdnd2 이벤트 핸들러"""
        raw_data = event.data
        if not raw_data: return

        file_path = raw_data
        if raw_data.startswith('{') and raw_data.endswith('}'):
            file_path = raw_data[1:-1]
        elif '} {' in raw_data:
             file_path = raw_data.split('} {')[0].replace('{', '')
             
        self.update_file_entry(col_name, file_path)

    def update_file_entry(self, col_name, full_path):
        if not full_path: return
        full_path = os.path.normpath(full_path)
        self.full_paths[col_name] = full_path
        if col_name in self.file_entries:
            entry = self.file_entries[col_name]
            try:
                entry.delete(0, "end")
                entry.insert(0, os.path.basename(full_path))
            except: pass

    # ... (나머지 메서드들은 경로만 수정하여 유지) ...
    def open_file(self, entry_widget, col_name):
        path = self.full_paths.get(col_name) if hasattr(self, "full_paths") else None
        if not path: path = entry_widget.get().strip()
        if path and os.path.exists(path):
            try: os.startfile(path)
            except Exception as e: messagebox.showerror("에러", f"파일을 열 수 없습니다.\n{e}", parent=self)
        else:
            messagebox.showwarning("경고", "파일 경로가 유효하지 않습니다.", parent=self)

    def clear_entry(self, entry_widget, col_name):
        path = self.full_paths.get(col_name) if hasattr(self, "full_paths") else None
        if not path: path = entry_widget.get().strip()
        if not path: return

        is_managed = False
        try:
            abs_path = os.path.abspath(path)
            from src.config import Config
            abs_root = os.path.abspath(Config.DEFAULT_ATTACHMENT_ROOT)
            if abs_path.startswith(abs_root): is_managed = True
        except: pass

        if is_managed:
            if messagebox.askyesno("파일 삭제", f"정말 파일을 삭제하시겠습니까?\n(영구 삭제됨)", parent=self):
                try:
                    if os.path.exists(path): os.remove(path)
                except Exception as e:
                    messagebox.showerror("오류", f"삭제 실패: {e}", parent=self)
                    return
                entry_widget.delete(0, "end")
                if hasattr(self, "full_paths") and col_name in self.full_paths: 
                    del self.full_paths[col_name]
        else:
            entry_widget.delete(0, "end")
            if hasattr(self, "full_paths") and col_name in self.full_paths: 
                del self.full_paths[col_name]

    # ... (클라이언트 선택 로직 등 유지) ...
    def _on_client_select(self, client_name):
        if not client_name: return
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

    def _add_item_row(self, item_data=None):
        if not hasattr(self, 'scroll_items'): return None
        row_frame = ctk.CTkFrame(self.scroll_items, fg_color="transparent", height=35)
        row_frame.pack(fill="x", pady=2)
        e_item = ctk.CTkEntry(row_frame, width=150)
        e_item.pack(side="left", padx=2)
        e_model = ctk.CTkEntry(row_frame, width=150)
        e_model.pack(side="left", padx=2)
        e_desc = ctk.CTkEntry(row_frame, width=200)
        e_desc.pack(side="left", padx=2)
        e_qty = ctk.CTkEntry(row_frame, width=60, justify="center")
        e_qty.pack(side="left", padx=2)
        e_price = ctk.CTkEntry(row_frame, width=100, justify="right")
        e_price.pack(side="left", padx=2)
        e_supply = ctk.CTkEntry(row_frame, width=100, justify="right", state="readonly")
        e_supply.pack(side="left", padx=2)
        e_tax = ctk.CTkEntry(row_frame, width=80, justify="right", state="readonly")
        e_tax.pack(side="left", padx=2)
        e_total = ctk.CTkEntry(row_frame, width=100, justify="right", state="readonly")
        e_total.pack(side="left", padx=2)
        
        btn_del = ctk.CTkButton(row_frame, text="X", width=40, fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
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

    def _generate_new_id(self): raise NotImplementedError
    def _load_data(self): raise NotImplementedError
    def save(self): raise NotImplementedError
    def delete(self): raise NotImplementedError