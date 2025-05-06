import pyautogui
import pytesseract
from PIL import Image
import os

pytesseract.pytesseract.tesseract_cmd = "/opt/homebrew/bin/tesseract"  # chỉnh theo máy bạn

img = pyautogui.screenshot()
img.save("screen.png")
print("Đã chụp màn hình!")

text = pytesseract.image_to_string(img, lang="eng")
print("Kết quả OCR:")
print(text)