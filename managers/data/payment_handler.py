import getpass
import pandas as pd
from datetime import datetime

class PaymentHandler:
    def __init__(self, data_manager):
        self.dm = data_manager

    def recalc_payment_status(self, dfs, mgmt_no):
        pay_df = dfs["payment"]
        if pay_df.empty:
            total_paid = 0
            last_pay_date = "-"
        else:
            target_pays = pay_df[pay_df["관리번호"].astype(str) == str(mgmt_no)]
            paid_series = target_pays["입금액"].astype(str).str.replace(",", "").replace("nan", "0")
            total_paid = pd.to_numeric(paid_series, errors='coerce').sum()
            
            if not target_pays.empty:
                target_pays = target_pays.sort_values(by="일시", ascending=False)
                last_pay_date = target_pays.iloc[0]["일시"].split(" ")[0]
            else:
                last_pay_date = "-"

        data_df = dfs["data"]
        mask = data_df["관리번호"] == mgmt_no
        indices = data_df[mask].index
        
        if len(indices) == 0: return

        amt_series = data_df.loc[mask, "합계금액"].astype(str).str.replace(",", "").replace("nan", "0")
        total_contract_amt = pd.to_numeric(amt_series, errors='coerce').sum()
        
        remaining_to_allocate = total_paid
        
        for idx in indices:
            val_str = str(data_df.at[idx, "합계금액"]).replace(",", "")
            try: row_total = float(val_str)
            except: row_total = 0
            
            if remaining_to_allocate >= row_total:
                allocated = row_total
            else:
                allocated = remaining_to_allocate
                if allocated < 0: allocated = 0
            
            data_df.at[idx, "기수금액"] = allocated
            data_df.at[idx, "미수금액"] = row_total - allocated
            
            remaining_to_allocate -= allocated
            
            try: row_unpaid = float(data_df.at[idx, "미수금액"])
            except: row_unpaid = 0
            
            current_status = str(data_df.at[idx, "Status"])
            
            if row_unpaid < 1:
                if "납품" in current_status or "완료" in current_status:
                    new_status = "완료"
                else:
                    new_status = "납품대기/입금완료"
                data_df.at[idx, "입금완료일"] = last_pay_date
            else:
                if current_status == "완료": new_status = "납품완료/입금완료"
                elif current_status == "납품대기/입금완료": new_status = current_status
                else: new_status = current_status
            
            data_df.at[idx, "Status"] = new_status

    def add_payment(self, payment_data: dict) -> tuple[bool, str]:
        def update(dfs):
            new_df = pd.DataFrame([payment_data])
            if not new_df.dropna(how='all').empty:
                dfs["payment"] = pd.concat([dfs["payment"], new_df], ignore_index=True)
            
            mgmt_no = payment_data.get("관리번호")
            if mgmt_no:
                self.recalc_payment_status(dfs, mgmt_no)
                
            self.dm.log_handler.add_log_to_dfs(dfs, "입금 등록", f"관리번호: {mgmt_no}, 금액: {payment_data.get('입금액')}")
            return True, ""
        return self.dm.execute_transaction(update)

    def process_payment(self, mgmt_nos, payment_amount, payment_date, file_paths, confirm_fee_callback=None):
        def update(dfs):
            mask = dfs["data"]["관리번호"].isin(mgmt_nos)
            if not mask.any(): return False, "데이터를 찾을 수 없습니다."

            indices = dfs["data"][mask].index
            
            # 1. 강제 재계산
            for mgmt_no in mgmt_nos:
                self.recalc_payment_status(dfs, mgmt_no)

            # 2. 배치 처리용 집계
            batch_summary = {}
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            try: current_user = getpass.getuser()
            except: current_user = "Unknown"

            remaining_payment = payment_amount

            # 3. 미수금 차감 시뮬레이션
            for idx in indices:
                if remaining_payment <= 0: break
                
                mgmt_no = dfs["data"].at[idx, "관리번호"]
                currency = str(dfs["data"].at[idx, "통화"]).upper()
                threshold = 200 if currency != "KRW" else 5000
                
                if mgmt_no not in batch_summary:
                    batch_summary[mgmt_no] = {'deposit': 0, 'fee': 0, 'currency': currency}

                try: unpaid = float(dfs["data"].at[idx, "미수금액"])
                except: unpaid = 0
                
                if unpaid > 0:
                    actual_pay = 0
                    fee_pay = 0
                    
                    if remaining_payment >= unpaid:
                        actual_pay = unpaid
                    else:
                        diff = unpaid - remaining_payment
                        if diff <= threshold:
                            item_name = str(dfs["data"].at[idx, "품목명"])
                            is_fee = False
                            if confirm_fee_callback:
                                is_fee = confirm_fee_callback(item_name, diff, currency)
                            
                            if is_fee:
                                actual_pay = remaining_payment
                                fee_pay = diff
                            else:
                                actual_pay = remaining_payment
                        else:
                            actual_pay = remaining_payment

                    batch_summary[mgmt_no]['deposit'] += actual_pay
                    batch_summary[mgmt_no]['fee'] += fee_pay
                    
                    remaining_payment -= actual_pay

            # 4. Payment 시트에 이력 기록
            new_payment_records = []
            
            for mgmt_no, summary in batch_summary.items():
                if summary['deposit'] > 0:
                    record = {
                        "일시": now_str,
                        "관리번호": mgmt_no,
                        "구분": "입금",
                        "입금액": summary['deposit'],
                        "통화": summary['currency'],
                        "작업자": current_user,
                        "비고": f"일괄 입금 ({payment_date})"
                    }
                    if "외화입금증빙경로" in file_paths:
                        record["외화입금증빙경로"] = file_paths["외화입금증빙경로"]
                    if "송금상세경로" in file_paths:
                        record["송금상세경로"] = file_paths["송금상세경로"]
                        
                    new_payment_records.append(record)
                
                if summary['fee'] > 0:
                    new_payment_records.append({
                        "일시": now_str,
                        "관리번호": mgmt_no,
                        "구분": "수수료/조정",
                        "입금액": summary['fee'],
                        "통화": summary['currency'],
                        "작업자": current_user,
                        "비고": "잔액 탕감 처리"
                    })

            if new_payment_records:
                payment_df_new = pd.DataFrame(new_payment_records)
                if not payment_df_new.dropna(how='all').empty:
                    dfs["payment"] = pd.concat([dfs["payment"], payment_df_new], ignore_index=True)

            # 5. 최종 재계산
            for mgmt_no in mgmt_nos:
                self.recalc_payment_status(dfs, mgmt_no)

            mgmt_str = mgmt_nos[0]
            if len(mgmt_nos) > 1: mgmt_str += f" 외 {len(mgmt_nos)-1}건"
            
            file_log = ""
            if file_paths.get("외화입금증빙경로"): file_log += " / 외화증빙"
            if file_paths.get("송금상세경로"): file_log += " / 송금상세"
            
            log_msg = f"번호 [{mgmt_str}] / 입금액 [{payment_amount:,.0f}] 처리{file_log} (재계산 완료)"
            self.dm.log_handler.add_log_to_dfs(dfs, "수금 처리", log_msg)

            return True, ""
            
        return self.dm.execute_transaction(update)
