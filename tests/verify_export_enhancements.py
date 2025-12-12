import sys
import os
import pandas as pd
from datetime import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from managers.data_manager import DataManager
from managers.export_manager import ExportManager
from src.config import Config

def verify_export_logic():
    print("Starting Export Logic Verification...")
    
    # 1. Initialize DataManager
    dm = DataManager()
    
    print("1. Checking DataManager methods...")
    if not hasattr(dm, 'update_order_fields'):
        print("FAIL: update_order_fields not found in DataManager")
        return
    print("PASS: update_order_fields exists")

    # Mock log handler to avoid errors
    dm.log_handler.add_log_to_dfs = lambda *args: None

    # We need to mock execute_transaction to just apply update locally
    def mock_transaction(update_func):
        dfs = {"data": dm.df_data, "delivery": dm.df_delivery, "log": pd.DataFrame(columns=["일시", "작업자", "구분", "상세내용"])}
        success, msg = update_func(dfs)
        if success:
            dm.df_data = dfs["data"]
            dm.df_delivery = dfs["delivery"]
        return success, msg
        
    dm.execute_transaction = mock_transaction
    
    # 2. Test Export Manager Logic (Mocking PDF conversion to avoid GUI/Printer issues)
    print("2. Checking ExportManager...")
    em = ExportManager(dm)
    
    # Mock _convert_and_save_pdf to just return a dummy path
    original_convert = em._convert_and_save_pdf
    em._convert_and_save_pdf = lambda wb, name, server_folder_name: (True, "Mock Success", f"C:\\Mock\\{server_folder_name}\\{name}")
    
    # Test Quote Export
    client_info = {"국가": "Korea", "담당자": "Tester", "전화번호": "123", "주소": "Seoul"}
    quote_info = {"client_name": "TestClient", "mgmt_no": "TEST-001", "date": "2024-01-01"}
    items = [{"item": "Item1", "qty": 10, "price": 100, "amount": 1000}]
    
    # We need a dummy order in dm.df_data to update
    dm.df_data = pd.DataFrame([{
        "관리번호": "TEST-001", "업체명": "TestClient", "견적서경로": "",
        "수량": 10, "단가": 100, "세율(%)": 10, "합계금액": 1100, "품목명": "TestItem",
        "Delivery Status": "준비", "Payment Status": "준비", "출고일": "-", "송장번호": "-", "운송방법": "-", "미수금액": 1100
    }])
    
    print("   Testing Quote Export...")
    success, msg, path = em.export_quote_to_pdf(client_info, quote_info, items)
    if success:
        saved_path = dm.df_data.iloc[0]["견적서경로"]
        if "C:\\Mock\\견적서" in str(saved_path):
            print(f"PASS: Quote path saved correctly: {saved_path}")
        else:
            print(f"FAIL: Quote path not saved or incorrect: {saved_path}")
    else:
        print(f"FAIL: Quote export failed: {msg}")

    # Test CI Export
    print("   Testing CI Export...")
    order_info = {"client_name": "TestClient", "mgmt_no": "TEST-001", "date": "2024-01-01", "invoice_no": "INV-001"}
    success, msg, path = em.export_ci_to_pdf(client_info, order_info, items)
    if success:
        print(f"PASS: CI Export successful: {path}")
    else:
        print(f"FAIL: CI Export failed: {msg}")

    # Test PL Export
    print("   Testing PL Export...")
    success, msg, path = em.export_pl_to_pdf(client_info, order_info, items)
    if success:
        print(f"PASS: PL Export successful: {path}")
    else:
        print(f"FAIL: PL Export failed: {msg}")
        
    # 3. Test Delivery Process with CI/PL
    print("3. Testing Delivery Process with CI/PL...")
    # Add dummy delivery columns if not present (in case config didn't reload in this script context)
    if "CI경로" not in dm.df_delivery.columns:
        dm.df_delivery["CI경로"] = ""
    if "PL경로" not in dm.df_delivery.columns:
        dm.df_delivery["PL경로"] = ""
        
    delivery_no = "DEL-001"
    ci_path = "C:\\Mock\\CI\\CI_Test.pdf"
    pl_path = "C:\\Mock\\PL\\PL_Test.pdf"
    
    update_requests = [{
        "idx": 0, # Index of our dummy order
        "serial_no": "SN-001",
        "deliver_qty": 5
    }]
    
    success, msg = dm.process_delivery(
        delivery_no, "2024-01-01", "INV-001", "Air", "Waybill.pdf", 
        update_requests, ci_path=ci_path, pl_path=pl_path
    )
    
    if success:
        # Check delivery df
        del_row = dm.df_delivery[dm.df_delivery["출고번호"] == delivery_no].iloc[0]
        if del_row["CI경로"] == ci_path and del_row["PL경로"] == pl_path:
             print(f"PASS: CI/PL paths saved in Delivery sheet: {del_row['CI경로']}, {del_row['PL경로']}")
        else:
             print(f"FAIL: CI/PL paths mismatch. CI: {del_row.get('CI경로')}, PL: {del_row.get('PL경로')}")
    else:
        print(f"FAIL: Process delivery failed: {msg}")

    print("Verification Complete.")

if __name__ == "__main__":
    verify_export_logic()
