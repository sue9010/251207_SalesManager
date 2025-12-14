import customtkinter as ctk
from datetime import datetime
from tkinter import messagebox
from ui.popups.base_popup import BasePopup
from src.styles import COLORS, FONTS

class MiniAccountingPopup(BasePopup):
    def __init__(self, parent, data_manager, refresh_callback, mgmt_nos, default_amount=0):
        self.mgmt_nos = mgmt_nos
        if default_amount == 0 and mgmt_nos:
            # Calculate default total from items
            total_sum = 0
            if hasattr(data_manager, 'df_data'):
                df = data_manager.df_data
                # Find rows for all mgmt_nos
                rows = df[df["관리번호"].isin(mgmt_nos)]
                for _, row in rows.iterrows():
                    val = row.get("합계금액", 0)
                    try: total_sum += float(str(val).replace(",", ""))
                    except: pass
            self.default_amount = total_sum
        else:
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
            total_amount = float(amount_str) if amount_str else 0
        except ValueError:
            messagebox.showerror("오류", "금액을 올바르게 입력하세요.", parent=self)
            return

        date = self.entry_date.get()
        tax_no = self.entry_tax_no.get()
        base_note = self.entry_note.get()

        # 1. Calculate Total Amount for Ratio (Use "합계금액")
        total_order_sum = 0
        mgmt_amounts = {} # {mgmt_no: total_amount}

        for mgmt_no in self.mgmt_nos:
            # Find amount from data
            amt = 0
            if hasattr(self.dm, 'df_data'):
                row = self.dm.df_data[self.dm.df_data["관리번호"] == mgmt_no]
                if not row.empty:
                    # Use "합계금액" (Total Amount) which corresponds to Tax Invoice Amount
                    val = row.iloc[0].get("합계금액", 0)
                    try: 
                        amt = float(str(val).replace(",", ""))
                    except: 
                        amt = 0
            
            mgmt_amounts[mgmt_no] = amt
            total_order_sum += amt

        # 2. Distribute and Save
        success_count = 0
        error_msg = ""
        
        # Note for cross-referencing
        all_mgmts_str = ", ".join(self.mgmt_nos)
        
        for mgmt_no in self.mgmt_nos:
            # Calculate Split Amount
            split_amount = 0
            if total_order_sum > 0:
                ratio = mgmt_amounts.get(mgmt_no, 0) / total_order_sum
                split_amount = total_amount * ratio
            elif len(self.mgmt_nos) > 0:
                # Fallback: Equal split if no amounts found (shouldn't happen with correct parsing)
                split_amount = total_amount / len(self.mgmt_nos)

            # Round to 0 decimal places
            split_amount = round(split_amount)

            # Construct Note
            note = base_note
            if len(self.mgmt_nos) > 1:
                note = f"{base_note} (일괄발행 포함: {all_mgmts_str})"

            tax_data = {
                "관리번호": mgmt_no,
                "발행일": date,
                "금액": split_amount,        # 안분된 금액 (합계용)
                "세금계산서번호": tax_no,
                "비고": note,
                "발행총액": total_amount       # 실제 세금계산서 총액 (참조용)
            }

            s, m = self.dm.add_tax_invoice(tax_data)
            if s:
                success_count += 1
            else:
                error_msg = m

        if success_count > 0:
            messagebox.showinfo("성공", f"세금계산서가 {success_count}건 등록되었습니다.", parent=self)
            if self.refresh_callback:
                self.refresh_callback()
            self.destroy()
            
        else:
            messagebox.showerror("실패", f"저장 실패: {error_msg}", parent=self)

    # Abstract methods
    def delete(self): pass
    def _generate_new_id(self): pass
    def _add_item_row(self, item_data=None): pass
    def _calculate_totals(self): pass
    def _on_client_select(self, client_name): pass
    def _load_data(self): pass
