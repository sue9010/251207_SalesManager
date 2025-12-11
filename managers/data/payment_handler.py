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
            
            if row_unpaid < 1:
                data_df.at[idx, "Payment Status"] = "완료"
                data_df.at[idx, "입금완료일"] = last_pay_date
            else:
                data_df.at[idx, "Payment Status"] = "대기"

        # Check for "회계처리" status update
        # Re-fetch rows for this mgmt_no to check overall status
        current_rows = data_df[data_df["관리번호"] == mgmt_no]
        if not current_rows.empty:
            all_paid = (current_rows["Payment Status"] == "완료").all()
            all_delivered = (current_rows["Delivery Status"] == "완료").all()
            
            if all_paid and all_delivered:
                data_df.loc[current_rows.index, "Status"] = "회계처리"

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

            # 전체 미수금액 계산
            total_unpaid = 0
            for idx in indices:
                try: unpaid = float(dfs["data"].at[idx, "미수금액"])
                except: unpaid = 0
                total_unpaid += unpaid

            # 전체 차액 확인 및 수수료 결정
            remaining_deposit = payment_amount
            remaining_fee = 0
            
            # 통화 확인 (첫 번째 항목 기준)
            first_idx = indices[0]
            currency = str(dfs["data"].at[first_idx, "통화"]).upper()
            threshold = 200 if currency != "KRW" else 5000

            diff = total_unpaid - payment_amount
            
            # 차액이 양수이고(미수금 남음) 임계값 이내인 경우
            if 0 < diff <= threshold:
                is_fee = False
                if confirm_fee_callback:
                    # 전체 항목에 대한 수수료 확인
                    item_count = len(indices)
                    item_name = str(dfs["data"].at[first_idx, "품목명"])
                    if item_count > 1:
                        item_name += f" 외 {item_count-1}건"
                    
                    is_fee = confirm_fee_callback(item_name, diff, currency)
                
                if is_fee:
                    remaining_fee = diff

            # 3. 입금 및 수수료 배분
            for idx in indices:
                if remaining_deposit <= 0 and remaining_fee <= 0: break
                
                mgmt_no = dfs["data"].at[idx, "관리번호"]
                if mgmt_no not in batch_summary:
                    batch_summary[mgmt_no] = {'deposit': 0, 'fee': 0, 'currency': currency}

                try: unpaid = float(dfs["data"].at[idx, "미수금액"])
                except: unpaid = 0
                
                if unpaid > 0:
                    actual_pay = 0
                    fee_pay = 0
                    
                    # 1) 입금액 배분
                    if remaining_deposit > 0:
                        if remaining_deposit >= unpaid:
                            actual_pay = unpaid
                            remaining_deposit -= unpaid
                        else:
                            actual_pay = remaining_deposit
                            remaining_deposit = 0
                    
                    # 2) 수수료 배분 (입금액 배분 후 남은 미수금에 대해)
                    remaining_unpaid = unpaid - actual_pay
                    if remaining_unpaid > 0 and remaining_fee > 0:
                        # 수수료는 남은 미수금을 털어내는 것이므로, 
                        # 남은 수수료 총액 내에서 해당 항목의 잔여 미수금만큼 할당
                        if remaining_fee >= remaining_unpaid:
                            fee_pay = remaining_unpaid
                            remaining_fee -= remaining_unpaid
                        else:
                            fee_pay = remaining_fee
                            remaining_fee = 0

                    batch_summary[mgmt_no]['deposit'] += actual_pay
                    batch_summary[mgmt_no]['fee'] += fee_pay

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
                    payment_df_new = payment_df_new.dropna(axis=1, how='all')
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
