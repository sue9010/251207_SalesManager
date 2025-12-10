import customtkinter as ctk
from datetime import datetime
from tkinter import messagebox
from ui.popups.base_popup import BasePopup
from src.styles import COLORS, FONTS

class MiniPaymentPopup(BasePopup):
    def __init__(self, parent, data_manager, refresh_callback, mgmt_nos, unpaid_amount):
        self.mgmt_nos = mgmt_nos
        self.unpaid_amount = unpaid_amount
        # BasePopup expects a single mgmt_no for title generation usually, but we can pass the first one
        super().__init__(parent, data_manager, refresh_callback, popup_title="입금 처리", mgmt_no=mgmt_nos[0])
        self.geometry("500x340")

    def _create_widgets(self):
        self.configure(fg_color=COLORS["bg_dark"])
        
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        self._setup_info_panel(self.main_container)
        self._create_footer(self.main_container)

    def _setup_info_panel(self, parent):
        # Unpaid Amount Display
        ctk.CTkLabel(parent, text=f"미수금액: {self.unpaid_amount:,.0f}", font=FONTS["header"], text_color=COLORS["danger"]).pack(anchor="e", pady=(0, 10))

        # Using a frame for form layout
        form_frame = ctk.CTkFrame(parent, fg_color="transparent")
        form_frame.pack(fill="both", expand=True)
        form_frame.grid_columnconfigure(1, weight=1)

        # 1. Payment Date
        ctk.CTkLabel(form_frame, text="입금일", font=FONTS["main_bold"]).grid(row=0, column=0, sticky="w", pady=5)
        self.entry_pay_date = ctk.CTkEntry(form_frame, height=30)
        self.entry_pay_date.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=5)
        self.entry_pay_date.insert(0, datetime.now().strftime("%Y-%m-%d"))

        # 2. Payment Amount (Currency + Entry)
        ctk.CTkLabel(form_frame, text="입금액", font=FONTS["main_bold"]).grid(row=1, column=0, sticky="w", pady=5)
        
        amt_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        amt_frame.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=5)
        
        self.combo_currency = ctk.CTkComboBox(amt_frame, values=["KRW", "USD", "EUR", "CNY", "JPY"], width=80, state="readonly")
        self.combo_currency.pack(side="left", padx=(0, 5))
        self.combo_currency.set("KRW")
        
        self.entry_amount = ctk.CTkEntry(amt_frame, height=30)
        self.entry_amount.pack(side="left", fill="x", expand=True)
        self.entry_amount.insert(0, f"{int(self.unpaid_amount)}")

        # 3. Foreign Proof File
        ctk.CTkLabel(form_frame, text="외화입금증빙", font=FONTS["main_bold"]).grid(row=2, column=0, sticky="w", pady=5)
        f_foreign = ctk.CTkFrame(form_frame, fg_color="transparent")
        f_foreign.grid(row=2, column=1, sticky="ew", padx=(10, 0), pady=5)
        self.entry_file_foreign, _, _ = self.create_file_input_row(f_foreign, "", "외화입금증빙경로") # Label empty as it's on left

        # 4. Remittance Detail File
        ctk.CTkLabel(form_frame, text="송금상세", font=FONTS["main_bold"]).grid(row=3, column=0, sticky="w", pady=5)
        f_remit = ctk.CTkFrame(form_frame, fg_color="transparent")
        f_remit.grid(row=3, column=1, sticky="ew", padx=(10, 0), pady=5)
        self.entry_file_remit, _, _ = self.create_file_input_row(f_remit, "", "송금상세경로")

    def _create_footer(self, parent):
        footer = ctk.CTkFrame(parent, fg_color="transparent")
        footer.pack(fill="x", side="bottom", pady=(20, 0))
        
        ctk.CTkButton(footer, text="취소", command=self.destroy, fg_color=COLORS["bg_light"], text_color=COLORS["text"], width=80).pack(side="left")
        ctk.CTkButton(footer, text="저장", command=self.save, fg_color=COLORS["success"], width=80).pack(side="right")

    def save(self):
        try:
            amount = float(self.entry_amount.get().replace(",", ""))
        except ValueError:
            messagebox.showerror("오류", "입금액을 올바르게 입력하세요.", parent=self)
            return

        if amount <= 0:
            messagebox.showwarning("경고", "입금액은 0보다 커야 합니다.", parent=self)
            return

        date = self.entry_pay_date.get()
        
        # File Saving
        saved_paths = {}
        # Need client name for file naming, fetch from DM using first mgmt_no
        rows = self.dm.df_data[self.dm.df_data["관리번호"] == self.mgmt_nos[0]]
        client_name = rows.iloc[0]["업체명"] if not rows.empty else "Unknown"
        safe_client = "".join([c for c in client_name if c.isalnum() or c in (' ', '_')]).strip()
        info_text = f"{safe_client}_{self.mgmt_nos[0]}_{int(amount)}"

        # Foreign Proof
        if self.entry_file_foreign and self.entry_file_foreign.get():
             success, msg, path = self.file_manager.save_file("외화입금증빙경로", "입금", "외화 입금", info_text)
             if success and path: saved_paths["외화입금증빙경로"] = path

        # Remittance Detail
        if self.entry_file_remit and self.entry_file_remit.get():
             success, msg, path = self.file_manager.save_file("송금상세경로", "입금", "Remittance detail", info_text)
             if success and path: saved_paths["송금상세경로"] = path

        def confirm_fee(item_name, diff, curr):
            return messagebox.askyesno("수수료 처리 확인", 
                                       f"[{item_name}] 항목의 잔액이 {diff:,.0f} ({curr}) 남습니다.\n"
                                       f"이를 수수료로 처리하여 '완납' 하시겠습니까?", parent=self)

        success, msg = self.dm.process_payment(
            self.mgmt_nos,
            amount,
            date,
            saved_paths,
            confirm_fee
        )

        if success:
            messagebox.showinfo("성공", "입금 처리가 완료되었습니다.", parent=self)
            self.refresh_callback()
            self.destroy()
        else:
            messagebox.showerror("실패", f"처리 실패: {msg}", parent=self)

    # Abstract methods
    def delete(self): pass
    def _generate_new_id(self): pass
    def _add_item_row(self, item_data=None): pass
    def _calculate_totals(self): pass
    def _on_client_select(self, client_name): pass
    def _load_data(self): pass # Data passed in constructor
