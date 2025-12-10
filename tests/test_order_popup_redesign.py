import unittest
from unittest.mock import MagicMock, patch
import pandas as pd
import customtkinter as ctk
import sys
import os

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from ui.popups.order_popup import OrderPopup

class TestOrderPopupRedesign(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ctk.set_appearance_mode("Dark")
        cls.root = ctk.CTk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def setUp(self):
        self.mock_dm = MagicMock()
        # Mock Clients Data
        self.mock_dm.df_clients = pd.DataFrame({
            "업체명": ["Test Client"],
            "국가": ["KR"],
            "사업자등록증경로": [""]
        })
        # Mock Sales Data (Quote)
        self.mock_dm.df_data = pd.DataFrame({
            "관리번호": ["QT-231210-001"],
            "구분": ["내수"],
            "업체명": ["Test Client"],
            "프로젝트명": ["Test Project"],
            "통화": ["KRW"],
            "세율(%)": [10],
            "결제조건": ["당사 공장 인도가"],
            "지급조건": ["납품 전 100%"],
            "주문요청사항": ["Request"],
            "비고": ["Note"],
            "Status": ["견적"],
            "수주일": [""],
            "품목명": ["Item A"],
            "모델명": ["Model A"],
            "Description": ["Desc A"],
            "수량": [1],
            "단가": [100],
            "공급가액": [100],
            "세액": [10],
            "합계금액": [110]
        })
        self.mock_dm.get_next_order_id.return_value = "OD-231210-001"
        self.mock_dm.add_order.return_value = (True, "Success")
        self.mock_dm.update_order.return_value = (True, "Success")

    def test_load_quote_data(self):
        # Open OrderPopup with Quote ID
        popup = OrderPopup(self.root, self.mock_dm, lambda: None, mgmt_no="QT-231210-001")
        
        # Verify fields loaded from Quote
        self.assertEqual(popup.entry_project.get(), "Test Project")
        self.assertEqual(popup.entry_payment_terms.get(), "당사 공장 인도가")
        self.assertEqual(popup.entry_payment_cond.get(), "납품 전 100%")
        self.assertEqual(popup.entry_req.get("1.0", "end-1c"), "Request")
        
        # Verify Date is Today (since Quote has no Order Date)
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        self.assertEqual(popup.entry_date.get(), today)
        
        popup.destroy()

    def test_save_new_fields(self):
        # Open New OrderPopup
        popup = OrderPopup(self.root, self.mock_dm, lambda: None)
        
        # Fill fields
        popup.entry_client.set_value("Test Client")
        popup.entry_payment_terms.insert(0, "New Terms")
        popup.entry_payment_cond.insert(0, "New Cond")
        
        # Add Item
        popup._add_item_row()
        row = popup.item_rows[0]
        row["item"].insert(0, "Item 1")
        row["qty"].insert(0, "1")
        row["price"].insert(0, "100")
        popup.calculate_row(row)
        
        # Save
        popup.save()
        
        # Verify add_order called with correct data
        args = self.mock_dm.add_order.call_args
        self.assertIsNotNone(args)
        rows = args[0][0] # First arg is rows list
        self.assertEqual(rows[0]["결제조건"], "New Terms")
        self.assertEqual(rows[0]["지급조건"], "New Cond")
        
        popup.destroy()

if __name__ == "__main__":
    unittest.main()
