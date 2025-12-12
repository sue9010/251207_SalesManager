import os
import json
import shutil
import pandas as pd
from datetime import datetime
from src.config import Config

class FileHandler:
    def __init__(self, data_manager):
        self.dm = data_manager

    def load_config(self):
        if os.path.exists(Config.CONFIG_FILENAME):
            try:
                with open(Config.CONFIG_FILENAME, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.dm.current_excel_path = data.get("excel_path", Config.DEFAULT_EXCEL_PATH)
                    self.dm.current_theme = data.get("theme", "Dark")
                    self.dm.attachment_root = data.get("attachment_root", Config.DEFAULT_ATTACHMENT_ROOT)
                    self.dm.production_request_path = data.get("production_request_path", Config.DEFAULT_PRODUCTION_REQUEST_PATH)
                    self.dm.purchase_data_path = data.get("purchase_data_path", Config.DEFAULT_PURCHASE_DATA_PATH)
            except: pass

    def save_config(self, new_path=None, new_theme=None, new_attachment_dir=None, new_prod_path=None, new_purchase_path=None):
        if new_path: self.dm.current_excel_path = new_path
        if new_theme: self.dm.current_theme = new_theme
        if new_attachment_dir: self.dm.attachment_root = new_attachment_dir
        if new_prod_path: self.dm.production_request_path = new_prod_path
        if new_purchase_path: self.dm.purchase_data_path = new_purchase_path
        
        data = {
            "excel_path": self.dm.current_excel_path,
            "theme": self.dm.current_theme,
            "attachment_root": self.dm.attachment_root,
            "production_request_path": self.dm.production_request_path,
            "purchase_data_path": self.dm.purchase_data_path
        }
        try:
            with open(Config.CONFIG_FILENAME, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"설정 저장 실패: {e}")

    def _get_columns_for_key(self, key):
        if key == "clients": return Config.CLIENT_COLUMNS
        elif key == "data": return Config.DATA_COLUMNS
        elif key == "payment": return Config.PAYMENT_COLUMNS
        elif key == "delivery": return Config.DELIVERY_COLUMNS
        elif key == "log": return Config.LOG_COLUMNS
        elif key == "memo": return Config.MEMO_COLUMNS
        elif key == "memo_log": return Config.MEMO_LOG_COLUMNS
        return []

    def read_all_sheets(self) -> dict[str, pd.DataFrame]:
        dfs = {}
        if not os.path.exists(self.dm.current_excel_path):
            keys = ["clients", "data", "payment", "delivery", "log", "memo", "memo_log"]
            for key in keys:
                dfs[key] = pd.DataFrame(columns=self._get_columns_for_key(key))
            return dfs

        try:
            with open(self.dm.current_excel_path, "rb") as f:
                with pd.ExcelFile(f, engine="openpyxl") as xls:
                    sheet_names = xls.sheet_names
                    
                    sheet_map = {
                        Config.SHEET_CLIENTS: "clients",
                        Config.SHEET_DATA: "data",
                        Config.SHEET_PAYMENT: "payment",
                        Config.SHEET_DELIVERY: "delivery",
                        Config.SHEET_LOG: "log",
                        Config.SHEET_MEMO: "memo",
                        Config.SHEET_MEMO_LOG: "memo_log"
                    }
                    
                    for sheet_name, key in sheet_map.items():
                        if sheet_name in sheet_names:
                            df = pd.read_excel(xls, sheet_name)
                            if key in ["clients", "data"]:
                                df.columns = df.columns.astype(str).str.strip()
                            dfs[key] = df
                        else:
                            dfs[key] = pd.DataFrame(columns=self._get_columns_for_key(key))
                            
            return dfs
        except Exception as e:
            print(f"Error reading sheets: {e}")
            return {}

    def normalize_all(self, dfs: dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame]:
        keys = ["clients", "data", "payment", "delivery", "log", "memo", "memo_log"]
        for key in keys:
            if key not in dfs:
                dfs[key] = pd.DataFrame(columns=self._get_columns_for_key(key))

        if "data" in dfs:
            for col in Config.DATA_COLUMNS:
                if col not in dfs["data"].columns: dfs["data"][col] = "-"
            dfs["data"] = dfs["data"].fillna("-")
            
            num_cols = ["수량", "단가", "환율", "세율(%)", "공급가액", "세액", "합계금액", "기수금액", "미수금액"]
            for col in num_cols:
                if col in dfs["data"].columns:
                    dfs["data"][col] = pd.to_numeric(dfs["data"][col], errors='coerce').fillna(0)

            date_cols = ["견적일", "수주일", "출고예정일", "출고일", "선적일", "입금완료일", "세금계산서발행일"]
            for col in date_cols:
                if col in dfs["data"].columns:
                    dfs["data"][col] = pd.to_datetime(dfs["data"][col], errors='coerce', format='mixed').dt.strftime("%Y-%m-%d")
                    dfs["data"][col] = dfs["data"][col].fillna("-")

        if "clients" in dfs:
            dfs["clients"] = dfs["clients"].fillna("-")

        if "payment" in dfs:
            # Ensure new columns are string type
            str_cols = ["세금계산서번호", "세금계산서발행일"]
            for col in str_cols:
                if col not in dfs["payment"].columns:
                    dfs["payment"][col] = ""
                dfs["payment"][col] = dfs["payment"][col].astype(str).replace("nan", "")

        if "delivery" in dfs:
            if "출고번호" not in dfs["delivery"].columns:
                dfs["delivery"]["출고번호"] = "-"
            for col in Config.DELIVERY_COLUMNS:
                if col not in dfs["delivery"].columns: dfs["delivery"][col] = "-"
            dfs["delivery"] = dfs["delivery"].fillna("-")
            
            # Ensure new columns are string type
            str_cols = ["수출신고번호", "수출신고필증경로"]
            for col in str_cols:
                if col in dfs["delivery"].columns:
                    dfs["delivery"][col] = dfs["delivery"][col].astype(str).replace("nan", "")

        return dfs

    def write_all_sheets(self, dfs: dict[str, pd.DataFrame]) -> None:
        with pd.ExcelWriter(self.dm.current_excel_path, engine="openpyxl") as writer:
            sheet_map = {
                "clients": Config.SHEET_CLIENTS,
                "data": Config.SHEET_DATA,
                "payment": Config.SHEET_PAYMENT,
                "delivery": Config.SHEET_DELIVERY,
                "log": Config.SHEET_LOG,
                "memo": Config.SHEET_MEMO,
                "memo_log": Config.SHEET_MEMO_LOG
            }
            for key, sheet_name in sheet_map.items():
                if key in dfs:
                    dfs[key].to_excel(writer, sheet_name=sheet_name, index=False)

    def load_data(self):
        try:
            dfs = self.read_all_sheets()
            dfs = self.normalize_all(dfs)
            
            self.dm.df_clients = dfs["clients"]
            self.dm.df_data = dfs["data"]
            self.dm.df_payment = dfs["payment"]
            self.dm.df_delivery = dfs["delivery"]
            self.dm.df_log = dfs["log"]
            self.dm.df_memo = dfs["memo"]
            self.dm.df_memo_log = dfs["memo_log"]
            
            if os.path.exists(self.dm.current_excel_path):
                self.dm.last_file_timestamp = os.path.getmtime(self.dm.current_excel_path)
                
            return True, "데이터 로드 완료"
        except Exception as e:
            return False, f"오류 발생: {e}"

    def check_for_external_changes(self):
        if not os.path.exists(self.dm.current_excel_path): return False
        try:
            current_mtime = os.path.getmtime(self.dm.current_excel_path)
            if current_mtime > self.dm.last_file_timestamp: return True
        except OSError: pass
        return False

    def save_to_excel(self):
        try:
            with pd.ExcelWriter(self.dm.current_excel_path, engine="openpyxl") as writer:
                self.dm.df_clients.to_excel(writer, sheet_name=Config.SHEET_CLIENTS, index=False)
                self.dm.df_data.to_excel(writer, sheet_name=Config.SHEET_DATA, index=False)
                self.dm.df_payment.to_excel(writer, sheet_name=Config.SHEET_PAYMENT, index=False)
                self.dm.df_delivery.to_excel(writer, sheet_name=Config.SHEET_DELIVERY, index=False)
                self.dm.df_log.to_excel(writer, sheet_name=Config.SHEET_LOG, index=False)
                self.dm.df_memo.to_excel(writer, sheet_name=Config.SHEET_MEMO, index=False)
                self.dm.df_memo_log.to_excel(writer, sheet_name=Config.SHEET_MEMO_LOG, index=False)
            return True, "저장 완료"
        except PermissionError:
            return False, "엑셀 파일이 열려있습니다."
        except Exception as e:
            return False, f"저장 실패: {e}"

    def load_purchase_data(self):
        """구매 엑셀 파일을 로드하여 DataFrame 반환"""
        if not os.path.exists(self.dm.purchase_data_path):
            try:
                dirname = os.path.dirname(self.dm.purchase_data_path)
                if dirname:
                    os.makedirs(dirname, exist_ok=True)
                with pd.ExcelWriter(self.dm.purchase_data_path, engine="openpyxl") as writer:
                    pd.DataFrame(columns=Config.PURCHASE_COLUMNS).to_excel(writer, sheet_name="Data", index=False)
                return pd.DataFrame(columns=Config.PURCHASE_COLUMNS), "새로운 구매 데이터 파일 생성됨"
            except Exception as e:
                return None, f"구매 파일 생성 실패: {e}"
        
        try:
            df = pd.read_excel(self.dm.purchase_data_path, sheet_name="Data", engine="openpyxl")
            for col in Config.PURCHASE_COLUMNS:
                if col not in df.columns:
                    df[col] = ""
            df = df.fillna("")
            return df, "구매 데이터 로드 성공"
        except Exception as e:
            return None, f"구매 데이터 읽기 실패: {e}"

    def save_purchase_data(self):
        try:
            with pd.ExcelWriter(self.dm.purchase_data_path, engine="openpyxl") as writer:
                self.dm.df_purchase.to_excel(writer, sheet_name="Data", index=False)
            return True, "구매 데이터 저장 완료"
        except PermissionError:
            return False, "구매 데이터 파일이 열려있습니다."
        except Exception as e:
            return False, f"구매 데이터 저장 실패: {e}"


    def create_backup(self):
        if not os.path.exists(self.dm.current_excel_path): return False, "파일 없음"
        try:
            folder = os.path.dirname(self.dm.current_excel_path)
            backup_folder = os.path.join(folder, "backup")
            if not os.path.exists(backup_folder): os.makedirs(backup_folder)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            fname = os.path.basename(self.dm.current_excel_path)
            shutil.copy2(self.dm.current_excel_path, os.path.join(backup_folder, f"{fname}_{timestamp}.bak"))
            return True, "백업 완료"
        except Exception as e: return False, str(e)

    def save_attachment(self, source_path, company_name, file_prefix):
        if not os.path.exists(source_path): return None, "파일 없음"
        try:
            current_year = datetime.now().strftime("%Y")
            year_dir = os.path.join(self.dm.attachment_root, current_year)
            if not os.path.exists(year_dir): os.makedirs(year_dir)

            safe_name = "".join([c for c in str(company_name) if c.isalnum() or c in (' ', '_', '-')]).strip()
            comp_dir = os.path.join(year_dir, safe_name)
            if not os.path.exists(comp_dir): os.makedirs(comp_dir)

            fname = os.path.basename(source_path)
            name, ext = os.path.splitext(fname)
            today = datetime.now().strftime("%Y%m%d")
            new_name = f"{file_prefix}_{today}_{name}{ext}"
            
            dest_path = os.path.join(comp_dir, new_name)
            shutil.copy2(source_path, dest_path)
            return dest_path, None
        except Exception as e:
            return None, str(e)
