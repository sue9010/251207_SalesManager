import sys
import os
sys.path.append(os.getcwd())

import unittest
import tkinter as tk
import customtkinter as ctk
from unittest.mock import MagicMock, patch
import pandas as pd
from ui.popups.purchase_popup import PurchasePopup
from managers.data_manager import DataManager

class TestPurchasePopupUI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = ctk.CTk()
        cls.root.withdraw()

    @classmethod
    def tearDownClass(cls):
        cls.root.destroy()

    def setUp(self):
        self.mock_dm = MagicMock(spec=DataManager)
        # Mock clients data
        self.mock_dm.df_clients = pd.DataFrame({
            "업체명": ["Test Client"],
            "예금주": ["Test Holder"],
            "계좌번호": ["123-456"],
            "은행명": ["Test Bank"],
            "Swift Code": ["TESTKRKR"],
            "은행주소": ["Seoul, Korea"]
        })
        self.mock_dm.df_purchase = pd.DataFrame(columns=[
            "관리번호", "발주일", "구분", "업체명", "통화", "세율(%)", "비고", 
            "입고상태", "지급상태", "견적서경로", "예금주", "계좌번호", "은행명", "Swift Code", "은행주소",
            "품목명", "모델명", "Description", "수량", "단가", "공급가액", "세액", "합계금액"
        ])
        self.mock_dm.get_next_purchase_id.return_value = "PO-20241209-001"
        
        self.popup = PurchasePopup(self.root, self.mock_dm, lambda: None)

    def tearDown(self):
        if self.popup:
            self.popup.destroy()

    def test_ui_elements_exist(self):
        """Verify that all new UI elements exist"""
        self.assertTrue(hasattr(self.popup, 'entry_date'), "Order Date entry missing")
        self.assertTrue(hasattr(self.popup, 'combo_type'), "Type combo missing")
        self.assertTrue(hasattr(self.popup, 'combo_currency'), "Currency combo missing")
        self.assertTrue(hasattr(self.popup, 'entry_tax_rate'), "Tax Rate entry missing")
        self.assertTrue(hasattr(self.popup, 'entry_client'), "Client entry missing")
        self.assertTrue(hasattr(self.popup, 'entry_account_holder'), "Account Holder entry missing")
        self.assertTrue(hasattr(self.popup, 'entry_account_number'), "Account Number entry missing")
        self.assertTrue(hasattr(self.popup, 'entry_bank_name'), "Bank Name entry missing")
        self.assertTrue(hasattr(self.popup, 'entry_swift_code'), "Swift Code entry missing")
        self.assertTrue(hasattr(self.popup, 'entry_bank_address'), "Bank Address entry missing")
        self.assertTrue(hasattr(self.popup, 'entry_quote_file'), "Quote File entry missing")
        self.assertTrue(hasattr(self.popup, 'combo_receiving_status'), "Receiving Status combo missing")
        self.assertTrue(hasattr(self.popup, 'combo_payment_status'), "Payment Status combo missing")

    def test_bank_info_autoload(self):
        """Verify that bank info is loaded when a client is selected"""
        # Simulate client selection
        self.popup._on_client_select("Test Client")
        
        self.assertEqual(self.popup.entry_account_holder.get(), "Test Holder")
        self.assertEqual(self.popup.entry_account_number.get(), "123-456")
        self.assertEqual(self.popup.entry_bank_name.get(), "Test Bank")
        self.assertEqual(self.popup.entry_swift_code.get(), "TESTKRKR")
        self.assertEqual(self.popup.entry_bank_address.get("1.0", "end-1c").strip(), "Seoul, Korea")

    def test_currency_change_logic(self):
        """Verify tax rate and type change based on currency"""
        # Default KRW
        self.popup.on_currency_change("KRW")
        self.assertEqual(self.popup.entry_tax_rate.get(), "10")
        self.assertEqual(self.popup.combo_type.get(), "내수")

        # Change to USD
        self.popup.on_currency_change("USD")
        self.assertEqual(self.popup.entry_tax_rate.get(), "0")
        self.assertEqual(self.popup.combo_type.get(), "수입")

if __name__ == '__main__':
    unittest.main()
