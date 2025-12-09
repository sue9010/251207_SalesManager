import os

class Config:
    APP_VERSION = "1.0.0"
    
    # 파일 경로 설정
    DEFAULT_EXCEL_PATH = "sales_data.xlsx"
    DEFAULT_PURCHASE_DATA_PATH = "purchase_data.xlsx"
    DEFAULT_ATTACHMENT_ROOT = "attachments"
    DEFAULT_PRODUCTION_REQUEST_PATH = "production_request.xlsx"
    DEFAULT_ORDER_REQUEST_DIR = "order_requests"
    CONFIG_FILENAME = "config.json"
    
    # 폼(템플릿) 파일 경로 (항상 attachments/forms 참조)
    FORMS_DIR = os.path.join("attachments", "forms")
    ORDER_REQUEST_FORM_PATH = os.path.join(FORMS_DIR, "order_request_form.xlsx")
    
    # 시트 이름 설정
    SHEET_CLIENTS = "Clients"
    SHEET_DATA = "Data"
    SHEET_PAYMENT = "Payment"
    SHEET_DELIVERY = "Delivery"
    SHEET_LOG = "Log"
    SHEET_MEMO = "Memo"
    SHEET_MEMO_LOG = "MemoLog"
    
    # 개발자 모드 비밀번호
    DEV_PASSWORD = "admin" 
    
    # 컬럼 설정 (추론된 값)
    CLIENT_COLUMNS = ["업체명", "사업자번호", "대표자", "전화번호", "이메일", "주소", "특이사항", "운송방법", "운송계정"]
    
    DATA_COLUMNS = [
        "관리번호", "업체명", "모델명", "Description", "수량", "단가", "환율", "세율(%)", 
        "공급가액", "세액", "합계금액", "기수금액", "미수금액", 
        "견적일", "수주일", "출고예정일", "출고일", "선적일", "입금완료일", "세금계산서발행일",
        "계산서번호", "수출신고번호", "수출신고필증경로",
        "Status", "비고", "주문요청사항"
    ]
    
    PAYMENT_COLUMNS = ["관리번호", "일시", "입금액", "비고", "외화입금증빙경로", "송금상세경로"]
    DELIVERY_COLUMNS = ["출고번호", "일시", "관리번호", "수량", "박스수량", "비고", "운송장경로"]
    LOG_COLUMNS = ["일시", "작업자", "구분", "상세내용"]
    MEMO_COLUMNS = ["관리번호", "내용", "작성일"]
    MEMO_LOG_COLUMNS = ["일시", "작업자", "내용"]
    
    # 검색 대상 컬럼
    SEARCH_TARGET_COLS = ["업체명", "모델명", "Description", "관리번호"]
