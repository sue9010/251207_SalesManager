import customtkinter as ctk
from datetime import datetime
from tkinter import messagebox
from ui.popups.base_popup import BasePopup
from src.styles import COLORS, FONTS

class MiniAccountingPopup(BasePopup):
    def __init__(self, parent, data_manager, refresh_callback, mgmt_no):
        # BasePopup expects a single mgmt_no
        super().__init__(parent, data_manager, refresh_callback, popup_title="회계 처리 입력", mgmt_no=mgmt_no)
        self.geometry("500x350")

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

        # 1. Tax Invoice Date
        ctk.CTkLabel(form_frame, text="세금계산서 발행일", font=FONTS["main_bold"]).grid(row=0, column=0, sticky="w", pady=5)
        self.entry_tax_date = ctk.CTkEntry(form_frame, height=30, placeholder_text="YYYY-MM-DD")
        self.entry_tax_date.grid(row=0, column=1, sticky="ew", padx=(10, 0), pady=5)
        
        # Load existing data if available
        row = self.dm.df_data[self.dm.df_data["관리번호"] == self.mgmt_no].iloc[0]
        if row.get("세금계산서발행일") and str(row.get("세금계산서발행일")) != "nan":
             self.entry_tax_date.insert(0, str(row.get("세금계산서발행일")))
        else:
             self.entry_tax_date.insert(0, datetime.now().strftime("%Y-%m-%d"))

        # 2. Tax Invoice No
        ctk.CTkLabel(form_frame, text="세금계산서 번호", font=FONTS["main_bold"]).grid(row=1, column=0, sticky="w", pady=5)
        self.entry_tax_no = ctk.CTkEntry(form_frame, height=30)
        self.entry_tax_no.grid(row=1, column=1, sticky="ew", padx=(10, 0), pady=5)
        if row.get("세금계산서번호") and str(row.get("세금계산서번호")) != "nan":
            self.entry_tax_no.insert(0, str(row.get("세금계산서번호")))

        # 3. Export Declaration No
        ctk.CTkLabel(form_frame, text="수출신고번호", font=FONTS["main_bold"]).grid(row=2, column=0, sticky="w", pady=5)
        self.entry_export_no = ctk.CTkEntry(form_frame, height=30)
        self.entry_export_no.grid(row=2, column=1, sticky="ew", padx=(10, 0), pady=5)
        if row.get("수출신고번호") and str(row.get("수출신고번호")) != "nan":
            self.entry_export_no.insert(0, str(row.get("수출신고번호")))

        # 4. Export Certificate (Per Delivery)
        ctk.CTkLabel(form_frame, text="수출신고필증 (출고별)", font=FONTS["main_bold"]).grid(row=3, column=0, sticky="nw", pady=5)
        
        self.scroll_deliveries = ctk.CTkScrollableFrame(form_frame, height=150, fg_color="transparent")
        self.scroll_deliveries.grid(row=3, column=1, sticky="ew", padx=(10, 0), pady=5)
        
        # Load deliveries
        self.delivery_rows = []
        if not self.dm.df_delivery.empty:
            deliveries = self.dm.df_delivery[self.dm.df_delivery["관리번호"].astype(str) == str(self.mgmt_no)]
            if not deliveries.empty:
                for idx, row in deliveries.iterrows():
                    self._add_delivery_file_row(idx, row)
            else:
                ctk.CTkLabel(self.scroll_deliveries, text="출고 내역이 없습니다.", text_color=COLORS["text_dim"]).pack(anchor="w")
        else:
            ctk.CTkLabel(self.scroll_deliveries, text="출고 내역이 없습니다.", text_color=COLORS["text_dim"]).pack(anchor="w")

    def _add_delivery_file_row(self, idx, row):
        f = ctk.CTkFrame(self.scroll_deliveries, fg_color="transparent")
        f.pack(fill="x", pady=2)
        
        d_no = row.get("출고번호", "-")
        d_date = row.get("출고일", "-")
        item = row.get("품목명", "-")
        qty = row.get("출고수량", 0)
        
        # Info Label
        info_text = f"[{d_date}] {item} ({qty}ea) - {d_no}"
        ctk.CTkLabel(f, text=info_text, font=FONTS["small"], text_color=COLORS["text"]).pack(anchor="w")
        
        # File Input
        # Key format: export_{idx} (using dataframe index to identify row)
        key = f"export_{idx}"
        
        # Create file input using FileDnDManager
        # We manually create it to fit our layout or use the helper
        # Using helper:
        entry, btn_open, btn_del = self.create_file_input_row(f, "", key, placeholder="수출신고필증 드래그 또는 선택")
        
        # Pre-fill if exists
        current_path = row.get("수출신고필증경로", "")
        if current_path and str(current_path) != "nan":
            self.update_file_entry(key, str(current_path))
            
        self.delivery_rows.append({"idx": idx, "key": key, "d_no": d_no})

    def _create_footer(self, parent):
        footer = ctk.CTkFrame(parent, fg_color="transparent")
        footer.pack(fill="x", side="bottom", pady=(20, 0))
        
        ctk.CTkButton(footer, text="취소", command=self.destroy, fg_color=COLORS["bg_light"], text_color=COLORS["text"], width=80).pack(side="left")
        ctk.CTkButton(footer, text="저장", command=self.save, fg_color=COLORS["primary"], width=80).pack(side="right")

    def save(self):
        tax_date = self.entry_tax_date.get()
        tax_no = self.entry_tax_no.get()
        export_no = self.entry_export_no.get()
        
        # 1. Save Accounting Info (Tax Invoice, etc.)
        # This updates the main Data sheet
        success, msg = self.dm.process_after_sales(
            [self.mgmt_no], 
            tax_date, 
            tax_no, 
            export_no, 
            {} # No file paths for Data sheet anymore
        )
        
        if not success:
            messagebox.showerror("실패", f"회계 정보 저장 실패: {msg}", parent=self)
            return

        # 2. Save Export Certificates (Delivery Sheet)
        rows = self.dm.df_data[self.dm.df_data["관리번호"] == self.mgmt_no]
        client_name = rows.iloc[0]["업체명"] if not rows.empty else "Unknown"
        safe_client = "".join([c for c in client_name if c.isalnum() or c in (' ', '_')]).strip()
        
        update_count = 0
        
        for item in self.delivery_rows:
            idx = item["idx"]
            key = item["key"]
            d_no = item["d_no"]
            
            # Check if file entry has value
            if key in self.file_entries and self.file_entries[key].get():
                info_text = f"{safe_client}_{d_no}_Export"
                
                # Save file
                s, m, path = self.file_manager.save_file(key, "수출", "Export", info_text)
                
                if s and path:
                    # Update DataFrame directly
                    # We need to ensure the column exists
                    if "수출신고필증경로" not in self.dm.df_delivery.columns:
                        self.dm.df_delivery["수출신고필증경로"] = ""
                        
                    self.dm.df_delivery.at[idx, "수출신고필증경로"] = path
                    update_count += 1
        
        # Save Delivery DataFrame
        if update_count > 0:
            self.dm.save_data("delivery")
            
        messagebox.showinfo("성공", "저장되었습니다.", parent=self)
        self.refresh_callback()
        self.destroy()

    # Abstract methods
    def delete(self): pass
    def _generate_new_id(self): pass
    def _add_item_row(self, item_data=None): pass
    def _calculate_totals(self): pass
    def _on_client_select(self, client_name): pass
    def _load_data(self): pass 
