import pyautogui


def highlight_area(center, size=50):
    x, y = center
    offset = size // 2
    print("[INFO] Highlight vùng nút...")
    pyautogui.moveTo(x - offset, y - offset, duration=0.2)
    pyautogui.moveTo(x + offset, y - offset, duration=0.2)
    pyautogui.moveTo(x + offset, y + offset, duration=0.2)
    pyautogui.moveTo(x - offset, y + offset, duration=0.2)
    pyautogui.moveTo(x, y, duration=0.2)


result = pyautogui.locateCenterOnScreen('images/confirm_export.png', confidence=0.8)
print("Kết quả tìm:", result)

highlight_area(result)