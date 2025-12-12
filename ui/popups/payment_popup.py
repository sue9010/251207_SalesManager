import os
import shutil
import tkinter as tk
from datetime import datetime
from tkinter import messagebox
import getpass


import customtkinter as ctk
import pandas as pd

from src.config import Config
from ui.popups.base_popup import BasePopup
from src.styles import COLORS, FONTS

class PaymentPopup(BasePopup):
    def __init__(self, parent, data_manager, refresh_callback, mgmt_nos):
        if isinstance(mgmt_nos, list):
            self.mgmt_nos = mgmt_nos
        else:
            self.mgmt_nos = [mgmt_nos]

        if not self.mgmt_nos:
            messagebox.showerror("오류", "수금 처리할 대상이 지정되지 않았습니다.", parent=parent)
            self.destroy()
            return
            
        super().__init__(parent, data_manager, refresh_callback, popup_title="수금", mgmt_no=self.mgmt_nos[0])
        self.geometry("1350x920")


    def _create_header(self, parent):
        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 10))
        
        # 상단: ID 및 상태
        top_row = ctk.CTkFrame(header_frame, fg_color="transparent")
        top_row.pack(fill="x", anchor="w")
        
        # ID 표시
        id_text = self.mgmt_nos[0]
        if len(self.mgmt_nos) > 1:
            id_text += f" 외 {len(self.mgmt_nos)-1}건"
            
        self.entry_id = ctk.CTkEntry(top_row, width=200, font=FONTS["main_bold"], text_color=COLORS["text_dim"])
        self.entry_id.pack(side="left")
        self.entry_id.insert(0, id_text)
        self.entry_id.configure(state="readonly")

        # Status (Readonly)
        ctk.CTkLabel(top_row, text="상태:", font=FONTS["main_bold"]).pack(side="left", padx=(20, 5))
        self.combo_status = ctk.CTkComboBox(top_row, values=["주문", "생산중", "완료", "취소", "보류"], 
                                          width=100, font=FONTS["main"], state="readonly")
        self.combo_status.pack(side="left")

    def _setup_info_panel(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(1, weight=1)

        # Row 0: Payment Date (Full Width)
        f_date = ctk.CTkFrame(parent, fg_color="transparent")
        f_date.grid(row=0, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        ctk.CTkLabel(f_date, text="입금일", width=60, anchor="w", font=FONTS["main"], text_color=COLORS["text_dim"]).pack(side="left")
        self.entry_pay_date = ctk.CTkEntry(f_date, height=28, placeholder_text="YYYY-MM-DD",
                                           fg_color=COLORS["entry_bg"], border_color=COLORS["entry_border"], border_width=2)
        self.entry_pay_date.pack(side="left", fill="x", expand=True)
        self.entry_pay_date.insert(0, datetime.now().strftime("%Y-%m-%d"))

        # Row 1: Payment Amount (Currency + Amount)
        f_amt = ctk.CTkFrame(parent, fg_color="transparent")
        f_amt.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        
        ctk.CTkLabel(f_amt, text="입금액", width=60, anchor="w", font=FONTS["main"], text_color=COLORS["text_dim"]).pack(side="left")
        
        self.combo_currency = ctk.CTkComboBox(f_amt, values=["KRW", "USD", "EUR", "CNY", "JPY"], width=80,
                                              font=FONTS["main"], state="readonly")
        self.combo_currency.pack(side="left", padx=(0, 5))
        self.combo_currency.set("KRW")
        
        self.lbl_paid_amount = self._add_summary_row(f_totals, "기수금액:", "0", 1)
        self.lbl_unpaid_amount = self._add_summary_row(f_totals, "미수금액 (잔액):", "0", 2)

    def _setup_items_panel(self, parent):
        # 타이틀
        top_frame = ctk.CTkFrame(parent, fg_color="transparent")
        top_frame.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(top_frame, text="관련 품목 리스트 (Read Only)", font=FONTS["header"]).pack(side="left")
        
        # 헤더 (BasePopup.COL_CONFIG 사용 - 삭제 제외)
        configs = [
            self.COL_CONFIG["item"], self.COL_CONFIG["model"], self.COL_CONFIG["desc"],
            self.COL_CONFIG["qty"], self.COL_CONFIG["price"], self.COL_CONFIG["supply"],
            self.COL_CONFIG["tax"], self.COL_CONFIG["total"]
        ]
        
        header_frame = ctk.CTkFrame(parent, height=35, fg_color=COLORS["bg_dark"])
        header_frame.pack(fill="x", padx=15)
        
        for conf in configs:
            ctk.CTkLabel(header_frame, text=conf["header"], width=conf["width"], font=FONTS["main_bold"]).pack(side="left", padx=2)
            
        # 스크롤 리스트
        self.scroll_items = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        self.scroll_items.pack(fill="both", expand=True, padx=10, pady=5)

    def _create_footer(self, parent):
        footer_frame = ctk.CTkFrame(parent, fg_color="transparent")
        footer_frame.pack(fill="x", pady=(10, 0))
        
        ctk.CTkButton(footer_frame, text="닫기", command=self.destroy, width=100, height=45,
                      fg_color=COLORS["bg_light"], hover_color=COLORS["bg_light_hover"], 
                      text_color=COLORS["text"]).pack(side="left")
                      
        ctk.CTkButton(footer_frame, text="수금 처리 (저장)", command=self.save, width=200, height=45,
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"], 
                      font=FONTS["header"]).pack(side="right")

    def _add_summary_row(self, parent, label_text, value_text, row):
        ctk.CTkLabel(parent, text=label_text, font=FONTS["main"], text_color=COLORS["text_dim"]).grid(row=row, column=0, padx=5, pady=5, sticky="w")
        value_label = ctk.CTkLabel(parent, text=value_text, font=FONTS["main_bold"])
        value_label.grid(row=row, column=1, padx=5, pady=5, sticky="e")
        return value_label

    def _add_item_row(self, item_data=None):
        # BasePopup._add_item_row를 사용하되, 버튼 제거 및 ReadOnly 처리
        row_widgets = super()._add_item_row(item_data)
        
        # 삭제 버튼 제거 (있다면)
        try:
            for child in row_widgets["frame"].winfo_children():
                if isinstance(child, ctk.CTkButton): child.destroy()
        except: pass
        
        if item_data is not None:
            def set_val(key, val, is_num=False):
                if is_num:
                    try: val = f"{float(str(val).replace(',', '')):,.0f}"
                    except: val = "0"
                else:
                    val = str(val)
                    if val == "nan": val = ""
                
                w = row_widgets[key]
                w.configure(state="normal")
                w.delete(0, "end")
                w.insert(0, val)
                w.configure(state="readonly")

            set_val("item", item_data.get("품목명", ""))
            set_val("model", item_data.get("모델명", ""))
            set_val("desc", item_data.get("Description", ""))
            set_val("qty", item_data.get("수량", 0), is_num=True)
            set_val("price", item_data.get("단가", 0), is_num=True)
            set_val("supply", item_data.get("공급가액", 0), is_num=True)
            set_val("tax", item_data.get("세액", 0), is_num=True)
            set_val("total", item_data.get("합계금액", 0), is_num=True)
                
        return row_widgets

    def _load_data(self):
        df = self.dm.df_data
        rows = df[df["관리번호"].isin(self.mgmt_nos)].copy()
        
        if rows.empty: return

        first = rows.iloc[0]
        
        self.combo_status.set(str(first.get("Status", "")))
        
        # BasePopup의 entry_client 등이 생성되지 않았으므로(BasePopup._create_widgets를 안부름)
        # 여기서는 품목 리스트만 채움
        
        for _, row in rows.iterrows():
            self._add_item_row(row)

        self._calculate_and_display_totals(rows)

    def _calculate_and_display_totals(self, df_rows):
        try:
            total_amount = pd.to_numeric(df_rows["합계금액"], errors='coerce').sum()
            paid_amount = pd.to_numeric(df_rows["기수금액"], errors='coerce').sum()
        except:
            total_amount = 0
            paid_amount = 0
            
        unpaid_amount = total_amount - paid_amount

        self.lbl_total_amount.configure(text=f"{total_amount:,.0f}")
        self.lbl_paid_amount.configure(text=f"{paid_amount:,.0f}")
        self.lbl_unpaid_amount.configure(text=f"{unpaid_amount:,.0f}")
        
        self.entry_payment.delete(0, "end")
        self.entry_payment.insert(0, f"{unpaid_amount:.0f}")


    # ==========================================================================
    # 저장 로직
    # ==========================================================================
    def save(self):
        try:
            payment_amount = float(self.entry_payment.get().replace(",", ""))
        except ValueError:
            messagebox.showerror("오류", "입금액은 숫자여야 합니다.", parent=self)
            return

        if payment_amount <= 0:
            messagebox.showwarning("확인", "입금액이 0보다 커야 합니다.", parent=self)
            return

        payment_date = self.entry_pay_date.get()
        currency = self.combo_currency.get()

        # File Saving Logic
        saved_paths = {}
        try:
            client_name = self.dm.df_data.loc[self.dm.df_data["관리번호"] == self.mgmt_nos[0], "업체명"].values[0]
        except: client_name = "Unknown"
        
        info_text = f"{client_name}_{self.mgmt_nos[0]}_{int(payment_amount)}"

        file_inputs = [
            ("외화입금증빙경로", "외화 입금"),
            ("송금상세경로", "Remittance detail")
        ]

        for col, prefix in file_inputs:
            success, msg, path = self.file_manager.save_file(col, "입금", prefix, info_text)
            if success and path:
                saved_paths[col] = path
            elif not success and msg:
                print(f"File save warning ({col}): {msg}") 

        def confirm_fee(item_name, diff, curr):
            # Use the currency from the popup if not provided or to override?
            # Actually the callback uses 'curr' passed from DataManager, which might be from the data.
            # But here we are processing payment in a specific currency.
            # If the payment currency differs from item currency, that's complex.
            # For now, we assume the user knows what they are doing.
            return messagebox.askyesno("수수료 처리 확인", 
                                       f"[{item_name}] 항목의 잔액이 {diff:,.0f} ({curr}) 남습니다.\n"
                                       f"이를 수수료로 처리하여 '완납' 하시겠습니까?", parent=self)

        success, msg = self.dm.process_payment(
            self.mgmt_nos,
            payment_amount,
            payment_date,
            saved_paths,
            confirm_fee
        )

        if success:
            self.attributes("-topmost", False)
            messagebox.showinfo("성공", "수금 처리가 완료되었습니다.", parent=self)
            self.refresh_callback()
            self.destroy()
        else:
            self.attributes("-topmost", False)
            messagebox.showerror("실패", f"저장에 실패했습니다: {msg}", parent=self)
            self.attributes("-topmost", True)
    
    # BasePopup 추상 메서드 구현 (사용 안함)
    def _generate_new_id(self): pass
    def delete(self): pass
    def _on_client_select(self, client_name): pass