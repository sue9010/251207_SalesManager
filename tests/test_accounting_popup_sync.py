import unittest
from unittest.mock import MagicMock
import pandas as pd
import tkinter as tk
import customtkinter as ctk

# Mocking necessary parts
class MockDataManager:
    def __init__(self):
        self.df_data = pd.DataFrame({
            "관리번호": ["MGMT001"],
            "모델명": ["Test Model"]
        })
        self.df_delivery = pd.DataFrame({
            "관리번호": ["MGMT001", "MGMT001"],
            "송장번호": ["INV123", "INV123"],
            "수출신고번호": ["", ""],
            "수출신고필증경로": ["", ""],
            "일시": ["2023-01-01", "2023-01-02"],
            "출고수량": [10, 20],
            "운송방법": ["Air", "Air"]
        })
        self.attachment_root = "attachments"

class MockFileManager:
    def __init__(self):
        self.file_entries = {}
        self.DND_AVAILABLE = False
    
    def update_file_entry(self, key, path):
        if key in self.file_entries:
            self.file_entries[key].delete(0, "end")
            self.file_entries[key].insert(0, path)
            
    def clear_entry(self, key):
        if key in self.file_entries:
            self.file_entries[key].delete(0, "end")

    def _setup_dnd(self, widget, key, callback=None):
        pass

class TestAccountingPopupSync(unittest.TestCase):
    def setUp(self):
        self.root = tk.Tk()
        self.dm = MockDataManager()
        
        # Mocking AccountingPopup structure
        self.popup = MagicMock()
        self.popup.dm = self.dm
        self.popup.target_mgmt_no = "MGMT001"
        self.popup.entries = {}
        self.popup.file_manager = MockFileManager()
        self.popup.COL_SPECS = {
            "delivery": [
                ("일시", 100), ("모델명", 120), ("출고수량", 80), ("송장번호", 120), ("운송방법", 100), 
                ("수출신고번호", 150), ("수출신고필증", 200)
            ]
        }
        
        # Create a dummy scroll frame
        self.popup.delivery_scroll = ctk.CTkFrame(self.root)
        
        # Bind the methods we want to test
        from ui.popups.accounting_popup import AccountingPopup
        self.popup._add_delivery_row = AccountingPopup._add_delivery_row.__get__(self.popup, AccountingPopup)
        self.popup._sync_export_info = AccountingPopup._sync_export_info.__get__(self.popup, AccountingPopup)
        
    def tearDown(self):
        self.root.destroy()

    def test_sync_logic(self):
        # 1. Add rows
        for idx, row in self.dm.df_delivery.iterrows():
            self.popup._add_delivery_row(idx, row)
            
        # Verify entries are created
        self.assertIn("delivery_export_no_0", self.popup.entries)
        self.assertIn("delivery_export_no_1", self.popup.entries)
        
        # 2. Simulate changing export no in row 0
        entry0 = self.popup.entries["delivery_export_no_0"]
        entry0.delete(0, "end")
        entry0.insert(0, "EXP-001")
        
        # Trigger sync manually (as if FocusOut happened)
        self.popup._sync_export_info("INV123", export_no="EXP-001")
        
        # 3. Verify row 1 is updated
        entry1 = self.popup.entries["delivery_export_no_1"]
        self.assertEqual(entry1.get(), "EXP-001")
        
        # 4. Simulate changing file path in row 1
        file_entry1 = self.popup.file_manager.file_entries["delivery_export_file_1"]
        file_entry1.delete(0, "end")
        file_entry1.insert(0, "C:/path/to/file.pdf")
        
        # Trigger sync
        self.popup._sync_export_info("INV123", export_file_path="C:/path/to/file.pdf")
        
        # 5. Verify row 0 is updated
        file_entry0 = self.popup.file_manager.file_entries["delivery_export_file_0"]
        self.assertEqual(file_entry0.get(), "C:/path/to/file.pdf")

if __name__ == "__main__":
    unittest.main()
