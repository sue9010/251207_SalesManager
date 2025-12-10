import tkinter as tk
from datetime import datetime
from tkinter import messagebox
import getpass
import customtkinter as ctk
import pandas as pd

from src.config import Config
from ui.popups.base_popup import BasePopup
from ui.popups.packing_list_popup import PackingListPopup 
from src.styles import COLORS, FONTS
from managers.export_manager import ExportManager 

class DeliveryPopup(BasePopup):
    def __init__(self, parent, data_manager, refresh_callback, mgmt_nos):
        if isinstance(mgmt_nos, list):
            self.mgmt_nos = mgmt_nos
        else:
            self.mgmt_nos = [mgmt_nos]

        if not self.mgmt_nos:
            messagebox.showerror("오류", "납품 처리할 대상이 지정되지 않았습니다.", parent=parent)
            self.destroy()
            return

        self.item_widgets_map = {}
        self.export_manager = ExportManager(data_manager) 
        self.current_delivery_no = ""
        self.cached_client_name = "" # UI Entry 대신 변수로 관리
        
        super().__init__(parent, data_manager, refresh_callback, popup_title="납품 처리", mgmt_no=self.mgmt_nos[0])
        self.geometry("1350x920")

    def _create_header(self, parent):
        header_frame = ctk.CTkFrame(parent, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 10))
        
        # 상단: ID 및 상태
        top_row = ctk.CTkFrame(header_frame, fg_color="transparent")
        top_row.pack(fill="x", anchor="w")
        
        self.lbl_id = ctk.CTkLabel(top_row, text="MGMT-000000", font=FONTS["main"], text_color=COLORS["text_dim"])
        self.lbl_id.pack(side="left")
        
        ctk.CTkLabel(top_row, text="납품 대기", font=FONTS["small"], fg_color=COLORS["primary"], 
                     text_color="white", corner_radius=10, width=80).pack(side="left", padx=10)

    def _setup_info_panel(self, parent):
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_columnconfigure(1, weight=1)

        # --- Basic Info Section ---
        ctk.CTkLabel(parent, text="기본 정보", font=FONTS["header"]).grid(row=0, column=0, columnspan=2, sticky="w", padx=5, pady=(5, 5))

        # Row 1: Date, Type
        self.entry_date = self.create_grid_input(parent, 1, 0, "수주일")
        self.entry_type = self.create_grid_input(parent, 1, 1, "구분")

        # Row 2: Currency, Tax Rate
        self.entry_currency = self.create_grid_input(parent, 2, 0, "통화")
        self.entry_tax_rate = self.create_grid_input(parent, 2, 1, "세율")

        # Row 3: Project Name (Full Width)
        self.entry_project = self._create_full_width_input(parent, 3, "프로젝트명")

        # Row 4: Client Name (Full Width)
        self.entry_client = self._create_full_width_input(parent, 4, "업체명")

        # Row 5: Payment Terms, Payment Cond
        self.entry_payment_terms = self.create_grid_input(parent, 5, 0, "결제조건")
        self.entry_payment_cond = self.create_grid_input(parent, 5, 1, "지급조건")

        # Row 6: PO No. (Full Width)
        self.entry_po_no = self._create_full_width_input(parent, 6, "발주서 No.")

        # Row 7: Request Note (Full Width)
        self.entry_req_note = self._create_full_width_input(parent, 7, "주문요청")

        # Row 8: Note (Full Width)
        self.entry_note = self._create_full_width_input(parent, 8, "비고")

        # Row 9: PO File (Full Width)
        f_po_file = ctk.CTkFrame(parent, fg_color="transparent")
        f_po_file.grid(row=9, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        self.entry_po_file, _, _ = self.create_file_input_row(f_po_file, "발주서 파일", "발주서경로")

        # Separator
        ctk.CTkFrame(parent, height=2, fg_color=COLORS["border"]).grid(row=10, column=0, columnspan=2, sticky="ew", padx=5, pady=15)

        # --- Delivery Info Section ---
        ctk.CTkLabel(parent, text="출고 정보", font=FONTS["header"]).grid(row=11, column=0, columnspan=2, sticky="w", padx=5, pady=(5, 5))

        # Row 12: Delivery Date, Delivery No
        self.entry_delivery_date = self.create_grid_input(parent, 12, 0, "출고일", placeholder="YYYY-MM-DD")
        self.entry_delivery_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        
        self.entry_delivery_no = self.create_grid_input(parent, 12, 1, "출고번호")
        self.entry_delivery_no.configure(state="readonly")

        # Row 13: Invoice No (Full Width)
        self.entry_invoice_no = self._create_full_width_input(parent, 13, "송장번호")

        # Row 14: Transport Method, Transport Account
        self.entry_shipping_method = self.create_grid_input(parent, 14, 0, "운송방법")
        self.entry_shipping_account = self.create_grid_input(parent, 14, 1, "운송계정")

        # Row 15: Waybill File (Full Width)
        f_waybill = ctk.CTkFrame(parent, fg_color="transparent")
        f_waybill.grid(row=15, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        self.entry_waybill_file, _, _ = self.create_file_input_row(f_waybill, "운송장 파일", "운송장경로")

        # Row 16: Buttons (Delivery Request, PI)
        f_btn1 = ctk.CTkFrame(parent, fg_color="transparent")
        f_btn1.grid(row=16, column=0, columnspan=2, sticky="ew", padx=5, pady=(10, 2))
        
        ctk.CTkButton(f_btn1, text="📄 출고요청서", command=self.export_order_request, height=30, 
                      fg_color=COLORS["bg_light"], hover_color=COLORS["primary_hover"], 
                      text_color=COLORS["text"], font=FONTS["main_bold"]).pack(side="left", padx=5, expand=True, fill="x")

        ctk.CTkButton(f_btn1, text="📄 PI 발행", command=self.export_pi, height=30, 
                      fg_color=COLORS["bg_light"], hover_color=COLORS["primary_hover"], 
                      text_color=COLORS["text"], font=FONTS["main_bold"]).pack(side="left", padx=5, expand=True, fill="x")

        # Row 17: Buttons (CI, PL)
        f_btn2 = ctk.CTkFrame(parent, fg_color="transparent")
        f_btn2.grid(row=17, column=0, columnspan=2, sticky="ew", padx=5, pady=(2, 10))

        ctk.CTkButton(f_btn2, text="📄 CI 발행", command=self.export_ci, height=30, 
                      fg_color=COLORS["bg_light"], hover_color=COLORS["primary_hover"], 
                      text_color=COLORS["text"], font=FONTS["main_bold"]).pack(side="left", padx=5, expand=True, fill="x")
                      
        ctk.CTkButton(f_btn2, text="📄 PL 발행", command=self.export_pl, height=30, 
                      fg_color=COLORS["bg_light"], hover_color=COLORS["primary_hover"], 
                      text_color=COLORS["text"], font=FONTS["main_bold"]).pack(side="left", padx=5, expand=True, fill="x")

    def _setup_items_panel(self, parent):
        ctk.CTkLabel(parent, text="납품 품목 리스트", font=FONTS["header"]).pack(anchor="w", padx=15, pady=15)
        
        headers = ["품명", "모델명", "시리얼", "잔여", "출고"]
        widths = [150, 150, 100, 50, 70]
        
        header_frame = ctk.CTkFrame(parent, height=35, fg_color=COLORS["bg_dark"])
        header_frame.pack(fill="x", padx=15)
        
        for h, w in zip(headers, widths):
            ctk.CTkLabel(header_frame, text=h, width=w, font=FONTS["main_bold"]).pack(side="left", padx=2)
            
        self.scroll_items = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        self.scroll_items.pack(fill="both", expand=True, padx=10, pady=5)
        
    def _create_footer(self, parent):
        footer_frame = ctk.CTkFrame(parent, fg_color="transparent")
        footer_frame.pack(fill="x", pady=(10, 0), side="bottom")
        
        ctk.CTkButton(footer_frame, text="닫기", command=self.destroy, width=100, height=45,
                      fg_color=COLORS["bg_light"], hover_color=COLORS["bg_light_hover"], 
                      text_color=COLORS["text"]).pack(side="left")
        ctk.CTkButton(footer_frame, text="납품 처리 (저장)", command=self.save, width=200, height=45,
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"], 
                      font=FONTS["header"]).pack(side="right")

    def _create_full_width_input(self, parent, row, label_text):
        f = ctk.CTkFrame(parent, fg_color="transparent")
        f.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=5)
        ctk.CTkLabel(f, text=label_text, width=80, anchor="w", font=FONTS["main"], text_color=COLORS["text_dim"]).pack(side="left")
        entry = ctk.CTkEntry(f, height=28, fg_color=COLORS["entry_bg"], border_color=COLORS["entry_border"], border_width=2)
        entry.pack(side="left", fill="x", expand=True)
        return entry

    def _set_entry_value(self, entry, value):
        entry.configure(state="normal")
        entry.delete(0, "end")
        entry.insert(0, str(value).replace("nan", ""))
        entry.configure(state="readonly")

    def _load_data(self):
        df = self.dm.df_data
        rows = df[df["관리번호"].isin(self.mgmt_nos)].copy()
        if rows.empty:
            messagebox.showinfo("정보", "데이터를 찾을 수 없습니다.", parent=self)
            self.after(100, self.destroy)
            return

        serial_map = self.dm.get_serial_number_map()
        first = rows.iloc[0]
        
        # 기본 정보 설정 (Basic Info Section)
        mgmt_str = f"{self.mgmt_nos[0]}" + (f" 외 {len(self.mgmt_nos)-1}건" if len(self.mgmt_nos) > 1 else "")
        self.lbl_id.configure(text=f"No. {mgmt_str}")
        
        self.cached_client_name = str(first.get("업체명", ""))

        self._set_entry_value(self.entry_date, first.get("수주일", ""))
        self._set_entry_value(self.entry_type, first.get("구분", ""))
        self._set_entry_value(self.entry_currency, first.get("통화", ""))
        self._set_entry_value(self.entry_tax_rate, first.get("세율(%)", ""))
        self._set_entry_value(self.entry_project, first.get("프로젝트명", ""))
        self._set_entry_value(self.entry_client, first.get("업체명", ""))
        self._set_entry_value(self.entry_payment_terms, first.get("결제조건", ""))
        self._set_entry_value(self.entry_payment_cond, first.get("지급조건", ""))
        self._set_entry_value(self.entry_po_no, first.get("발주서번호", ""))
        self._set_entry_value(self.entry_req_note, first.get("주문요청사항", ""))
        self._set_entry_value(self.entry_note, first.get("비고", ""))
        
        if self.entry_po_file:
             path = str(first.get("발주서경로", "")).replace("nan", "")
             if path: self.update_file_entry("발주서경로", path)

        # 배송 정보 프리필
        self.entry_shipping_method.insert(0, self.dm.get_client_shipping_method(self.cached_client_name) or "")
        self.entry_shipping_account.insert(0, self.dm.get_client_shipping_account(self.cached_client_name) or "")
        
        if self.entry_waybill_file:
            path = str(first.get("운송장경로", "")).replace("nan", "")
            if path: self.update_file_entry("운송장경로", path)

        # 출고번호 (항상 신규 생성)
        self.current_delivery_no = self.dm.get_next_delivery_id() # 신규 생성
            
        self.entry_delivery_no.configure(state="normal")
        self.entry_delivery_no.delete(0, "end")
        self.entry_delivery_no.insert(0, self.current_delivery_no)
        self.entry_delivery_no.configure(state="readonly")

        # 품목 리스트
        target_rows = rows[~rows["Status"].isin(["납품완료/입금대기", "완료", "취소", "보류"])]
        for index, row_data in target_rows.iterrows():
            item_data = row_data.to_dict()
            key = (str(row_data.get("관리번호", "")).strip(), str(row_data.get("모델명", "")).strip(), str(row_data.get("Description", "")).strip())
            item_data["시리얼번호"] = serial_map.get(key, "-")
            self._add_delivery_item_row(index, item_data)

    def _add_delivery_item_row(self, row_index, item_data):
        row_frame = ctk.CTkFrame(self.scroll_items, fg_color="transparent", height=40)
        row_frame.pack(fill="x", pady=2)

        def add_label(text, width, anchor="w", color=None):
            ctk.CTkLabel(row_frame, text=str(text), width=width, anchor=anchor, text_color=color).pack(side="left", padx=2)

        add_label(item_data.get("품목명", ""), 150)
        add_label(item_data.get("모델명", ""), 150)
        add_label(item_data.get("시리얼번호", "-"), 100, "center", COLORS["primary"])
        
        try: current_qty = float(str(item_data.get("수량", "0")).replace(",", ""))
        except: current_qty = 0.0
        add_label(f"{current_qty:g}", 50)
        
        entry_deliver_qty = ctk.CTkEntry(row_frame, width=70, justify="center", fg_color=COLORS["bg_light"], border_color=COLORS["primary"])
        entry_deliver_qty.pack(side="left", padx=2)
        entry_deliver_qty.insert(0, f"{current_qty:g}")

        self.item_widgets_map[row_index] = {
            "current_qty": current_qty,
            "entry": entry_deliver_qty,
            "row_data": item_data
        }


    # Helper Methods for Export

    def _get_client_info(self):
        """고객사 정보를 가져오고 유효성을 검사합니다."""
        if not self.cached_client_name:
            messagebox.showwarning("경고", "고객사 정보가 없습니다.", parent=self)
            return None
        client_row = self.dm.df_clients[self.dm.df_clients["업체명"] == self.cached_client_name]
        if client_row.empty:
            messagebox.showerror("오류", "고객 정보를 찾을 수 없습니다.", parent=self)
            return None
        return client_row.iloc[0]

    def _collect_export_items(self):
        """출고 수량이 입력된 항목들을 수집합니다."""
        items = []
        for index, item_info in self.item_widgets_map.items():
            entry_widget = item_info["entry"]
            row_data = item_info["row_data"]
            try: deliver_qty = float(entry_widget.get().replace(",", ""))
            except: deliver_qty = 0
            
            if deliver_qty <= 0: continue
            
            try: price = float(str(row_data.get("단가", 0)).replace(",", ""))
            except: price = 0
            
            items.append({
                "model": row_data.get("모델명", ""),
                "desc": row_data.get("Description", ""),
                "qty": deliver_qty, 
                "currency": row_data.get("통화", ""),
                "price": price,
                "amount": deliver_qty * price, 
                "po_no": row_data.get("발주서번호", ""),
                "serial": str(row_data.get("시리얼번호", "-"))
            })
        return items


    # Export Methods
    
    def export_order_request(self):
        client_info = self._get_client_info()
        if client_info is None: return

        main_mgmt_no = self.mgmt_nos[0]
        rows = self.dm.df_data[self.dm.df_data["관리번호"] == main_mgmt_no]
        if rows.empty: return
        first = rows.iloc[0]

        order_info = {
            "client_name": self.cached_client_name,
            "mgmt_no": main_mgmt_no,
            "date": first.get("수주일", ""),
            "type": first.get("구분", ""),
            "req_note": first.get("주문요청사항", ""),
        }
        
        items = []
        for _, row in rows.iterrows():
            items.append({
                "item": row.get("품목명", ""),
                "model": row.get("모델명", ""),
                "desc": row.get("Description", ""),
                "qty": float(str(row.get("수량", 0)).replace(",", "") or 0),
            })

        self._execute_export(self.export_manager.export_order_request_to_pdf, client_info, order_info, items, "출고요청서")

    def export_pi(self):
        client_info = self._get_client_info()
        if client_info is None: return

        main_mgmt_no = self.mgmt_nos[0]
        rows = self.dm.df_data[self.dm.df_data["관리번호"] == main_mgmt_no]
        if rows.empty: return
        first = rows.iloc[0]

        order_info = {
            "client_name": self.cached_client_name,
            "mgmt_no": main_mgmt_no,
            "date": first.get("수주일", ""), 
            "po_no": first.get("발주서번호", ""), 
        }
        
        items = []
        for _, row in rows.iterrows():
            items.append({
                "item": row.get("품목명", ""),
                "model": row.get("모델명", ""),
                "desc": row.get("Description", ""),
                "qty": float(str(row.get("수량", 0)).replace(",", "") or 0),
                "price": float(str(row.get("단가", 0)).replace(",", "") or 0),
                "amount": float(str(row.get("공급가액", 0)).replace(",", "") or 0)
            })

        self._execute_export(self.export_manager.export_pi_to_pdf, client_info, order_info, items, "PI")

    def export_ci(self):
        client_info = self._get_client_info()
        if client_info is None: return

        items = self._collect_export_items()
        if not items:
            messagebox.showwarning("경고", "출고 수량이 입력된 항목이 없습니다.", parent=self)
            return

        rows = self.dm.df_data[self.dm.df_data["관리번호"].isin(self.mgmt_nos)]
        first = rows.iloc[0] if not rows.empty else {}

        order_info = {
            "client_name": self.cached_client_name,
            "mgmt_no": self.current_delivery_no, 
            "date": self.entry_delivery_date.get(), 
            "po_no": first.get("발주서번호", ""), 
        }
        self._execute_export(self.export_manager.export_ci_to_pdf, client_info, order_info, items, "CI")

    def export_pl(self):
        client_info = self._get_client_info()
        if client_info is None: return

        items = self._collect_export_items()
        if not items:
            messagebox.showwarning("경고", "출고 수량이 입력된 항목이 없습니다.", parent=self)
            return

        initial_data = {
            "client_name": self.cached_client_name,
            "mgmt_no": self.current_delivery_no,
            "date": self.entry_delivery_date.get(),
            "items": items
        }

        def on_pl_confirm(pl_items, notes):
            first_po = items[0].get("po_no", "") if items else ""
            order_info = {
                "client_name": self.cached_client_name,
                "mgmt_no": self.current_delivery_no,
                "date": self.entry_delivery_date.get(),
                "po_no": first_po,
                "notes": notes
            }
            success, result = self.export_manager.export_pl_to_pdf(client_info, order_info, pl_items)
            return success, result 

        self.attributes("-topmost", False)
        # [변경] ui.popups 경로의 PackingListPopup 사용
        from ui.popups.packing_list_popup import PackingListPopup
        PackingListPopup(self, self.dm, on_pl_confirm, initial_data)

    def _execute_export(self, export_func, client_info, order_info, items, doc_name):
        self.attributes("-topmost", False)
        success, result = export_func(client_info, order_info, items)
        if success:
            messagebox.showinfo("성공", f"{doc_name}가 생성되었습니다.\n{result}", parent=self)
        else:
            messagebox.showerror("실패", result, parent=self)
        self.attributes("-topmost", True)

    # 저장 (납품 처리) 메서드

    def save(self):
        delivery_date = self.entry_delivery_date.get()
        if not delivery_date:
            messagebox.showwarning("경고", "출고일을 입력하세요.", parent=self)
            return

        update_requests = []
        for index, item_widget in self.item_widgets_map.items():
            try: deliver_qty = float(item_widget["entry"].get().replace(",", ""))
            except ValueError:
                messagebox.showerror("오류", "출고 수량은 숫자여야 합니다.", parent=self)
                return
            
            if deliver_qty <= 0: continue
            if deliver_qty > item_widget["current_qty"]:
                messagebox.showerror("오류", f"잔여 수량 초과: {item_widget['row_data'].get('품목명','')}", parent=self)
                return

            update_requests.append({
                "idx": index, "deliver_qty": deliver_qty,
                "serial_no": str(item_widget["row_data"].get("시리얼번호", "-"))
            })
        
        if not update_requests:
            messagebox.showinfo("정보", "처리할 품목이 없습니다.", parent=self)
            return

        waybill_path = ""
        if self.entry_waybill_file:
            path = self.full_paths.get("운송장경로", "")
            waybill_path = path if path else self.entry_waybill_file.get().strip()

        # 운송장 파일 저장
        final_waybill_path = ""
        safe_client = "".join([c for c in self.cached_client_name if c.isalnum() or c in (' ', '_')]).strip()
        
        success, msg, new_path = self.file_manager.save_file(
            "운송장경로", "운송장", "운송장", f"{safe_client}_{self.mgmt_nos[0]}_{self.current_delivery_no}"
        )
        
        if success and new_path:
             final_waybill_path = new_path
        elif not success and waybill_path: # Failed to save but had path
             pass

        success, msg = self.dm.process_delivery(
            self.current_delivery_no,
            delivery_date,
            self.entry_invoice_no.get(),
            self.entry_shipping_method.get(),
            final_waybill_path,
            update_requests
        )

        if success:
            messagebox.showinfo("성공", "납품 처리가 완료되었습니다.\n(CI/PL 발행 가능)", parent=self)
            self.refresh_callback()
            self.export_pl() # 저장 후 바로 PL 발행 팝업 호출 (기존 로직 유지)
            self.destroy()
        else:
            messagebox.showerror("실패", f"저장에 실패했습니다: {msg}", parent=self)

    # Abstract Methods Placeholder
    def delete(self): pass
    def _generate_new_id(self): pass
    def _add_item_row(self, item_data=None): pass
    def _calculate_totals(self): pass
    def _on_client_select(self, client_name): pass