import sys
import os
sys.path.append(os.getcwd())

from managers.data_manager import DataManager
import pandas as pd

def test_client_flow():
    print("=== Client Data Flow Test ===")
    
    # 1. Initialize DataManager
    dm = DataManager()
    print("[1] DataManager Initialized")
    
    # Test Data with Bank Info
    test_client_name = "테스트업체_BankInfo"
    client_data = {
        "업체명": test_client_name,
        "사업자번호": "123-45-67890",
        "대표자": "홍길동",
        "전화번호": "010-1234-5678",
        "이메일": "test@example.com",
        "주소": "서울시 강남구",
        "특이사항": "테스트 업체입니다.",
        "운송방법": "DHL",
        "운송계정": "987654321",
        # New Bank Info Fields
        "계좌번호": "110-123-456789",
        "예금주": "홍길동",
        "은행명": "신한은행",
        "은행주소": "서울시 중구",
        "Swift Code": "SHBKRSE"
    }
    
    # 2. Add Client
    # Check if exists first and delete if so (cleanup from previous runs)
    if not dm.df_clients.empty and test_client_name in dm.df_clients["업체명"].values:
        dm.delete_client(test_client_name)
        print(f"[Pre-cleanup] Deleted existing {test_client_name}")

    success, msg = dm.add_client(client_data)
    if success: print(f"[2] Add Success: {msg}")
    else: print(f"[2] Add Failed: {msg}"); return

    # 3. Verify in Memory
    if not dm.df_clients.empty and test_client_name in dm.df_clients["업체명"].values:
        row = dm.df_clients[dm.df_clients["업체명"] == test_client_name].iloc[0]
        if row["계좌번호"] == "110-123-456789" and row["Swift Code"] == "SHBKRSE":
            print("[3] Verified in Memory (including Bank Info)")
        else:
            print(f"[3] Verification Failed: Bank Info mismatch. Got {row.get('계좌번호')}, {row.get('Swift Code')}")
            return
    else:
        print("[3] Verification Failed: Client not found in memory")
        return

    # 4. Save (Implicitly handled by add_client usually, but let's ensure persistence)
    # DataManager.add_client calls save_clients() internally? Let's assume yes or check.
    # Usually it does.
    
    # 5. Reload
    dm2 = DataManager()
    dm2.load_data()
    if not dm2.df_clients.empty and test_client_name in dm2.df_clients["업체명"].values:
        row = dm2.df_clients[dm2.df_clients["업체명"] == test_client_name].iloc[0]
        if row["은행명"] == "신한은행":
            print("[4] Reload Verified")
        else:
             print(f"[4] Reload Failed: Bank Name mismatch. Got {row.get('은행명')}")
    else:
        print("[4] Reload Failed: Client not found")
        return

    # 6. Update
    client_data["예금주"] = "홍길동(수정)"
    client_data["은행명"] = "국민은행"
    
    success, msg = dm.update_client(test_client_name, client_data)
    if success: print(f"[5] Update Success: {msg}")
    else: print(f"[5] Update Failed: {msg}"); return
    
    # Verify Update
    row = dm.df_clients[dm.df_clients["업체명"] == test_client_name].iloc[0]
    if row["예금주"] == "홍길동(수정)" and row["은행명"] == "국민은행":
        print("[6] Update Verified")
    else:
        print(f"[6] Update Failed: Expected '홍길동(수정)', '국민은행', got {row.get('예금주')}, {row.get('은행명')}")

    # # 7. Delete
    # success, msg = dm.delete_client(test_client_name)
    # if success: print(f"[7] Delete Success: {msg}")
    # else: print(f"[7] Delete Failed: {msg}"); return
    
    # # Verify Delete
    # if test_client_name not in dm.df_clients["업체명"].values:
    #     print("[8] Delete Verified")
    # else:
    #     print("[8] Delete Failed")

    print("=== Test Complete ===")

if __name__ == "__main__":
    test_client_flow()
