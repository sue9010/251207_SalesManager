import pandas as pd
from datetime import datetime
from src.config import Config

class OrderHandler:
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

    def get_next_quote_id(self):
        return self._generate_sequential_id(self.dm.df_data, "관리번호", "QT")

    def get_next_order_id(self):
        return self._generate_sequential_id(self.dm.df_data, "관리번호", "OD")

    def get_status_by_req_no(self, req_no):
        if self.dm.df_data.empty: return None
        rows = self.dm.df_data[self.dm.df_data["관리번호"] == req_no]
        return rows.iloc[0]["Status"] if not rows.empty else None

    def get_filtered_data(self, status_list=None, keyword=""):
        df = self.dm.df_data
        if df.empty: return df
        if status_list: df = df[df["Status"].isin(status_list)]
        if keyword:
            mask = pd.Series(False, index=df.index)
            for col in Config.SEARCH_TARGET_COLS:
                if col in df.columns:
                    mask |= df[col].astype(str).str.contains(keyword, case=False)
            df = df[mask]
        return df

    def add_order(self, order_rows: list[dict], mgmt_no: str, client_name: str) -> tuple[bool, str]:
        def update(dfs):
            # Initialize new status columns
            for row in order_rows:
                row["Delivery Status"] = "대기"
                row["Payment Status"] = "대기"
                
            new_df = pd.DataFrame(order_rows)
            if not new_df.dropna(how='all').empty:
                dfs["data"] = pd.concat([dfs["data"], new_df], ignore_index=True)
            self.dm.log_handler.add_log_to_dfs(dfs, "주문 등록", f"번호 [{mgmt_no}] / 업체 [{client_name}]")
            return True, ""
        return self.dm.execute_transaction(update)

    def update_order(self, mgmt_no: str, order_rows: list[dict], client_name: str, is_copy=False) -> tuple[bool, str]:
        def update(dfs):
            mask = dfs["data"]["관리번호"] == mgmt_no
            existing_rows = dfs["data"][mask]
            
            if not existing_rows.empty:
                first_exist = existing_rows.iloc[0]
                preserve_cols = ["출고예정일", "출고일", "입금완료일", "세금계산서발행일", "계산서번호", "수출신고번호", "Delivery Status", "Payment Status"]
                for row in order_rows:
                    for col in preserve_cols:
                        if col not in row:
                            row[col] = first_exist.get(col, "-")
            
            dfs["data"] = dfs["data"][~mask]
            
            new_df = pd.DataFrame(order_rows)
            if not new_df.dropna(how='all').empty:
                dfs["data"] = pd.concat([dfs["data"], new_df], ignore_index=True)
            
            action = "복사 등록" if is_copy else "수정"
            self.dm.log_handler.add_log_to_dfs(dfs, f"주문 {action}", f"번호 [{mgmt_no}] / 업체 [{client_name}]")
            return True, ""
        return self.dm.execute_transaction(update)

    def delete_order(self, mgmt_no: str) -> tuple[bool, str]:
        def update(dfs):
            mask = dfs["data"]["관리번호"] == mgmt_no
            if not mask.any(): return False, "데이터를 찾을 수 없습니다."
            
            dfs["data"] = dfs["data"][~mask]
            self.dm.log_handler.add_log_to_dfs(dfs, "삭제", f"주문 삭제: 번호 [{mgmt_no}]")
            return True, ""
        return self.dm.execute_transaction(update)

    def add_quote(self, quote_rows: list[dict], mgmt_no: str, client_name: str) -> tuple[bool, str]:
        def update(dfs):
            new_df = pd.DataFrame(quote_rows)
            if not new_df.dropna(how='all').empty:
                dfs["data"] = pd.concat([dfs["data"], new_df], ignore_index=True)
            self.dm.log_handler.add_log_to_dfs(dfs, "견적 등록", f"번호 [{mgmt_no}] / 업체 [{client_name}]")
            return True, ""
        return self.dm.execute_transaction(update)

    def update_quote(self, mgmt_no: str, quote_rows: list[dict], client_name: str, is_copy=False) -> tuple[bool, str]:
        def update(dfs):
            mask = dfs["data"]["관리번호"] == mgmt_no
            existing_rows = dfs["data"][mask]
            
            if not existing_rows.empty:
                first_exist = existing_rows.iloc[0]
                preserve_cols = ["수주일", "출고예정일", "출고일", "입금완료일", 
                                 "세금계산서발행일", "계산서번호", "수출신고번호", "발주서경로"]
                for row in quote_rows:
                    for col in preserve_cols:
                        if col not in row:
                            row[col] = first_exist.get(col, "-")
            
            dfs["data"] = dfs["data"][~mask]
            
            new_df = pd.DataFrame(quote_rows)
            if not new_df.dropna(how='all').empty:
                dfs["data"] = pd.concat([dfs["data"], new_df], ignore_index=True)
            
            action = "복사 등록" if is_copy else "수정"
            self.dm.log_handler.add_log_to_dfs(dfs, f"견적 {action}", f"번호 [{mgmt_no}] / 업체 [{client_name}]")
            return True, ""
        return self.dm.execute_transaction(update)

    def delete_quote(self, mgmt_no: str) -> tuple[bool, str]:
        def update(dfs):
            mask = dfs["data"]["관리번호"] == mgmt_no
            if not mask.any(): return False, "데이터를 찾을 수 없습니다."
            
            dfs["data"] = dfs["data"][~mask]
            self.dm.log_handler.add_log_to_dfs(dfs, "삭제", f"견적 삭제: 번호 [{mgmt_no}]")
            return True, ""
        return self.dm.execute_transaction(update)

    def process_after_sales(self, mgmt_nos, tax_date, tax_no, export_no, saved_paths):
        def update(dfs):
            mask = dfs["data"]["관리번호"].isin(mgmt_nos)
            if not mask.any():
                return False, "처리할 항목을 찾을 수 없습니다."

            # Update fields
            if tax_date: dfs["data"].loc[mask, "세금계산서발행일"] = tax_date
            if tax_no: dfs["data"].loc[mask, "계산서번호"] = tax_no
            if export_no: dfs["data"].loc[mask, "수출신고번호"] = export_no
            
            # Update file paths
            for col, path in saved_paths.items():
                dfs["data"].loc[mask, col] = path

            # Update Status to "종료"
            dfs["data"].loc[mask, "Status"] = "종료"

            # Log
            cnt = mask.sum()
            self.dm.log_handler.add_log_to_dfs(dfs, "사후처리", f"{cnt}건 처리 완료 (상태: 종료)")
            return True, ""

        return self.dm.execute_transaction(update)

    def update_status(self, mgmt_no: str, new_status: str, updates: dict = None) -> tuple[bool, str]:
        def update(dfs):
            mask = dfs["data"]["관리번호"] == mgmt_no
            if not mask.any(): return False, "항목을 찾을 수 없습니다."
            
            old_status = dfs["data"].loc[mask, "Status"].iloc[0]
            dfs["data"].loc[mask, "Status"] = new_status
            
            if updates:
                for key, value in updates.items():
                    if key in dfs["data"].columns:
                         dfs["data"].loc[mask, key] = value
            
            self.dm.log_handler.add_log_to_dfs(dfs, "상태 변경", f"번호 [{mgmt_no}] : {old_status} -> {new_status}")
            return True, ""
        return self.dm.execute_transaction(update)

    def update_order_fields(self, mgmt_no: str, updates: dict) -> tuple[bool, str]:
        def update(dfs):
            mask = dfs["data"]["관리번호"] == mgmt_no
            if not mask.any(): return False, "항목을 찾을 수 없습니다."
            
            for key, value in updates.items():
                if key in dfs["data"].columns:
                    dfs["data"].loc[mask, key] = value
            
            # 로그는 선택사항이지만 남기는 것이 좋음
            self.dm.log_handler.add_log_to_dfs(dfs, "정보 업데이트", f"번호 [{mgmt_no}] 필드 업데이트")
            return True, ""
        return self.dm.execute_transaction(update)

    def confirm_order(self, mgmt_no: str, confirm_data: dict) -> tuple[bool, str]:
        def update(dfs):
            mask = dfs["data"]["관리번호"] == mgmt_no
            if not mask.any(): return False, "항목을 찾을 수 없습니다."
            
            # Update Statuses
            dfs["data"].loc[mask, "Status"] = "주문"
            dfs["data"].loc[mask, "Delivery Status"] = "대기"
            dfs["data"].loc[mask, "Payment Status"] = "대기"
            
            # Update additional data
            for key, value in confirm_data.items():
                if key in dfs["data"].columns:
                    dfs["data"].loc[mask, key] = value
            
            self.dm.log_handler.add_log_to_dfs(dfs, "주문 확정", f"번호 [{mgmt_no}] 주문 확정 처리")
            return True, ""
        return self.dm.execute_transaction(update)
