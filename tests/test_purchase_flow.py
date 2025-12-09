import sys
import os
sys.path.append(os.getcwd())

from managers.data_manager import DataManager
from src.config import Config
import pandas as pd

def test_purchase_flow():
    print("=== Purchase Data Flow Test ===")
    
    # 1. Initialize DataManager
    dm = DataManager()
    print("[1] DataManager Initialized")
    
    # Ensure purchase file is clean or we use a test file?
    # For safety, we'll use the default path but maybe backup first?
    # Or just add a test record and delete it.
    
    # 2. Add Purchase
    test_id = dm.get_next_purchase_id()
    print(f"[2] Generated ID: {test_id}")
    
    row_data = {
        "관리번호": test_id,
        "발주일": "2025-12-09",
        "구분": "내수",
        "업체명": "테스트업체",
        "품목명": "테스트품목",
        "수량": 10,
        "단가": 1000,
        "공급가액": 10000,
        "세액": 1000,
        "합계금액": 11000,
        "Status": "발주"
    }
    
    success, msg = dm.add_purchase([row_data])
    if success: print(f"[3] Add Success: {msg}")
    else: print(f"[3] Add Failed: {msg}"); return

    # 3. Verify in Memory
    if not dm.df_purchase.empty and test_id in dm.df_purchase["관리번호"].values:
        print("[4] Verified in Memory")
    else:
        print("[4] Verification Failed")
        return

    # 4. Save
    success, msg = dm.save_purchase_data()
    if success: print(f"[5] Save Success: {msg}")
    else: print(f"[5] Save Failed: {msg}"); return
    
    # 5. Reload
    dm2 = DataManager()
    dm2.load_data()
    if not dm2.df_purchase.empty and test_id in dm2.df_purchase["관리번호"].values:
        print("[6] Reload Verified")
    else:
        print("[6] Reload Failed")
        return

    # 6. Update
    row_data["수량"] = 20
    row_data["합계금액"] = 22000
    success, msg = dm.update_purchase(test_id, [row_data])
    if success: print(f"[7] Update Success: {msg}")
    else: print(f"[7] Update Failed: {msg}"); return
    
    # Verify Update
    row = dm.df_purchase[dm.df_purchase["관리번호"] == test_id].iloc[0]
    if row["수량"] == 20: print("[8] Update Verified")
    else: print(f"[8] Update Failed: Expected 20, got {row['수량']}")

    # 7. Delete
    success, msg = dm.delete_purchase(test_id)
    if success: print(f"[9] Delete Success: {msg}")
    else: print(f"[9] Delete Failed: {msg}"); return
    
    # Verify Delete
    if test_id not in dm.df_purchase["관리번호"].values:
        print("[10] Delete Verified")
    else:
        print("[10] Delete Failed")

    # Save final state
    dm.save_purchase_data()
    print("=== Test Complete ===")

if __name__ == "__main__":
    test_purchase_flow()
