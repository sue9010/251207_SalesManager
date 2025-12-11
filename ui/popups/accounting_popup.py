import customtkinter as ctk
from tkinter import messagebox
from ui.popups.base_popup import BasePopup
from src.styles import COLORS, FONTS

class AccountingPopup(BasePopup):
    def __init__(self, parent, data_manager, refresh_callback, mgmt_nos):
        if isinstance(mgmt_nos, list):
            self.mgmt_nos = mgmt_nos
        else:
            self.mgmt_nos = [mgmt_nos]

        if not self.mgmt_nos:
            messagebox.showerror("오류", "처리할 대상이 지정되지 않았습니다.", parent=parent)
            self.destroy()
            return

        super().__init__(parent, data_manager, refresh_callback, popup_title="회계처리", mgmt_no=self.mgmt_nos[0])
        self.geometry("1000x600")

    def _setup_info_panel(self, parent):
        ctk.CTkLabel(parent, text="기본 정보", font=FONTS["header"]).pack(anchor="w", padx=10, pady=10)
        
        self.lbl_info = ctk.CTkLabel(parent, text="", justify="left", font=FONTS["main"])
        self.lbl_info.pack(anchor="w", padx=10)

    def _setup_items_panel(self, parent):
        ctk.CTkLabel(parent, text="품목 리스트", font=FONTS["header"]).pack(anchor="w", padx=10, pady=10)
        
        self.scroll_items = ctk.CTkScrollableFrame(parent, fg_color="transparent")
        self.scroll_items.pack(fill="both", expand=True, padx=10, pady=5)

    def _load_data(self):
        # Load Basic Info
        if self.mgmt_nos:
            df = self.dm.df_data
            row = df[df["관리번호"] == self.mgmt_nos[0]]
            if not row.empty:
                info_text = f"관리번호: {self.mgmt_nos[0]}\n"
                info_text += f"업체명: {row.iloc[0].get('업체명', '')}\n"
                info_text += f"프로젝트명: {row.iloc[0].get('프로젝트명', '')}\n"
                self.lbl_info.configure(text=info_text)

        # Load Items
        # Clear existing items
        for widget in self.scroll_items.winfo_children():
            widget.destroy()

        df = self.dm.df_data
        rows = df[df["관리번호"].isin(self.mgmt_nos)]
        
        for _, row in rows.iterrows():
            item_text = f"{row.get('품목명', '')} - {row.get('모델명', '')} ({row.get('수량', '')})"
            ctk.CTkLabel(self.scroll_items, text=item_text, anchor="w").pack(fill="x", padx=5, pady=2)

    def _create_footer(self, parent):
        footer_frame = ctk.CTkFrame(parent, height=60, fg_color="transparent")
        footer_frame.pack(fill="x", pady=(10, 0), side="bottom")
        
        ctk.CTkButton(footer_frame, text="닫기", command=self.destroy, width=100, height=40,
                      fg_color=COLORS["bg_light"], hover_color=COLORS["bg_light_hover"], 
                      text_color=COLORS["text"]).pack(side="right", padx=10)
                      
    def save(self):
        pass

    def delete(self):
        pass
