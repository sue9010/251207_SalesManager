import pandas as pd
from datetime import datetime
from src.config import Config

class PurchaseHandler:
    def __init__(self, data_manager):
        self.dm = data_manager

    def _generate_sequential_id(self, df, id_col, prefix):
        today = datetime.now().strftime("%y%m%d")
        prefix_date = f"{prefix}-{today}-"
        
        max_seq = 0
        if not df.empty and id_col in df.columns:
            def extract_seq(val):
                s = str(val)
                if s.startswith(prefix_date):
                    try: return int(s.split("-")[-1])
                    except: return 0
                return 0
            
            seqs = df[id_col].apply(extract_seq)
            if not seqs.empty: max_seq = seqs.max()
        
        next_seq = max_seq + 1
        return f"{prefix_date}{next_seq:03d}"

    def get_next_purchase_id(self):
        return self._generate_sequential_id(self.dm.df_purchase, "관리번호", "PU")

    def add_purchase(self, rows: list[dict]) -> tuple[bool, str]:
        def update(dfs):
            if "purchase" not in dfs:
                dfs["purchase"] = pd.DataFrame(columns=Config.PURCHASE_COLUMNS)
            
            new_df = pd.DataFrame(rows)
            if not new_df.dropna(how='all').empty:
                if dfs["purchase"].empty:
                    dfs["purchase"] = new_df
                else:
                    dfs["purchase"] = pd.concat([dfs["purchase"], new_df], ignore_index=True)
            
            mgmt_no = rows[0].get('관리번호', '?') if rows else '?'
            client_name = rows[0].get('업체명', '?') if rows else '?'
            self.dm.log_handler.add_log_to_dfs(dfs, "발주 등록", f"번호 [{mgmt_no}] / 업체 [{client_name}]")
            return True, ""
        return self.dm.execute_transaction(update)

    def update_purchase(self, mgmt_no: str, rows: list[dict]) -> tuple[bool, str]:
        def update(dfs):
            if "purchase" not in dfs:
                return False, "구매 데이터가 로드되지 않았습니다."

            mask = dfs["purchase"]["관리번호"] == mgmt_no
            # 기존 데이터 삭제 (덮어쓰기 위해)
            dfs["purchase"] = dfs["purchase"][~mask]
            
            # 새 데이터 추가
            new_df = pd.DataFrame(rows)
            if not new_df.dropna(how='all').empty:
                if dfs["purchase"].empty:
                    dfs["purchase"] = new_df
                else:
                    dfs["purchase"] = pd.concat([dfs["purchase"], new_df], ignore_index=True)
            
            self.dm.log_handler.add_log_to_dfs(dfs, "발주 수정", f"번호 [{mgmt_no}]")
            return True, ""
        return self.dm.execute_transaction(update)

    def delete_purchase(self, mgmt_no: str) -> tuple[bool, str]:
        def update(dfs):
            if "purchase" not in dfs:
                return False, "구매 데이터가 로드되지 않았습니다."
            
            mask = dfs["purchase"]["관리번호"] == mgmt_no
            if not mask.any(): return False, "삭제할 항목을 찾을 수 없습니다."
            
            dfs["purchase"] = dfs["purchase"][~mask]
            self.dm.log_handler.add_log_to_dfs(dfs, "발주 삭제", f"번호 [{mgmt_no}]")
            return True, ""
        return self.dm.execute_transaction(update)
