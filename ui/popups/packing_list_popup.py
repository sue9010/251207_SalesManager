import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

# [변경] 스타일 경로 수정
from src.styles import COLORS, FONTS

class PackingListPopup(ctk.CTkToplevel):
    def __init__(self, parent, data_manager, export_callback, initial_data):
        super().__init__(parent)
        self.parent = parent
        self.dm = data_manager
        self.export_callback = export_callback
        self.initial_data = initial_data 
        
        self.title("Packing List 입력 - Sales Manager")
        self.geometry("1200x600")
        self.configure(fg_color=COLORS["bg_dark"])
        
        # ESC 닫기
        self.bind("<Escape>", lambda e: self.destroy())
        
        self.transient(parent)
        self.attributes("-topmost", True)
        
        self.item_entries = []
        self._create_ui()
        
        self.update_idletasks()
        width = self.winfo_width()
        height = self.winfo_height()
        x = (self.winfo_screenwidth() // 2) - (width // 2)
        y = (self.winfo_screenheight() // 2) - (height // 2)
        self.geometry(f'+{x}+{y}')
        
        self.grab_set()
        self.focus_set()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _create_ui(self):
        # 1. 상단 정보
        top_frame = ctk.CTkFrame(self, fg_color="transparent")
        top_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(top_frame, text="출고번호:", font=FONTS["main_bold"]).pack(side="left", padx=5)
        ctk.CTkLabel(top_frame, text=self.initial_data.get("mgmt_no", ""), font=FONTS["main"], text_color=COLORS["primary"]).pack(side="left", padx=5)
        
        ctk.CTkLabel(top_frame, text="업체명:", font=FONTS["main_bold"]).pack(side="left", padx=(20, 5))
        ctk.CTkLabel(top_frame, text=self.initial_data.get("client_name", ""), font=FONTS["main"]).pack(side="left", padx=5)

        ctk.CTkLabel(top_frame, text="출고일:", font=FONTS["main_bold"]).pack(side="left", padx=(20, 5))
        ctk.CTkLabel(top_frame, text=self.initial_data.get("date", ""), font=FONTS["main"]).pack(side="left", padx=5)

        # 2. 품목 리스트 (테이블 헤더)
        list_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_medium"])
        list_frame.pack(fill="both", expand=True, padx=20, pady=5)
        
        headers = ["C/No.", "Description", "Qty", "Unit", "N.W(kg)", "G.W(kg)", "L(cm)", "W(cm)", "H(cm)", "삭제"]
        widths = [60, 250, 60, 60, 80, 80, 60, 60, 60, 50]
        
        header_frame = ctk.CTkFrame(list_frame, height=30, fg_color=COLORS["bg_dark"])
        header_frame.pack(fill="x")
        
        for h, w in zip(headers, widths):
            ctk.CTkLabel(header_frame, text=h, width=w, font=FONTS["small"]).pack(side="left", padx=2)

        # 스크롤 영역
        self.scroll_frame = ctk.CTkScrollableFrame(list_frame, fg_color="transparent")
        self.scroll_frame.pack(fill="both", expand=True)

        # 초기 아이템 로우 생성
        for item in self.initial_data.get("items", []):
            self._add_item_row(item)

        # 3. 하단 (행 추가, Notes, 버튼)
        bottom_frame = ctk.CTkFrame(self, fg_color="transparent")
        bottom_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkButton(bottom_frame, text="+ 행 추가", command=lambda: self._add_item_row(), 
                      fg_color=COLORS["success"], hover_color="#26A65B",
                      width=100, height=30, font=FONTS["main_bold"]).pack(anchor="w", pady=(0, 10))
        
        ctk.CTkLabel(bottom_frame, text="Notes:", font=FONTS["main_bold"]).pack(anchor="w")
        self.entry_notes = ctk.CTkEntry(bottom_frame, width=600)
        self.entry_notes.pack(fill="x", pady=5)
        
        btn_frame = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=10)
        
        ctk.CTkButton(btn_frame, text="발행", command=self.on_export, 
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"],
                      width=100, height=40, font=FONTS["header"]).pack(side="right", padx=5)
        
        ctk.CTkButton(btn_frame, text="취소", command=self.on_close,
                      fg_color=COLORS["bg_medium"], hover_color=COLORS["bg_light"],
                      width=80, height=40, font=FONTS["main"]).pack(side="right", padx=5)

    def _get_next_c_no(self):
        if not self.item_entries:
            return "1"
        
        last_entry = self.item_entries[-1]["widgets"]["c_no"]
        try:
            val = int(last_entry.get())
            return str(val + 1)
        except:
            return "1"

    def _add_item_row(self, item_data=None):
        row = ctk.CTkFrame(self.scroll_frame, fg_color="transparent", height=35)
        row.pack(fill="x", pady=2)
        
        if item_data is None: item_data = {}
        
        entries = {}
        
        next_c_no = self._get_next_c_no()
        current_c_no = item_data.get("c_no", next_c_no) 
        
        ent_cno = ctk.CTkEntry(row, width=60)
        ent_cno.pack(side="left", padx=2)
        ent_cno.insert(0, str(current_c_no))
        entries["c_no"] = ent_cno
        
        # [수정] Description 값을 무조건 "Thermal camera set"으로 고정
        desc_text = "Thermal camera set"
        
        ent_desc = ctk.CTkEntry(row, width=250)
        ent_desc.pack(side="left", padx=2)
        ent_desc.insert(0, desc_text)
        entries["desc"] = ent_desc
        
        qty_val = item_data.get("qty", "")
        ent_qty = ctk.CTkEntry(row, width=60, justify="right")
        ent_qty.pack(side="left", padx=2)
        ent_qty.insert(0, f"{qty_val:g}" if isinstance(qty_val, (int, float)) else str(qty_val))
        entries["qty"] = ent_qty
        
        ent_unit = ctk.CTkEntry(row, width=60)
        ent_unit.pack(side="left", padx=2)
        ent_unit.insert(0, str(item_data.get("unit", "SET")))
        entries["unit"] = ent_unit
        
        ent_nw = ctk.CTkEntry(row, width=80)
        ent_nw.pack(side="left", padx=2)
        ent_nw.insert(0, str(item_data.get("net_weight", "")))
        entries["net_weight"] = ent_nw
        
        ent_gw = ctk.CTkEntry(row, width=80)
        ent_gw.pack(side="left", padx=2)
        ent_gw.insert(0, str(item_data.get("gross_weight", "")))
        entries["gross_weight"] = ent_gw
        
        ent_l = ctk.CTkEntry(row, width=60)
        ent_l.pack(side="left", padx=2)
        ent_l.insert(0, str(item_data.get("size_l", "")))
        entries["size_l"] = ent_l
        
        ent_w = ctk.CTkEntry(row, width=60)
        ent_w.pack(side="left", padx=2)
        ent_w.insert(0, str(item_data.get("size_w", "")))
        entries["size_w"] = ent_w
        
        ent_h = ctk.CTkEntry(row, width=60)
        ent_h.pack(side="left", padx=2)
        ent_h.insert(0, str(item_data.get("size_h", "")))
        entries["size_h"] = ent_h
        
        btn_del = ctk.CTkButton(row, text="X", width=40, height=28,
                                fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"],
                                command=lambda r=row: self._remove_row(r))
        btn_del.pack(side="left", padx=5)
        
        entry_obj = {
            "row_widget": row,
            "widgets": entries,
            "data": item_data 
        }
        self.item_entries.append(entry_obj)

    def _remove_row(self, row_widget):
        self.item_entries = [e for e in self.item_entries if e["row_widget"] != row_widget]
        row_widget.destroy()

    def on_export(self):
        pl_items = []
        for row in self.item_entries:
            w = row["widgets"]
            d = row["data"]
            
            try:
                qty = float(w["qty"].get().replace(",", ""))
            except: qty = 0
            
            pl_items.append({
                "c_no": w["c_no"].get(),
                "desc": w["desc"].get(), 
                "qty": qty,              
                "unit": w["unit"].get(),
                "net_weight": w["net_weight"].get(),
                "gross_weight": w["gross_weight"].get(),
                "size_l": w["size_l"].get(),
                "size_w": w["size_w"].get(),
                "size_h": w["size_h"].get(),
                "po_no": d.get("po_no", ""),
                "serial": d.get("serial", "")
            })
            
        notes = self.entry_notes.get()
        
        success, msg = self.export_callback(pl_items, notes)
        
        if success:
            messagebox.showinfo("성공", f"PL이 생성되었습니다.\n{msg}", parent=self)
            self.on_close()
        else:
            messagebox.showerror("실패", msg, parent=self)
            self.attributes("-topmost", True) 

    def on_close(self):
        if self.parent:
            try:
                self.parent.attributes("-topmost", True)
                self.parent.lift()
            except: pass
        self.destroy()