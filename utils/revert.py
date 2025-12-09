import os
import sys
import pandas as pd

# 프로젝트 루트 경로 설정
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)

from src.config import Config

def restore_sales_list():
    # 복구할 파일 경로: SalesList.xlsx
    target_path = os.path.join(project_root, "data", "SalesList.xlsx")
    
    print(f"🔄 [판매 데이터] 복구 시작: {target_path}")

    # 데이터 폴더가 없으면 생성
    os.makedirs(os.path.dirname(target_path), exist_ok=True)

    try:
        with pd.ExcelWriter(target_path, engine="openpyxl") as writer:
            # 1. Data 시트 (판매 메인 데이터)
            # 주의: 반드시 Sales용 DATA_COLUMNS를 사용해야 함
            if not hasattr(Config, 'DATA_COLUMNS'):
                print("❌ Config.DATA_COLUMNS가 정의되지 않았습니다. config.py를 확인하세요.")
                return

            df_data = pd.DataFrame(columns=Config.DATA_COLUMNS)
            df_data.to_excel(writer, sheet_name="Data", index=False)
            print(f"✅ 'Data' 시트 생성 (컬럼: {len(Config.DATA_COLUMNS)}개 - 수주일/출고일 포함)")

            # 2. Clients 시트 (고객사 정보)
            df_clients = pd.DataFrame(columns=Config.CLIENT_COLUMNS)
            df_clients.to_excel(writer, sheet_name="Clients", index=False)
            print("✅ 'Clients' 시트 생성")

            # 3. Payment 시트 (입금/수금)
            df_payment = pd.DataFrame(columns=Config.PAYMENT_COLUMNS)
            df_payment.to_excel(writer, sheet_name="Payment", index=False)
            print("✅ 'Payment' 시트 생성")

            # 4. Delivery 시트 (출고/납품)
            df_delivery = pd.DataFrame(columns=Config.DELIVERY_COLUMNS)
            df_delivery.to_excel(writer, sheet_name="Delivery", index=False)
            print("✅ 'Delivery' 시트 생성")

            # 5. Log 시트
            df_log = pd.DataFrame(columns=Config.LOG_COLUMNS)
            df_log.to_excel(writer, sheet_name="Log", index=False)
            print("✅ 'Log' 시트 생성")

            # 6. Memo 시트
            df_memo = pd.DataFrame(columns=Config.MEMO_COLUMNS)
            df_memo.to_excel(writer, sheet_name="Memo", index=False)
            print("✅ 'Memo' 시트 생성")
            
            # 7. MemoLog 시트
            df_memo_log = pd.DataFrame(columns=Config.MEMO_LOG_COLUMNS)
            df_memo_log.to_excel(writer, sheet_name="MemoLog", index=False)
            print("✅ 'MemoLog' 시트 생성")

        print(f"\n🎉 [SalesList.xlsx] 복구 완료!")
        print(f"경로: {target_path}")
        print("이제 프로그램을 다시 실행하면 '판매 관리' 탭이 정상 작동할 것입니다.")

    except Exception as e:
        print(f"\n❌ 복구 실패: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    restore_sales_list()