import pandas as pd

class ClientHandler:
    def __init__(self, data_manager):
        self.dm = data_manager

    def get_client_shipping_method(self, client_name):
        if self.dm.df_clients.empty:
            return ""
            
        row = self.dm.df_clients[self.dm.df_clients["업체명"] == client_name]
        if not row.empty:
            val = row.iloc[0].get("운송방법", "")
            return str(val).strip() if str(val).lower() != "nan" else ""
        return ""

    def get_client_shipping_account(self, client_name):
        if self.dm.df_clients.empty:
            return ""
            
        row = self.dm.df_clients[self.dm.df_clients["업체명"] == client_name]
        if not row.empty:
            val = row.iloc[0].get("운송계정", "")
            return str(val).strip() if str(val).lower() != "nan" else ""
        return ""

    def add_client(self, client_data: dict) -> tuple[bool, str]:
        def update(dfs):
            if client_data.get("업체명") in dfs["clients"]["업체명"].values:
                return False, "이미 존재하는 업체명입니다."
            
            new_df = pd.DataFrame([client_data])
            if not new_df.dropna(how='all').empty:
                dfs["clients"] = pd.concat([dfs["clients"], new_df], ignore_index=True)
            self.dm.log_handler.add_log_to_dfs(dfs, "업체 등록", f"업체명: {client_data.get('업체명')}")
            return True, ""
        return self.dm.execute_transaction(update)

    def update_client(self, original_name, client_data: dict) -> tuple[bool, str]:
        def update(dfs):
            mask = dfs["clients"]["업체명"] == original_name
            if not mask.any(): return False, "업체를 찾을 수 없습니다."
            
            idx = dfs["clients"][mask].index[0]
            for k, v in client_data.items():
                dfs["clients"].at[idx, k] = v
                
            self.dm.log_handler.add_log_to_dfs(dfs, "업체 수정", f"업체명: {original_name}")
            return True, ""
        return self.dm.execute_transaction(update)

    def delete_client(self, client_name) -> tuple[bool, str]:
        def update(dfs):
            mask = dfs["clients"]["업체명"] == client_name
            if not mask.any(): return False, "업체를 찾을 수 없습니다."
            
            dfs["clients"] = dfs["clients"][~mask]
            self.dm.log_handler.add_log_to_dfs(dfs, "업체 삭제", f"업체명: {client_name}")
            return True, ""
        return self.dm.execute_transaction(update)
