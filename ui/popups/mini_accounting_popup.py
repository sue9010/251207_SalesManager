import customtkinter as ctk
from datetime import datetime
from tkinter import messagebox
from ui.popups.base_popup import BasePopup
from src.styles import COLORS, FONTS

class MiniAccountingPopup(BasePopup):
    def __init__(self, parent, data_manager, refresh_callback, mgmt_nos, default_amount=0):
        self.mgmt_nos = mgmt_nos
        self.default_amount = default_amount
        self.dm = data_manager
        
        super().__init__(parent, data_manager, refresh_callback, popup_title="세금계산서 발행", mgmt_no=mgmt_nos[0])
        self.geometry("500x350")
        self.after(100, lambda: self.entry_amount.focus_set())

    def _create_widgets(self):
        self.configure(fg_color=COLORS["bg_dark"])
        
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        self._setup_info_panel(self.main_container)
        self._create_footer(self.main_container)

    def _setup_info_panel(self, parent):
        # Form Frame
        form_frame = ctk.CTkFrame(parent, fg_color="transparent")
        form_frame.pack(fill="both", expand=True)
        form_frame.grid_columnconfigure(1, weight=1)

        # 1. Issue Date
        ctk.CTkLabel(form_frame, text="발행일", font=FONTS["main_bold"]).grid(row=0, column=0, sticky="w", pady=5)
        self.entry_date = ctk.CTkEntry(form_frame, height=30)
        self.entry_date.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=5)
        self.entry_date.insert(0, datetime.now().strftime("%Y-%m-%d"))

        # 2. Amount
        ctk.CTkLabel(form_frame, text="금액", font=FONTS["main_bold"]).grid(row=1, column=0, sticky="w", pady=5)
        self.entry_amount = ctk.CTkEntry(form_frame, height=30)
        self.entry_amount.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=5)
        if self.default_amount > 0:
            self.entry_amount.insert(0, f"{self.default_amount:,.0f}")

        # 3. Tax Invoice No
        ctk.CTkLabel(form_frame, text="세금계산서번호", font=FONTS["main_bold"]).grid(row=2, column=0, sticky="w", pady=5)
        self.entry_tax_no = ctk.CTkEntry(form_frame, height=30, placeholder_text="선택 사항")
        self.entry_tax_no.grid(row=2, column=1, sticky="ew", padx=(10, 0), pady=5)

        # 4. Note
        ctk.CTkLabel(form_frame, text="비고", font=FONTS["main_bold"]).grid(row=3, column=0, sticky="w", pady=5)
        self.entry_note = ctk.CTkEntry(form_frame, height=30)
        self.entry_note.grid(row=3, column=1, sticky="ew", padx=(10, 0), pady=5)

    def _create_footer(self, parent):
        footer = ctk.CTkFrame(parent, fg_color="transparent")
        footer.pack(fill="x", side="bottom", pady=(20, 0))
        
        ctk.CTkButton(footer, text="취소", command=self.destroy, fg_color=COLORS["bg_light"], text_color=COLORS["text"], width=80).pack(side="left")
        ctk.CTkButton(footer, text="저장", command=self.save, fg_color=COLORS["success"], width=80).pack(side="right")

    def save(self):
        try:
            amount_str = self.entry_amount.get().replace(",", "")
            amount = float(amount_str) if amount_str else 0
        except ValueError:
            messagebox.showerror("오류", "금액을 올바르게 입력하세요.", parent=self)
            return

        date = self.entry_date.get()
        tax_no = self.entry_tax_no.get()
        note = self.entry_note.get()

        # Create records for each mgmt_no?
        # Usually tax invoice is per order or grouped?
        # If multiple mgmt_nos are passed, how do we split the amount?
        # The user said "ProductionPopup... open mini... input amount".
        # If ProductionPopup has multiple items selected, it passes list of mgmt_nos.
        # But usually ProductionPopup is for one mgmt_no (grouped items under one order).
        # Wait, ProductionPopup constructor: `mgmt_no=self.mgmt_nos[0]`.
        # And `self.mgmt_nos` is a list.
        # If I have multiple mgmt_nos, should I create one tax invoice record linked to the MAIN mgmt_no?
        # Or split it?
        # Tax Invoice is usually for the total amount.
        # I'll link it to the FIRST mgmt_no (Main Order No).
        
        tax_data = {
            "관리번호": self.mgmt_nos[0],
            "발행일": date,
            "금액": amount,
            "세금계산서번호": tax_no,
            "비고": note
        }

        success, msg = self.dm.add_tax_invoice(tax_data)

        if success:
            messagebox.showinfo("성공", "세금계산서가 등록되었습니다.", parent=self)
            if self.refresh_callback:
                self.refresh_callback()
            self.destroy()
        else:
            messagebox.showerror("실패", f"저장 실패: {msg}", parent=self)

    # Abstract methods
    def delete(self): pass
    def _generate_new_id(self): pass
    def _add_item_row(self, item_data=None): pass
    def _calculate_totals(self): pass
    def _on_client_select(self, client_name): pass
    def _load_data(self): pass
