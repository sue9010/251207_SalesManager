import customtkinter as ctk
from datetime import datetime
from tkinter import messagebox
from ui.popups.base_popup import BasePopup
from src.styles import COLORS, FONTS

class MiniDeliveryPopup(BasePopup):
    def __init__(self, parent, data_manager, refresh_callback, mgmt_nos, delivery_items):
        self.mgmt_nos = mgmt_nos
        self.delivery_items = delivery_items
        super().__init__(parent, data_manager, refresh_callback, popup_title="납품 처리", mgmt_no=mgmt_nos[0])
        self.geometry("500x300")

    def _create_widgets(self):
        self.configure(fg_color=COLORS["bg_dark"])
        
        self.main_container = ctk.CTkFrame(self, fg_color="transparent")
        self.main_container.pack(fill="both", expand=True, padx=20, pady=20)
        
        self._setup_info_panel(self.main_container)
        self._create_footer(self.main_container)

    def _setup_info_panel(self, parent):
        # Using a frame for form layout
        form_frame = ctk.CTkFrame(parent, fg_color="transparent")
        form_frame.pack(fill="both", expand=True)
        form_frame.grid_columnconfigure(1, weight=1)

        # 1. Delivery Date
        ctk.CTkLabel(form_frame, text="납품일", font=FONTS["main_bold"]).grid(row=0, column=0, sticky="w", pady=5)
        self.entry_date = ctk.CTkEntry(form_frame, height=30)
        self.entry_date.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=5)
        self.entry_date.insert(0, datetime.now().strftime("%Y-%m-%d"))

        # 2. Invoice No
        ctk.CTkLabel(form_frame, text="송장번호", font=FONTS["main_bold"]).grid(row=1, column=0, sticky="w", pady=5)
        self.entry_invoice = ctk.CTkEntry(form_frame, height=30)
        self.entry_invoice.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=5)

        # 3. Shipping Method & Account
        ctk.CTkLabel(form_frame, text="운송방법", font=FONTS["main_bold"]).grid(row=2, column=0, sticky="w", pady=5)
        f_ship = ctk.CTkFrame(form_frame, fg_color="transparent")
        f_ship.grid(row=2, column=1, sticky="ew", padx=(10, 0), pady=5)
        
        self.entry_ship_method = ctk.CTkEntry(f_ship, height=30, placeholder_text="방법")
        self.entry_ship_method.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.entry_ship_account = ctk.CTkEntry(f_ship, height=30, placeholder_text="계정")
        self.entry_ship_account.pack(side="left", fill="x", expand=True)

        # 4. Waybill File
        ctk.CTkLabel(form_frame, text="운송장경로", font=FONTS["main_bold"]).grid(row=3, column=0, sticky="w", pady=5)
        f_waybill = ctk.CTkFrame(form_frame, fg_color="transparent")
        f_waybill.grid(row=3, column=1, sticky="ew", padx=(10, 0), pady=5)
        self.entry_file_waybill, _, _ = self.create_file_input_row(f_waybill, "", "운송장경로")

        # Load Client Shipping Info
        self._load_client_shipping_info()

    def _load_client_shipping_info(self):
        rows = self.dm.df_data[self.dm.df_data["관리번호"] == self.mgmt_nos[0]]
        if rows.empty: return
        client_name = rows.iloc[0]["업체명"]
        
        client_row = self.dm.df_clients[self.dm.df_clients["업체명"] == client_name]
        if not client_row.empty:
            method = str(client_row.iloc[0].get("운송방법", "")).replace("nan", "")
            account = str(client_row.iloc[0].get("운송계정", "")).replace("nan", "")
            
            if method: 
                self.entry_ship_method.delete(0, "end")
                self.entry_ship_method.insert(0, method)
            if account:
                self.entry_ship_account.delete(0, "end")
                self.entry_ship_account.insert(0, account)

    def _create_footer(self, parent):
        footer = ctk.CTkFrame(parent, fg_color="transparent")
        footer.pack(fill="x", side="bottom", pady=(20, 0))
        
        ctk.CTkButton(footer, text="취소", command=self.destroy, fg_color=COLORS["bg_light"], text_color=COLORS["text"], width=80).pack(side="left")
        ctk.CTkButton(footer, text="저장", command=self.save, fg_color=COLORS["primary"], width=80).pack(side="right")

    def save(self):
        date = self.entry_date.get()
        invoice_no = self.entry_invoice.get()
        ship_method = self.entry_ship_method.get()
        ship_account = self.entry_ship_account.get()
        
        # File Saving
        saved_paths = {}
        rows = self.dm.df_data[self.dm.df_data["관리번호"] == self.mgmt_nos[0]]
        client_name = rows.iloc[0]["업체명"] if not rows.empty else "Unknown"
        safe_client = "".join([c for c in client_name if c.isalnum() or c in (' ', '_')]).strip()
        info_text = f"{safe_client}_{self.mgmt_nos[0]}_Delivery"

        if self.entry_file_waybill and self.entry_file_waybill.get():
             success, msg, path = self.file_manager.save_file("운송장경로", "납품", "Waybill", info_text)
             if success and path: saved_paths["운송장경로"] = path

        # Process Delivery
        delivery_no = self.dm.get_next_delivery_id()
        waybill_path = saved_paths.get("운송장경로", "")
        
        success, msg = self.dm.process_delivery(
            delivery_no,
            date,
            invoice_no,
            ship_method,
            waybill_path,
            self.delivery_items
        )

        if success:
            messagebox.showinfo("성공", "납품 처리가 완료되었습니다.", parent=self)
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
    def _load_data(self): pass
