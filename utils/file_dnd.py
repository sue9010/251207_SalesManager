import os
import shutil
from datetime import datetime
import tkinter as tk
from tkinter import messagebox, filedialog
import customtkinter as ctk
from src.styles import COLORS, FONTS

try:
    from tkinterdnd2 import DND_FILES
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False

class FileDnDManager:
    def __init__(self, parent_popup):
        self.parent = parent_popup
        self.dm = parent_popup.dm
        self.file_entries = {} # {key: entry_widget}
        self.full_paths = {}   # {key: full_path}
        self.DND_AVAILABLE = DND_AVAILABLE

    def create_file_input_row(self, parent, label, key, placeholder="파일을 드래그하거나 열기 버튼을 클릭하세요", height=28):
        """Standard file input row creation"""
        if label:
            ctk.CTkLabel(parent, text=label, font=FONTS["main"], text_color=COLORS["text_dim"]).pack(anchor="w", pady=(5, 0))
        
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", pady=(2, 5))
        
        entry = ctk.CTkEntry(row, placeholder_text=placeholder, height=height)
        entry.pack(side="left", fill="x", expand=True)
        
        btn_find = ctk.CTkButton(row, text="찾기", width=50, height=height,
                      command=lambda: self.browse_file(key),
                      fg_color=COLORS["bg_dark"], text_color=COLORS["text"])
        btn_find.pack(side="left", padx=(5, 0))

        btn_open = ctk.CTkButton(row, text="열기", width=50, height=height,
                      command=lambda: self.open_file(key),
                      fg_color=COLORS["bg_light"], text_color=COLORS["text"])
        btn_open.pack(side="left", padx=(5, 0))
                      
        btn_delete = ctk.CTkButton(row, text="삭제", width=50, height=height,
                      command=lambda: self.clear_entry(key),
                      fg_color=COLORS["danger"], hover_color=COLORS["danger_hover"])
        btn_delete.pack(side="left", padx=(5, 0))
        
        self.file_entries[key] = entry
        
        # [변경] tkinterdnd2 적용
        if self.DND_AVAILABLE:
            self._setup_dnd(entry, key)
        
        return entry, btn_find, btn_open, btn_delete

    def browse_file(self, key):
        """Open file dialog to select a file"""
        file_path = filedialog.askopenfilename(parent=self.parent)
        if file_path:
            self.update_file_entry(key, file_path)

    def _setup_dnd(self, widget, key):
        """Setup tkinterdnd2 drop target"""
        # 위젯이 생성된 후 DnD 등록
        def register_dnd():
            try:
                # drop_target_register는 tkinterdnd2의 메서드입니다.
                # 위젯이 TkinterDnD.DnDWrapper를 상속받은 루트 윈도우의 자식이어야 합니다.
                widget.drop_target_register(DND_FILES)
                widget.dnd_bind('<<Drop>>', lambda e: self.on_drop(e, key))
            except Exception as e:
                print(f"DnD Registration Error ({key}): {e}")
        
        # 위젯이 완전히 생성될 때까지 잠시 대기 후 등록
        self.parent.after(200, register_dnd)

    def on_drop(self, event, key):
        """Handle dropped files (tkinterdnd2 event)"""
        # event.data는 '{path1} {path2}' 형태의 문자열일 수 있습니다 (공백 포함 시 중괄호로 감싸짐).
        # 여기서는 첫 번째 파일만 처리하는 간단한 파싱 로직을 사용합니다.
        raw_data = event.data
        if not raw_data: return

        # 중괄호 제거 및 첫 번째 경로 추출 (tkinterdnd2 특성상 경로에 공백이 있으면 {}로 감싸짐)
        if raw_data.startswith('{') and raw_data.endswith('}'):
            file_path = raw_data[1:-1]
        else:
            file_path = raw_data
            
        # 여러 파일이 드롭된 경우 첫 번째 파일만 취함 (간이 로직)
        # 더 정교한 파싱이 필요하다면 별도의 파서 사용 권장
        if '} {' in raw_data: # 여러 파일인 경우
             file_path = raw_data.split('} {')[0].replace('{', '')

        self.update_file_entry(key, file_path)

    def update_file_entry(self, key, full_path):
        """Update entry text and internal tracking"""
        if not full_path: return
        
        # 경로 정리 (윈도우 스타일 역슬래시 등)
        full_path = os.path.normpath(full_path)
        
        self.full_paths[key] = full_path
        
        if key in self.file_entries:
            entry = self.file_entries[key]
            try:
                entry.delete(0, "end")
                entry.insert(0, os.path.basename(full_path))
            except: pass

    def open_file(self, key):
        """Open the file associated with key"""
        path = self.full_paths.get(key)
        if not path and key in self.file_entries:
             path = self.file_entries[key].get().strip()
        
        if path and os.path.exists(path):
            try: os.startfile(path)
            except Exception as e: messagebox.showerror("에러", f"파일을 열 수 없습니다.\n{e}", parent=self.parent)
        else:
            messagebox.showwarning("경고", "파일 경로가 유효하지 않습니다.", parent=self.parent)

    def clear_entry(self, key, confirm=True):
        """Clear entry and optionally delete actual file if managed"""
        entry_widget = self.file_entries.get(key)
        if not entry_widget: return
        
        path = self.full_paths.get(key)
        if not path: path = entry_widget.get().strip()
        if not path: return

        # Check if file is managed (inside attachment root)
        is_managed = False
        try:
            abs_path = os.path.abspath(path)
            abs_root = os.path.abspath(self.dm.attachment_root)
            if abs_path.startswith(abs_root): is_managed = True
        except: pass

        if is_managed and confirm:
            if messagebox.askyesno("파일 삭제", f"정말 파일을 삭제하시겠습니까?\n(영구 삭제됨)", parent=self.parent):
                try:
                    if os.path.exists(path): os.remove(path)
                except Exception as e:
                    messagebox.showerror("오류", f"삭제 실패: {e}", parent=self.parent)
                    return
                entry_widget.delete(0, "end")
                if key in self.full_paths: del self.full_paths[key]
        else:
            entry_widget.delete(0, "end")
            if key in self.full_paths: del self.full_paths[key]

    def save_file(self, key, target_subdir, prefix, info_text):
        """
        Saves the file tracked by 'key' to 'attachment_root/target_subdir'.
        """
        current_path = self.full_paths.get(key, "")
        if not current_path and key in self.file_entries:
            current_path = self.file_entries[key].get().strip()
            
        if not current_path: return True, "", "" 
        
        # Clean up path (remove surrounding quotes if any)
        current_path = current_path.strip('"').strip("'")

        if not os.path.exists(current_path):
             return False, f"파일을 찾을 수 없습니다: {current_path}", ""

        # Target Directory
        target_dir = os.path.join(self.dm.attachment_root, target_subdir)
        if not os.path.exists(target_dir):
            try: os.makedirs(target_dir)
            except Exception as e: return False, f"폴더 생성 실패: {e}", ""

        # New Filename
        ext = os.path.splitext(current_path)[1]
        
        safe_prefix = "".join(c for c in prefix if c.isalnum() or c in (' ', '_', '-')).strip()
        safe_info = "".join(c for c in info_text if c.isalnum() or c in (' ', '_', '-')).strip()
        today_str = datetime.now().strftime("%y%m%d")
        
        new_name = f"{safe_prefix}_{safe_info}_{today_str}{ext}"
        target_path = os.path.join(target_dir, new_name)

        if os.path.abspath(current_path) != os.path.abspath(target_path):
            try:
                shutil.copy2(current_path, target_path)
                self.update_file_entry(key, target_path) 
                return True, "Success", target_path
            except Exception as e:
                return False, f"파일 복사 실패: {e}", ""
        
        return True, "Already in place", target_path