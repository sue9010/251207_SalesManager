import win32gui
import time

def get_active_window_info():
    print("--- 창 크기 측정기 시작 (종료하려면 Ctrl+C) ---")
    try:
        last_hwnd = None
        
        while True:
            # 1. 현재 가장 위에 있는(활성화된) 창의 핸들(ID)을 가져옵니다.
            hwnd = win32gui.GetForegroundWindow()
            
            # 2. 창이 존재하고, 이전과 다른 창이거나(새로 클릭), 루프가 돌 때마다 체크
            if hwnd:
                # 창의 좌표(Left, Top, Right, Bottom)를 가져옵니다.
                rect = win32gui.GetWindowRect(hwnd)
                x = rect[0]
                y = rect[1]
                w = rect[2] - x
                h = rect[3] - y
                
                # 창의 제목을 가져옵니다.
                text = win32gui.GetWindowText(hwnd)

                # 보기 좋게 출력
                # 너무 빠르게 출력되면 정신없으므로 약간의 텀을 줍니다.
                print(f"[활성 창] 제목: {text} | 크기: {w} x {h} | 위치: ({x}, {y})")
            
            # 0.5초마다 갱신 (원하는대로 조절 가능)
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\n측정을 종료합니다.")

if __name__ == "__main__":
    get_active_window_info()