import getpass
import pandas as pd
from datetime import datetime

class LogHandler:
    def __init__(self, data_manager):
        self.dm = data_manager

    def create_log_entry(self, action, details):
        try: user = getpass.getuser()
        except: user = "Unknown"
        return {
            "일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "작업자": user,
            "구분": action,
            "상세내용": details
        }

    def add_log(self, action, details):
        try: user = getpass.getuser()
        except: user = "Unknown"
        new = {"일시": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "작업자": user, "구분": action, "상세내용": details}
        new_df = pd.DataFrame([new])
        if self.dm.df_log.empty: self.dm.df_log = new_df
        else: self.dm.df_log = pd.concat([self.dm.df_log, new_df], ignore_index=True)

    def add_log_to_dfs(self, dfs, action, details):
        new_log = self.create_log_entry(action, details)
        if "log" in dfs:
            dfs["log"] = pd.concat([dfs["log"], pd.DataFrame([new_log])], ignore_index=True)

    def clean_old_logs(self):
        return True, "로그 정리 완료"
