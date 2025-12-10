import sys
import os
sys.path.append(os.getcwd())

import unittest
import tkinter as tk
import customtkinter as ctk
from unittest.mock import MagicMock, patch
import pandas as pd
from datetime import datetime, timedelta
from ui.popups.quote_popup import QuotePopup
from managers.data_manager import DataManager

class TestQuotePopupUI(unittest.TestCase):
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
            "업체명": ["Test Client KR", "Test Client US"],
            "국가": ["Korea", "USA"],
            "특이사항": ["", ""]
        })
        self.mock_dm.df_data = pd.DataFrame(columns=[
            "관리번호", "견적일", "구분", "업체명", "프로젝트명", "통화", "세율(%)", "비고", "Status",
            "유효기간", "결제조건", "지급조건", "보증기간",
            "품목명", "모델명", "Description", "수량", "단가", "공급가액", "세액", "합계금액"
        ])
        self.mock_dm.get_next_quote_id.return_value = "QT-20241210-001"
        
        self.popup = QuotePopup(self.root, self.mock_dm, lambda: None)

    def tearDown(self):
        if self.popup:
            self.popup.destroy()

    def test_ui_elements_exist(self):
        """Verify that all new UI elements exist"""
        self.assertTrue(hasattr(self.popup, 'entry_date'), "Quote Date entry missing")
        self.assertTrue(hasattr(self.popup, 'combo_type'), "Type combo missing")
        self.assertTrue(hasattr(self.popup, 'combo_currency'), "Currency combo missing")
        self.assertTrue(hasattr(self.popup, 'entry_tax_rate'), "Tax Rate entry missing")
        self.assertTrue(hasattr(self.popup, 'entry_client'), "Client entry missing")
        self.assertTrue(hasattr(self.popup, 'entry_project'), "Project entry missing")
        self.assertTrue(hasattr(self.popup, 'entry_valid_until'), "Valid Until entry missing")
        self.assertTrue(hasattr(self.popup, 'entry_payment_terms'), "Payment Terms entry missing")
        self.assertTrue(hasattr(self.popup, 'entry_payment_cond'), "Payment Conditions entry missing")
        self.assertTrue(hasattr(self.popup, 'entry_warranty'), "Warranty entry missing")
        self.assertTrue(hasattr(self.popup, 'entry_note'), "Note entry missing")

    def test_valid_until_calculation(self):
        """Verify Valid Until is calculated correctly (Date + 30 days)"""
        test_date = "2024-01-01"
        self.popup.entry_date.delete(0, "end")
        self.popup.entry_date.insert(0, test_date)
        
        # Trigger calculation
        self.popup._on_date_change()
        
        expected_date = (datetime.strptime(test_date, "%Y-%m-%d") + timedelta(days=30)).strftime("%Y-%m-%d")
        self.assertEqual(self.popup.entry_valid_until.get(), expected_date)

    def test_conditional_fields_korea(self):
        """Verify fields for Korean client"""
        self.popup._on_client_select("Test Client KR")
        
        self.assertEqual(self.popup.entry_payment_terms.get(), "당사 공장 인도가")
        self.assertEqual(self.popup.entry_payment_cond.get(), "납품 전 100%")
        self.assertEqual(self.popup.entry_warranty.get(), "2년")

    def test_conditional_fields_foreign(self):
        """Verify fields for Foreign client"""
        self.popup._on_client_select("Test Client US")
        
        self.assertEqual(self.popup.entry_payment_terms.get(), "EXW")
        self.assertEqual(self.popup.entry_payment_cond.get(), "T/T in advance")
        self.assertEqual(self.popup.entry_warranty.get(), "2 years conditional")

    def test_save_data(self):
        """Verify that save calls add_quote with correct data including new fields"""
        # Fill data
        self.popup.entry_id.configure(state="normal")
        self.popup.entry_id.delete(0, "end")
        self.popup.entry_id.insert(0, "QT-TEST")
        self.popup.entry_client.set_value("Test Client KR")
        self.popup.entry_date.delete(0, "end"); self.popup.entry_date.insert(0, "2024-01-01")
        self.popup.entry_valid_until.delete(0, "end"); self.popup.entry_valid_until.insert(0, "2024-01-31")
        self.popup.entry_payment_terms.delete(0, "end"); self.popup.entry_payment_terms.insert(0, "Terms")
        self.popup.entry_payment_cond.delete(0, "end"); self.popup.entry_payment_cond.insert(0, "Cond")
        self.popup.entry_warranty.delete(0, "end"); self.popup.entry_warranty.insert(0, "Warranty")
        
        # Add item
        self.popup._add_item_row()
        row = self.popup.item_rows[0]
        row["item"].insert(0, "Item1")
        row["qty"].insert(0, "1")
        row["price"].insert(0, "100")
        row["supply"].insert(0, "100")
        row["total"].insert(0, "110")
        
        # Mock success
        self.mock_dm.add_quote.return_value = (True, "Success")
        
        # Save
        self.popup.save()
        
        # Verify call
        self.mock_dm.add_quote.assert_called_once()
        args = self.mock_dm.add_quote.call_args
        rows = args[0][0]
        self.assertEqual(len(rows), 1)
        data = rows[0]
        
        self.assertEqual(data["유효기간"], "2024-01-31")
        self.assertEqual(data["결제조건"], "Terms")
        self.assertEqual(data["지급조건"], "Cond")
        self.assertEqual(data["보증기간"], "Warranty")

    def test_tax_rate_change_recalculation(self):
        """Verify that changing tax rate updates item totals"""
        # Add item
        self.popup._add_item_row()
        row = self.popup.item_rows[0]
        row["qty"].delete(0, "end")
        row["qty"].insert(0, "1")
        row["price"].delete(0, "end")
        row["price"].insert(0, "100")
        self.popup.calculate_row(row)
        
        # Initial check (Tax 10% default for KRW)
        self.assertEqual(row["tax"].get(), "10")
        self.assertEqual(row["total"].get(), "110")
        
        # Change Tax Rate to 20
        self.popup.entry_tax_rate.delete(0, "end")
        self.popup.entry_tax_rate.insert(0, "20")
        self.popup._on_tax_change()
        
        # Verify update
        self.assertEqual(row["tax"].get(), "20")
        self.assertEqual(row["total"].get(), "120")

if __name__ == '__main__':
    unittest.main()
