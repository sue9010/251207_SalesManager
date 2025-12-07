import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog

import customtkinter as ctk

# [변경] 경로 수정
from src.config import Config
from src.styles import COLORS, FONT_FAMILY, FONTS


class SettingsPopup(ctk.CTkToplevel):
    def __init__(self, parent, data_manager, refresh_callback):
        super().__init__(parent)
        self.dm = data_manager
        self.refresh_callback = refresh_callback
        
        self.title("환경 설정")
        # [수정] 창 크기를 넉넉하게 설정 (600x900)
        self.geometry("600x900")
        
        self.center_window(600, 900)
        
        # [수정] 모달 설정 (순서 중요)
        self.transient(parent)
        self.grab_set()
        
        self.create_widgets()
        
        # [수정] 팝업을 최상위로 강제 이동 및 포커스
        self.lift()
        self.focus_force()
        self.attributes("-topmost", True)
        
        # ESC 닫기
        self.bind("<Escape>", lambda e: self.destroy())

    def center_window(self, width, height):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width / 2) - (width / 2)
        y = (screen_height / 2) - (height / 2)
        self.geometry(f"{width}x{height}+{int(x)}+{int(y)}")

    def create_widgets(self):
        # [수정] 하단 저장 버튼을 먼저 배치 (스크롤 영역 밖, 하단 고정)
        btn_frame = ctk.CTkFrame(self, fg_color="transparent", height=60)
        btn_frame.pack(side="bottom", fill="x", padx=20, pady=20)
        
        ctk.CTkButton(btn_frame, text="설정 저장 및 닫기", command=self.save, height=40,
                      fg_color=COLORS["primary"], hover_color=COLORS["primary_hover"], font=FONTS["header"]).pack(fill="x")

        # [수정] 스크롤 프레임을 나머지 영역에 꽉 차게 배치
        self.scroll_frame = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll_frame.pack(side="top", fill="both", expand=True, padx=10, pady=10)
        
        parent = self.scroll_frame

        # 1. 테마 설정 섹션
        ctk.CTkLabel(parent, text="테마 설정 (Appearance)", font=FONTS["header"]).pack(pady=(10, 5), anchor="w")
        
        theme_frame = ctk.CTkFrame(parent, fg_color="transparent")
        theme_frame.pack(fill="x")
        
        self.theme_var = ctk.StringVar(value=self.dm.current_theme)
        
        self.theme_switch = ctk.CTkSegmentedButton(
            theme_frame, 
            values=["Light", "Dark"], 
            variable=self.theme_var,
            command=self.change_theme,
            font=(FONT_FAMILY, 12, "bold"),
            selected_color=COLORS["primary"],
            selected_hover_color=COLORS["primary_hover"]
        )
        self.theme_switch.pack(fill="x")

        ctk.CTkFrame(parent, height=1, fg_color=COLORS["border"]).pack(fill="x", pady=15)

        # 2. 엑셀 파일 경로 설정 섹션
        ctk.CTkLabel(parent, text="영업 데이터 파일 경로 (SalesList)", font=FONTS["header"]).pack(pady=(0, 5), anchor="w")

        path_frame = ctk.CTkFrame(parent, fg_color="transparent")
        path_frame.pack(fill="x")

        self.path_entry = ctk.CTkEntry(path_frame, font=FONTS["main"])
        self.path_entry.insert(0, self.dm.current_excel_path)
        self.path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkButton(path_frame, text="찾기", width=60, command=self.browse_excel, 
                      fg_color=COLORS["bg_medium"], text_color=COLORS["text"]).pack(side="right")
        
        # 3. 첨부 파일 저장 경로 설정 섹션
        ctk.CTkLabel(parent, text="첨부 파일 저장 폴더 (Root)", font=FONTS["header"]).pack(pady=(15, 5), anchor="w")

        attach_frame = ctk.CTkFrame(parent, fg_color="transparent")
        attach_frame.pack(fill="x")

        self.attach_path_entry = ctk.CTkEntry(attach_frame, font=FONTS["main"])
        self.attach_path_entry.insert(0, self.dm.attachment_root)
        self.attach_path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkButton(attach_frame, text="폴더선택", width=80, command=self.browse_folder, 
                      fg_color=COLORS["bg_medium"], text_color=COLORS["text"]).pack(side="right")

        ctk.CTkFrame(parent, height=1, fg_color=COLORS["border"]).pack(fill="x", pady=15)

        # 4. 생산 요청 파일 경로 설정
        ctk.CTkLabel(parent, text="생산 요청 파일 경로 (출고관리)", font=FONTS["header"]).pack(pady=(0, 5), anchor="w")

        prod_frame = ctk.CTkFrame(parent, fg_color="transparent")
        prod_frame.pack(fill="x")

        self.prod_path_entry = ctk.CTkEntry(prod_frame, font=FONTS["main"])
        self.prod_path_entry.insert(0, self.dm.production_request_path)
        self.prod_path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkButton(prod_frame, text="찾기", width=60, command=self.browse_production_file, 
                      fg_color=COLORS["bg_medium"], text_color=COLORS["text"]).pack(side="right")

        # 5. 출고요청서 저장 폴더 설정 (이 부분이 잘려서 안 보였음)
        ctk.CTkLabel(parent, text="출고요청서 저장 폴더 (PDF)", font=FONTS["header"]).pack(pady=(15, 5), anchor="w")

        order_req_frame = ctk.CTkFrame(parent, fg_color="transparent")
        order_req_frame.pack(fill="x")

        self.order_req_path_entry = ctk.CTkEntry(order_req_frame, font=FONTS["main"])
        self.order_req_path_entry.insert(0, self.dm.order_request_dir)
        self.order_req_path_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        ctk.CTkButton(order_req_frame, text="폴더선택", width=80, command=self.browse_order_req_folder, 
                      fg_color=COLORS["bg_medium"], text_color=COLORS["text"]).pack(side="right")

        ctk.CTkFrame(parent, height=1, fg_color=COLORS["border"]).pack(fill="x", pady=15)

        # 6. 개발자 모드 설정
        dev_frame = ctk.CTkFrame(parent, fg_color="transparent")
        dev_frame.pack(fill="x")
        
        self.dev_var = ctk.BooleanVar(value=self.dm.is_dev_mode)
        
        ctk.CTkSwitch(
            dev_frame, 
            text="관리자/개발자 모드 활성화", 
            variable=self.dev_var,
            command=self.toggle_dev_mode,
            font=FONTS["main_bold"],
            progress_color=COLORS["danger"]
        ).pack(side="left")

        self.dev_tools_frame = ctk.CTkFrame(parent, fg_color="transparent")
        if self.dm.is_dev_mode:
            self.show_dev_tools()

        # 하단 빈 공간 확보 (스크롤 끝까지 내렸을 때 여유)
        ctk.CTkFrame(parent, height=20, fg_color="transparent").pack()

    def show_dev_tools(self):
        self.dev_tools_frame.pack(fill="x", pady=(10, 0))
        for widget in self.dev_tools_frame.winfo_children(): widget.destroy()
        
        ctk.CTkButton(self.dev_tools_frame, text="💾 데이터 백업 생성", height=30,
                      fg_color=COLORS["success"], hover_color="#26A65B", command=self.do_backup).pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        ctk.CTkButton(self.dev_tools_frame, text="🧹 오래된 로그 정리", height=30,
                      fg_color=COLORS["warning"], hover_color="#D35400", command=self.do_clean_logs).pack(side="right", fill="x", expand=True, padx=(5, 0))

    def change_theme(self, new_theme):
        ctk.set_appearance_mode(new_theme)

    def browse_excel(self):
        self.attributes("-topmost", False)
        file_path = filedialog.askopenfilename(parent=self, filetypes=[("Excel files", "*.xlsx;*.xls;*.xlsm")])
        self.attributes("-topmost", True)
        if file_path:
            self.path_entry.delete(0, "end")
            self.path_entry.insert(0, file_path)

    def browse_production_file(self):
        self.attributes("-topmost", False)
        file_path = filedialog.askopenfilename(parent=self, filetypes=[("Excel files", "*.xlsx;*.xls;*.xlsm")])
        self.attributes("-topmost", True)
        if file_path:
            self.prod_path_entry.delete(0, "end")
            self.prod_path_entry.insert(0, file_path)

    def browse_folder(self):
        self.attributes("-topmost", False)
        folder_path = filedialog.askdirectory(parent=self)
        self.attributes("-topmost", True)
        if folder_path:
            self.attach_path_entry.delete(0, "end")
            self.attach_path_entry.insert(0, folder_path)

    def browse_order_req_folder(self):
        self.attributes("-topmost", False)
        folder_path = filedialog.askdirectory(parent=self)
        self.attributes("-topmost", True)
        if folder_path:
            self.order_req_path_entry.delete(0, "end")
            self.order_req_path_entry.insert(0, folder_path)

    def toggle_dev_mode(self):
        if self.dev_var.get():
            self.attributes("-topmost", False)
            pwd = simpledialog.askstring("관리자 인증", "관리자 비밀번호를 입력하세요:", show="*", parent=self)
            self.attributes("-topmost", True)
            
            if pwd == Config.DEV_PASSWORD:
                self.dm.set_dev_mode(True)
                messagebox.showinfo("인증 성공", "관리자 모드가 활성화되었습니다.", parent=self)
                self.show_dev_tools()
            else:
                self.dev_var.set(False)
                messagebox.showerror("인증 실패", "비밀번호가 올바르지 않습니다.", parent=self)
        else:
            self.dm.set_dev_mode(False)
            self.dev_tools_frame.pack_forget()

    def do_backup(self):
        self.attributes("-topmost", False)
        if messagebox.askyesno("백업", "현재 데이터 파일의 백업본을 생성하시겠습니까?", parent=self):
            success, msg = self.dm.create_backup()
            if success:
                messagebox.showinfo("성공", msg, parent=self)
            else:
                messagebox.showerror("실패", msg, parent=self)
        self.attributes("-topmost", True)

    def do_clean_logs(self):
        self.attributes("-topmost", False)
        if messagebox.askyesno("로그 정리", "오래된 로그 데이터를 정리하시겠습니까?", parent=self):
            success, msg = self.dm.clean_old_logs()
            messagebox.showinfo("완료", msg, parent=self)
        self.attributes("-topmost", True)

    def save(self):
        new_path = self.path_entry.get()
        new_theme = self.theme_var.get()
        new_attach = self.attach_path_entry.get()
        new_prod_path = self.prod_path_entry.get()
        new_order_req = self.order_req_path_entry.get() 
        
        if new_path:
            self.dm.save_config(
                new_path=new_path, 
                new_theme=new_theme, 
                new_attachment_dir=new_attach,
                new_prod_path=new_prod_path,
                new_order_req_dir=new_order_req 
            )
            
            self.attributes("-topmost", False)
            messagebox.showinfo("설정 저장", "설정이 저장되었습니다.", parent=self)
            self.destroy()
            
            if self.refresh_callback:
                self.refresh_callback()
        else:
            messagebox.showwarning("경고", "엑셀 파일 경로를 입력해주세요.", parent=self)