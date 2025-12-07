import os
import shutil
import tkinter as tk
from datetime import datetime
from tkinter import messagebox
import getpass


import customtkinter as ctk
import pandas as pd

# [변경] 경로 수정
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
        self.geometry("1500x850")


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
        
        # 상태 콤보박스 (헤더에 배치)
        self.combo_status = ctk.CTkComboBox(top_row, values=["주문", "생산중", "완료", "취소", "보류"], 
                                          width=100, font=FONTS["main"], state="readonly")
        self.combo_status.pack(side="left", padx=10)
        self.combo_status.set("주문")

    def _setup_info_panel(self, parent):
        # 스크롤 없이 고정된 패널 사용
        
        # 1. 수금 요약
        ctk.CTkLabel(parent, text="수금 요약", font=FONTS["header"]).pack(anchor="w", padx=10, pady=(10, 5))
        
        summary_frame = ctk.CTkFrame(parent, fg_color="transparent")
        summary_frame.pack(fill="x", padx=10, pady=5)
        
        self.lbl_total_amount = self._add_summary_row(summary_frame, "총 합계금액", "0", 0)
        self.lbl_paid_amount = self._add_summary_row(summary_frame, "기수금액", "0", 1)
        
        line = ctk.CTkFrame(summary_frame, height=2, fg_color=COLORS["border"])
        line.grid(row=2, column=0, columnspan=2, sticky="ew", padx=5, pady=10)
        
        ctk.CTkLabel(summary_frame, text="남은 미수금", font=FONTS["header"], text_color=COLORS["danger"]).grid(row=3, column=0, padx=5, pady=5, sticky="w")
        self.lbl_unpaid_amount = ctk.CTkLabel(summary_frame, text="0", font=FONTS["title"], text_color=COLORS["danger"])
        self.lbl_unpaid_amount.grid(row=3, column=1, padx=5, pady=5, sticky="e")
        
        summary_frame.columnconfigure(1, weight=1)

        ctk.CTkFrame(parent, height=2, fg_color=COLORS["border"]).pack(fill="x", padx=10, pady=10)

        # 2. 입금 정보 입력
        ctk.CTkLabel(parent, text="입금 정보", font=FONTS["header"]).pack(anchor="w", padx=10, pady=(0, 5))
        
        input_frame = ctk.CTkFrame(parent, fg_color="transparent")
        input_frame.pack(fill="x", padx=10)
        input_frame.columnconfigure(1, weight=1)
        
        # 입금액
        ctk.CTkLabel(input_frame, text="입금액", font=FONTS["main_bold"]).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.entry_payment = ctk.CTkEntry(input_frame, height=35, font=FONTS["header"])
        self.entry_payment.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # 입금일
        ctk.CTkLabel(input_frame, text="입금일", font=FONTS["main_bold"]).grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.entry_pay_date = ctk.CTkEntry(input_frame, height=30)
        self.entry_pay_date.grid(row=1, column=1, padx=5, pady=5, sticky="ew")
        self.entry_pay_date.insert(0, datetime.now().strftime("%Y-%m-%d"))

        ctk.CTkFrame(parent, height=2, fg_color=COLORS["border"]).pack(fill="x", padx=10, pady=10)

        # 3. 증빙 파일 (DnD)
        ctk.CTkLabel(parent, text="증빙 파일", font=FONTS["header"]).pack(anchor="w", padx=10, pady=(0, 5))
        
        # 외화입금증빙
        self.entry_file_foreign, _, _ = self.create_file_input_row(parent, "외화입금증빙", "외화입금증빙경로")
        
        # 송금상세
        self.entry_file_remit, _, _ = self.create_file_input_row(parent, "송금상세(Remittance)", "송금상세경로")
        
        # DnD Setup


    def _setup_items_panel(self, parent):
        # 타이틀
        top_frame = ctk.CTkFrame(parent, fg_color="transparent")
        top_frame.pack(fill="x", padx=15, pady=15)
        
        ctk.CTkLabel(top_frame, text="관련 품목 리스트 (Read Only)", font=FONTS["header"]).pack(side="left")
        
        # 헤더
        headers = ["품명", "모델명", "Description", "수량", "단가", "공급가액", "세액", "합계"]
        widths = [150,150,200,60,100,100,80,100]
        
        header_frame = ctk.CTkFrame(parent, height=35, fg_color=COLORS["bg_dark"])
        header_frame.pack(fill="x", padx=15)
        
        for h, w in zip(headers, widths):
            ctk.CTkLabel(header_frame, text=h, width=w, font=FONTS["main_bold"]).pack(side="left", padx=2)
            
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
        try: current_user = getpass.getuser()
        except: current_user = "Unknown"

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

        def update_logic(dfs):
            mask = dfs["data"]["관리번호"].isin(self.mgmt_nos)
            if not mask.any():
                return False, "데이터를 찾을 수 없습니다."

            indices = dfs["data"][mask].index
            
            # 1. 강제 재계산
            for mgmt_no in self.mgmt_nos:
                self.dm.recalc_payment_status(dfs, mgmt_no)

            # 2. 배치 처리용 집계
            batch_summary = {}
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            remaining_payment = payment_amount

            # 3. 미수금 차감 시뮬레이션
            for idx in indices:
                if remaining_payment <= 0: break
                
                mgmt_no = dfs["data"].at[idx, "관리번호"]
                currency = str(dfs["data"].at[idx, "통화"]).upper()
                threshold = 200 if currency != "KRW" else 5000
                
                if mgmt_no not in batch_summary:
                    batch_summary[mgmt_no] = {'deposit': 0, 'fee': 0, 'currency': currency}

                try: unpaid = float(dfs["data"].at[idx, "미수금액"])
                except: unpaid = 0
                
                if unpaid > 0:
                    actual_pay = 0
                    fee_pay = 0
                    
                    if remaining_payment >= unpaid:
                        actual_pay = unpaid
                    else:
                        diff = unpaid - remaining_payment
                        if diff <= threshold:
                            item_name = str(dfs["data"].at[idx, "품목명"])
                            if messagebox.askyesno("수수료 처리 확인", 
                                                   f"[{item_name}] 항목의 잔액이 {diff:,.0f} ({currency}) 남습니다.\n"
                                                   f"이를 수수료로 처리하여 '완납' 하시겠습니까?"):
                                actual_pay = remaining_payment
                                fee_pay = diff
                            else:
                                actual_pay = remaining_payment
                        else:
                            actual_pay = remaining_payment

                    batch_summary[mgmt_no]['deposit'] += actual_pay
                    batch_summary[mgmt_no]['fee'] += fee_pay
                    
                    remaining_payment -= actual_pay

            # 4. Payment 시트에 이력 기록
            new_payment_records = []
            
            for mgmt_no, summary in batch_summary.items():
                if summary['deposit'] > 0:
                    record = {
                        "일시": now_str,
                        "관리번호": mgmt_no,
                        "구분": "입금",
                        "입금액": summary['deposit'],
                        "통화": summary['currency'],
                        "작업자": current_user,
                        "비고": f"일괄 입금 ({payment_date})"
                    }
                    if "외화입금증빙경로" in saved_paths:
                        record["외화입금증빙경로"] = saved_paths["외화입금증빙경로"]
                    if "송금상세경로" in saved_paths:
                        record["송금상세경로"] = saved_paths["송금상세경로"]
                        
                    new_payment_records.append(record)
                
                if summary['fee'] > 0:
                    new_payment_records.append({
                        "일시": now_str,
                        "관리번호": mgmt_no,
                        "구분": "수수료/조정",
                        "입금액": summary['fee'],
                        "통화": summary['currency'],
                        "작업자": current_user,
                        "비고": "잔액 탕감 처리"
                    })

            if new_payment_records:
                payment_df_new = pd.DataFrame(new_payment_records)
                dfs["payment"] = pd.concat([dfs["payment"], payment_df_new], ignore_index=True)

            # 5. 최종 재계산
            for mgmt_no in self.mgmt_nos:
                self.dm.recalc_payment_status(dfs, mgmt_no)

            mgmt_str = self.mgmt_nos[0]
            if len(self.mgmt_nos) > 1: mgmt_str += f" 외 {len(self.mgmt_nos)-1}건"
            
            file_log = ""
            if saved_paths.get("외화입금증빙경로"): file_log += " / 외화증빙"
            if saved_paths.get("송금상세경로"): file_log += " / 송금상세"
            
            log_msg = f"번호 [{mgmt_str}] / 입금액 [{payment_amount:,.0f}] 처리{file_log} (재계산 완료)"
            new_log = self.dm._create_log_entry("수금 처리", log_msg)
            dfs["log"] = pd.concat([dfs["log"], pd.DataFrame([new_log])], ignore_index=True)

            return True, ""

        success, msg = self.dm._execute_transaction(update_logic)

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