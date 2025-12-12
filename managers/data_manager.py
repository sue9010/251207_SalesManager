import os
import pandas as pd
from src.config import Config

from managers.data.file_handler import FileHandler
from managers.data.log_handler import LogHandler
from managers.data.client_handler import ClientHandler
from managers.data.order_handler import OrderHandler
from managers.data.payment_handler import PaymentHandler
from managers.data.delivery_handler import DeliveryHandler
from managers.data.purchase_handler import PurchaseHandler

class DataManager:
    def __init__(self):
        # 기존 판매 관련 DataFrame
        self.df_clients = pd.DataFrame(columns=Config.CLIENT_COLUMNS)
        self.df_data = pd.DataFrame(columns=Config.DATA_COLUMNS) # Sales Data
        self.df_payment = pd.DataFrame(columns=Config.PAYMENT_COLUMNS)
        self.df_delivery = pd.DataFrame(columns=Config.DELIVERY_COLUMNS)
        self.df_log = pd.DataFrame(columns=Config.LOG_COLUMNS)
        self.df_memo = pd.DataFrame(columns=Config.MEMO_COLUMNS)
        self.df_memo_log = pd.DataFrame(columns=Config.MEMO_LOG_COLUMNS)
        
        # [신규] 구매 관련 DataFrame 추가
        self.df_purchase = pd.DataFrame(columns=Config.PURCHASE_COLUMNS)
        
        # Paths (Config에서 로드됨)
        self.current_excel_path = Config.DEFAULT_EXCEL_PATH
        self.purchase_data_path = Config.DEFAULT_PURCHASE_DATA_PATH # 구매 엑셀 경로
        self.attachment_root = Config.DEFAULT_ATTACHMENT_ROOT
        self.production_request_path = Config.DEFAULT_PRODUCTION_REQUEST_PATH
        
        self.current_theme = "Dark"
        self.is_dev_mode = False
        self.last_file_timestamp = 0.0
        
        # Handlers
        self.file_handler = FileHandler(self)
        self.log_handler = LogHandler(self)
        self.client_handler = ClientHandler(self)
        self.order_handler = OrderHandler(self)
        self.payment_handler = PaymentHandler(self)
        self.delivery_handler = DeliveryHandler(self)
        self.purchase_handler = PurchaseHandler(self)
        
        self.load_config()

    # Delegate to FileHandler
    def load_config(self):
        self.file_handler.load_config()
        # config 로드 후 경로 업데이트 확인
        # self.purchase_data_path = Config.DEFAULT_PURCHASE_DATA_PATH # Removed to fix overwrite issue

    def save_config(self, *args, **kwargs):
        self.file_handler.save_config(*args, **kwargs)

    def load_data(self):
        """
        판매 데이터(SalesList.xlsx)와 구매 데이터(OrderList.xlsx)를 모두 로드합니다.
        """
        # 1. 판매 데이터 로드 (기존 로직)
        success_sales, msg_sales = self.file_handler.load_data()
        
        # 2. 구매 데이터 로드 (신규 로직)
        success_purchase, msg_purchase = self._load_purchase_data()
        
        if not success_sales: return False, f"Sales Load Error: {msg_sales}"
        if not success_purchase: 
            # 구매 파일 로드 실패 시 로그만 남기고 일단 진행 (판매 기능은 유지)하거나 실패 처리
            # 여기서는 명확한 오류 확인을 위해 실패로 처리합니다.
            return False, f"Purchase Load Error: {msg_purchase}"
            
        # 3. 생산 요청 파일의 날짜 동기화 (출고예정일 등)
        self.sync_production_dates()
            
        return True, "데이터 로드 완료"

    def _load_purchase_data(self):
        """내부 메서드: 구매 엑셀 파일을 로드하여 self.df_purchase에 저장"""
        df, msg = self.file_handler.load_purchase_data()
        if df is not None:
            self.df_purchase = df
            return True, msg
        else:
            return False, msg

    def save_to_excel(self):
        # 판매 데이터 저장
        return self.file_handler.save_to_excel()
        # TODO: 구매 데이터 저장 로직도 save_purchase_data() 등으로 분리하거나 통합 필요

    def save_data(self, sheet_type=None):
        """
        데이터를 저장합니다. sheet_type은 호환성을 위해 유지하지만, 현재는 전체 저장을 수행합니다.
        """
        return self.save_to_excel()

    def create_backup(self):
        return self.file_handler.create_backup()

    def check_for_external_changes(self):
        # TODO: Purchase 파일 변경 체크 로직도 추가 필요
        return self.file_handler.check_for_external_changes()

    def save_attachment(self, *args, **kwargs):
        return self.file_handler.save_attachment(*args, **kwargs)

    # Delegate to LogHandler
    def add_log(self, action, details):
        self.log_handler.add_log(action, details)

    def _add_log_to_dfs(self, dfs, action, details):
        self.log_handler.add_log_to_dfs(dfs, action, details)

    def _create_log_entry(self, action, details):
        return self.log_handler.create_log_entry(action, details)

    def clean_old_logs(self):
        return self.log_handler.clean_old_logs()

    # Delegate to ClientHandler
    def get_client_shipping_method(self, client_name):
        return self.client_handler.get_client_shipping_method(client_name)

    def get_client_shipping_account(self, client_name):
        return self.client_handler.get_client_shipping_account(client_name)

    def add_client(self, client_data):
        return self.client_handler.add_client(client_data)

    def update_client(self, original_name, client_data):
        return self.client_handler.update_client(original_name, client_data)

    def delete_client(self, client_name):
        return self.client_handler.delete_client(client_name)

    # Delegate to OrderHandler
    def get_next_quote_id(self):
        return self.order_handler.get_next_quote_id()

    def get_next_order_id(self):
        return self.order_handler.get_next_order_id()

    def get_status_by_req_no(self, req_no):
        return self.order_handler.get_status_by_req_no(req_no)

    def get_filtered_data(self, status_list=None, keyword=""):
        return self.order_handler.get_filtered_data(status_list, keyword)

    def add_order(self, order_rows, mgmt_no, client_name):
        return self.order_handler.add_order(order_rows, mgmt_no, client_name)

    def update_order(self, mgmt_no, order_rows, client_name, is_copy=False):
        return self.order_handler.update_order(mgmt_no, order_rows, client_name, is_copy)

    def delete_order(self, mgmt_no):
        return self.order_handler.delete_order(mgmt_no)

    def add_quote(self, quote_rows, mgmt_no, client_name):
        return self.order_handler.add_quote(quote_rows, mgmt_no, client_name)

    def update_quote(self, mgmt_no, quote_rows, client_name, is_copy=False):
        return self.order_handler.update_quote(mgmt_no, quote_rows, client_name, is_copy)

    def delete_quote(self, mgmt_no):
        return self.order_handler.delete_quote(mgmt_no)

    def process_after_sales(self, mgmt_nos, tax_date, tax_no, export_no, saved_paths):
        return self.order_handler.process_after_sales(mgmt_nos, tax_date, tax_no, export_no, saved_paths)

    def update_order_status(self, mgmt_no, new_status, updates=None):
        return self.order_handler.update_status(mgmt_no, new_status, updates)

    def confirm_order(self, mgmt_no, confirm_data):
        return self.order_handler.confirm_order(mgmt_no, confirm_data)

    # Delegate to PaymentHandler
    def recalc_payment_status(self, dfs, mgmt_no):
        self.payment_handler.recalc_payment_status(dfs, mgmt_no)

    def add_payment(self, payment_data):
        return self.payment_handler.add_payment(payment_data)

    def process_payment(self, mgmt_nos, payment_amount, payment_date, file_paths, confirm_fee_callback=None):
        return self.payment_handler.process_payment(mgmt_nos, payment_amount, payment_date, file_paths, confirm_fee_callback)

    # Delegate to DeliveryHandler
    def get_next_delivery_id(self):
        return self.delivery_handler.get_next_delivery_id()

    def add_delivery(self, delivery_data):
        return self.delivery_handler.add_delivery(delivery_data)

    def process_delivery(self, delivery_no, delivery_date, invoice_no, shipping_method, waybill_path, update_requests):
        return self.delivery_handler.process_delivery(delivery_no, delivery_date, invoice_no, shipping_method, waybill_path, update_requests)

    def export_to_production_request(self, rows_data):
        return self.delivery_handler.export_to_production_request(rows_data)

    def sync_production_dates(self):
        self.delivery_handler.sync_production_dates()

    def get_production_status_map(self):
        return self.delivery_handler.get_production_status_map()

    def get_serial_number_map(self):
        return self.delivery_handler.get_serial_number_map()

    # Delegate to PurchaseHandler
    def get_next_purchase_id(self):
        return self.purchase_handler.get_next_purchase_id()

    def add_purchase(self, row_data):
        return self.purchase_handler.add_purchase(row_data)

    def update_purchase(self, mgmt_no, row_data):
        return self.purchase_handler.update_purchase(mgmt_no, row_data)

    def delete_purchase(self, mgmt_no):
        return self.purchase_handler.delete_purchase(mgmt_no)

    def save_purchase_data(self):
        return self.file_handler.save_purchase_data()

    # Common methods
    def set_dev_mode(self, enabled):
        self.is_dev_mode = enabled

    def execute_transaction(self, update_logic_func):
        if not os.path.exists(self.current_excel_path):
            return False, "엑셀 파일이 존재하지 않습니다."

        try:
            dfs = self.file_handler.read_all_sheets()
            dfs = self.file_handler.normalize_all(dfs)
            
            # 구매 데이터도 트랜잭션에 포함
            if self.df_purchase is not None:
                dfs["purchase"] = self.df_purchase
            
            success, msg = update_logic_func(dfs)
            if not success: return False, msg

            # dfs에 'purchase' 키가 있으면 구매 데이터 저장
            if "purchase" in dfs:
                self.df_purchase = dfs["purchase"]
                self.file_handler.save_purchase_data()

            self.file_handler.write_all_sheets(dfs)
            self.load_data()
            return True, "저장되었습니다."

        except PermissionError:
            return False, "엑셀 파일이 열려있습니다. 파일을 닫고 다시 시도해주세요."
        except Exception as e:
            return False, f"트랜잭션 오류: {e}"

    # For backward compatibility if needed, or internal use
    def _execute_transaction(self, update_logic_func):
        return self.execute_transaction(update_logic_func)