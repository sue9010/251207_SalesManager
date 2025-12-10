import unittest
import pandas as pd
from unittest.mock import MagicMock
from managers.data_manager import DataManager
from managers.data.order_handler import OrderHandler
from managers.data.delivery_handler import DeliveryHandler
from managers.data.payment_handler import PaymentHandler

class TestStatusSchema(unittest.TestCase):
    def setUp(self):
        self.mock_dm = MagicMock(spec=DataManager)
        self.mock_dm.log_handler = MagicMock()
        self.mock_dm.df_data = pd.DataFrame()
        self.mock_dm.df_delivery = pd.DataFrame()
        self.mock_dm.df_payment = pd.DataFrame()
        self.mock_dm.execute_transaction = lambda func: func({"data": self.mock_dm.df_data, "delivery": self.mock_dm.df_delivery, "payment": self.mock_dm.df_payment})
        
        self.order_handler = OrderHandler(self.mock_dm)
        self.delivery_handler = DeliveryHandler(self.mock_dm)
        self.payment_handler = PaymentHandler(self.mock_dm)

    def test_add_order_initializes_statuses(self):
        order_rows = [{
            "관리번호": "PO-231210-001",
            "업체명": "Test Client",
            "Status": "주문"
        }]
        
        # Mock execute_transaction to update local df
        def mock_exec(func):
            dfs = {"data": pd.DataFrame(), "delivery": pd.DataFrame(), "payment": pd.DataFrame()}
            func(dfs)
            self.mock_dm.df_data = dfs["data"]
            return True, ""
        self.mock_dm.execute_transaction = mock_exec
        
        self.order_handler.add_order(order_rows, "PO-231210-001", "Test Client")
        
        df = self.mock_dm.df_data
        self.assertEqual(len(df), 1)
        self.assertEqual(df.iloc[0]["Delivery Status"], "대기")
        self.assertEqual(df.iloc[0]["Payment Status"], "대기")

    def test_delivery_update(self):
        # Setup initial data
        self.mock_dm.df_data = pd.DataFrame([{
            "관리번호": "PO-231210-001",
            "Status": "주문",
            "Delivery Status": "대기",
            "Payment Status": "대기",
            "수량": 10,
            "단가": 100,
            "세율(%)": 10,
            "합계금액": 1100,
            "미수금액": 1100
        }])
        
        def mock_exec(func):
            dfs = {"data": self.mock_dm.df_data, "delivery": pd.DataFrame(), "payment": pd.DataFrame()}
            func(dfs)
            self.mock_dm.df_data = dfs["data"]
            return True, ""
        self.mock_dm.execute_transaction = mock_exec
        
        # Process Delivery
        reqs = [{"idx": 0, "deliver_qty": 10, "serial_no": "SN123"}]
        self.delivery_handler.process_delivery("CX-001", "2023-12-10", "INV123", "Truck", "", reqs)
        
        df = self.mock_dm.df_data
        self.assertEqual(df.iloc[0]["Delivery Status"], "완료")
        self.assertEqual(df.iloc[0]["Status"], "주문") # Status should remain "주문"

    def test_payment_update(self):
        # Setup initial data
        self.mock_dm.df_data = pd.DataFrame([{
            "관리번호": "PO-231210-001",
            "Status": "주문",
            "Delivery Status": "완료",
            "Payment Status": "대기",
            "합계금액": 1100,
            "미수금액": 1100,
            "기수금액": 0
        }])
        
        def mock_exec(func):
            dfs = {"data": self.mock_dm.df_data, "delivery": pd.DataFrame(), "payment": pd.DataFrame()}
            func(dfs)
            self.mock_dm.df_data = dfs["data"]
            # Also update payment df for recalc
            dfs["payment"] = pd.DataFrame([{
                "관리번호": "PO-231210-001",
                "입금액": 1100,
                "일시": "2023-12-10 10:00:00"
            }])
            return True, ""
        self.mock_dm.execute_transaction = mock_exec
        
        # Process Payment (Simulate add_payment or process_payment calling recalc)
        # Here we manually call recalc to test logic
        dfs = {"data": self.mock_dm.df_data, "payment": pd.DataFrame([{
                "관리번호": "PO-231210-001",
                "입금액": 1100,
                "일시": "2023-12-10 10:00:00"
            }])}
        
        self.payment_handler.recalc_payment_status(dfs, "PO-231210-001")
        
        df = dfs["data"]
        self.assertEqual(df.iloc[0]["Payment Status"], "완료")
        self.assertEqual(df.iloc[0]["Status"], "주문") # Status should remain "주문"

if __name__ == '__main__':
    unittest.main()
