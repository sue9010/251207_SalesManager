# [변경] ui.popups 패키지 경로로 수정
from ui.popups.client_popup import ClientPopup
from ui.popups.production_popup import ProductionPopup
from ui.popups.payment_popup import PaymentPopup
from ui.popups.quote_popup import QuotePopup
from ui.popups.order_popup import OrderPopup
from ui.popups.complete_popup import CompletePopup
from ui.popups.settings_popup import SettingsPopup
from ui.popups.packing_list_popup import PackingListPopup
from ui.popups.after_sales_popup import AfterSalesPopup
from ui.popups.purchase_popup import PurchasePopup


class PopupManager:
    def __init__(self, parent, data_manager, refresh_callback):
        self.parent = parent
        self.dm = data_manager
        self.refresh_callback = refresh_callback

    def open_settings(self):
        win = SettingsPopup(self.parent, self.dm, self.refresh_callback)

    def open_client_popup(self, client_name=None):
        win = ClientPopup(self.parent, self.dm, self.refresh_callback, client_name)

    def open_quote_popup(self, mgmt_no=None, copy_mode=False):
        win = QuotePopup(self.parent, self.dm, self.refresh_callback, mgmt_no, copy_mode=copy_mode)

    def open_order_popup(self, mgmt_no=None, copy_mode=False):
        win = OrderPopup(self.parent, self.dm, self.refresh_callback, mgmt_no, copy_mode=copy_mode)

    def open_production_popup(self, mgmt_nos):
        win = ProductionPopup(self.parent, self.dm, self.refresh_callback, mgmt_nos)

    def open_payment_popup(self, mgmt_nos):
        win = PaymentPopup(self.parent, self.dm, self.refresh_callback, mgmt_nos)

    def open_complete_popup(self, mgmt_no):
        win = CompletePopup(self.parent, self.dm, self.refresh_callback, mgmt_no)

    def open_packing_list_popup(self, mgmt_no):
        win = PackingListPopup(self.parent, self.dm, self.refresh_callback, mgmt_no)

    def open_after_sales_popup(self, mgmt_nos):
        win = AfterSalesPopup(self.parent, self.dm, self.refresh_callback, mgmt_nos)

    def open_purchase_popup(self, mgmt_no=None, copy_mode=False):
        win = PurchasePopup(self.parent, self.dm, self.refresh_callback, mgmt_no, copy_mode=copy_mode)