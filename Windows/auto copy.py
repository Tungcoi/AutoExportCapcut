import pyautogui
import time
import os
from enum import IntEnum
import pytesseract
from PIL import Image, ImageDraw
import cv2
import numpy as np
from difflib import SequenceMatcher
import logging
from datetime import datetime
import subprocess
# Gắn thủ công đường dẫn tới file tesseract.exe
# pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
pytesseract.pytesseract.tesseract_cmd = os.path.abspath("Tesseract-OCR/tesseract.exe")
print(pytesseract.pytesseract.tesseract_cmd)

GRID_ROWS = 3
GRID_COLS = 3

class RegionPosition(IntEnum):
    TOP_LEFT = 0
    TOP_CENTER = 1
    TOP_RIGHT = 2
    CENTER_LEFT = 3
    CENTER = 4
    CENTER_RIGHT = 5
    BOTTOM_LEFT = 6
    BOTTOM_CENTER = 7
    BOTTOM_RIGHT = 8

def is_similar(a, b, threshold=0.8):
    ratio = SequenceMatcher(None, a.lower(), b.lower()).ratio()
    return ratio >= threshold, ratio


# Thiết lập thư mục và file log
log_directory = None 

def setup_logging():
    global log_directory
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    log_directory = os.path.join(os.getcwd(), 'logs', timestamp)
    print(f"setup_logging log_directory = {log_directory}")
    os.makedirs(log_directory, exist_ok=True)
    
    # Thiết lập file log
    logging.basicConfig(filename=os.path.join(log_directory, 'log.txt'),
                        level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        datefmt='%Y-%m-%d %H:%M:%S',
                        encoding='utf-8')
    print(f"setup_logging log_directory = {log_directory}")
    return log_directory




def screenshot_center_quarter():
    screen_width, screen_height = pyautogui.size()
    quarter_w = screen_width // 4
    quarter_h = screen_height // 4
    left = quarter_w
    top = quarter_h
    width = quarter_w * 2
    height = quarter_h * 2
    logging.info(f"[INFO] Chụp vùng trung tâm: ({left}, {top}, {width}, {height})")
    screenshot = pyautogui.screenshot(region=(left, top, width, height))
    return screenshot, left, top

def click_on_project_by_name(project_name: str, strict=False, try_times=5):
    logging.info(f"[INFO] Đang tìm project: {project_name}")
    global log_directory
    print(f"click_on_project_by_name log_directory = {log_directory}")
    
    refer_ratio = 1.0
    for attempt in range(try_times):
        screenshot, offset_x, offset_y = screenshot_center_quarter()
        img = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        data = pytesseract.image_to_data(img, lang='eng', output_type=pytesseract.Output.DICT)
        logging.info(data['text'])

        best_match = None
        highest_ratio = 0
        rect_start = None
        rect_end = None
        logging.info(f"click_on_project_by_name {project_name} with ration = {int(refer_ratio*100)} %")
        for i, text in enumerate(data['text']):
            if not text.strip():
                continue

            match = False
            if strict:
                match = project_name.lower() in text.lower()
                ratio = 1.0 if match else 0
            else:
                match, ratio = is_similar(project_name, text)

            if match and ratio > highest_ratio:
                highest_ratio = ratio
                x = data['left'][i] + offset_x
                y = data['top'][i] + offset_y
                w = data['width'][i]
                h = data['height'][i]
                rect_start = (data['left'][i], data['top'][i])  # Tọa độ góc trên bên trái
                rect_end = (data['left'][i] + w, data['top'][i] + h)  # Tọa độ góc dưới bên phải
                best_match = (x + w // 2, y - h, ratio)

        if best_match:
            screenshot = Image.frombytes('RGB', screenshot.size, screenshot.tobytes())
            draw = ImageDraw.Draw(screenshot)
            draw.rectangle([rect_start, rect_end], outline="red", width=5)

        filename = f"{int(time.time())}_Find_{project_name}_{attempt}.png"
        screenshot_path = os.path.join(log_directory, filename)
        screenshot.save(screenshot_path)
        logging.info(f"[DEBUG] Ảnh OCR đã lưu tại: {screenshot_path}")

        if best_match:
            x, y, ratio = best_match
            if ratio >= refer_ratio:
                logging.info(f"[INFO] Tìm thấy kết quả tốt nhất '{project_name}' với ratio {ratio} tại ({x},{y})")
                # highlight_area((x, y), size=60)
                pyautogui.moveTo(x, y, duration=0.3)
                time.sleep(1)
                pyautogui.click()
                return True
        refer_ratio -= 0.1
  
    logging.info(f"[WARN] Không tìm thấy project tên gần giống: {project_name} sau {try_times} lần thử")
    return False
    


def get_region_from_enum(pos_enum: RegionPosition, scale: float = 1.0):
    screen_width, screen_height = pyautogui.size()
    cell_width = screen_width / GRID_COLS
    cell_height = screen_height / GRID_ROWS

    index = int(pos_enum)
    row = index // GRID_COLS
    col = index % GRID_COLS

    # Tọa độ vùng gốc
    x = col * cell_width
    y = row * cell_height

    # Tính tâm vùng gốc
    center_x = x + cell_width / 2
    center_y = y + cell_height / 2

    # Scale vùng theo tâm
    scaled_w = cell_width * scale
    scaled_h = cell_height * scale

    new_x = int(center_x - scaled_w / 2)
    new_y = int(center_y - scaled_h / 2)
    new_w = int(scaled_w)
    new_h = int(scaled_h)

    # Ràng giới hạn không vượt khỏi màn hình
    new_x = max(0, new_x)
    new_y = max(0, new_y)
    if new_x + new_w > screen_width:
        new_w = screen_width - new_x
    if new_y + new_h > screen_height:
        new_h = screen_height - new_y

    return (new_x, new_y, new_w, new_h)


def highlight_region(region, padding=5):
    screen_width, screen_height = pyautogui.size()
    x, y, w, h = region

    # Co lại vùng để tránh đụng sát góc màn hình (gây fail-safe)
    x += padding
    y += padding
    w -= 2 * padding
    h -= 2 * padding

    # Nếu vùng bị co quá nhỏ hoặc âm thì bỏ qua
    if w <= 0 or h <= 0 or x + w > screen_width or y + h > screen_height:
        logging.info(f"[WARN] Vùng {region} sau padding bị lỗi! Bỏ qua highlight.")
        return

    logging.info(f"[INFO] Highlight vùng tìm kiếm (co lại): ({x}, {y}, {w}, {h})")
    pyautogui.moveTo(x, y, duration=0.2)
    pyautogui.moveTo(x + w, y, duration=0.2)
    pyautogui.moveTo(x + w, y + h, duration=0.2)
    pyautogui.moveTo(x, y + h, duration=0.2)
    pyautogui.moveTo(x, y, duration=0.2)


def highlight_area(center, size=50):
    x, y = center
    offset = size // 2
    logging.info("[INFO] Highlight vùng nút...")
    pyautogui.moveTo(x - offset, y - offset, duration=0.2)
    pyautogui.moveTo(x + offset, y - offset, duration=0.2)
    pyautogui.moveTo(x + offset, y + offset, duration=0.2)
    pyautogui.moveTo(x - offset, y + offset, duration=0.2)
    pyautogui.moveTo(x, y, duration=0.2)

def locate_and_click(IMG_DIR, image_name, timeout=30, highlight=False, wait_before_click=2, region_pos=None, region_scale=1):
    region = get_region_from_enum(region_pos, region_scale) if region_pos else None
    image_path = f"{IMG_DIR}/{image_name}"

    logging.info(f"[INFO] Tìm và xử lý nút: {image_path} (region={region})")
    start = time.time()
    try_time = 1
    while time.time() - start < timeout:
        try:
            logging.info(f"[DEBUG] Region: {region}")
            location = pyautogui.locateOnScreen(image_path, confidence=0.8, region=region)
            screenshot = pyautogui.screenshot(region= region)
            filename = f"{int(time.time())}_Click_{image_name}_{try_time}.png"
            if location:
                x = location.left
                y = location.top
                w = location.width
                h = location.height
                rect_start = (x, y)  # Tọa độ góc trên bên trái
                rect_end = (x + w, y + h)  # Tọa độ góc dưới bên phải
                screenshot = Image.frombytes('RGB', screenshot.size, screenshot.tobytes())
                draw = ImageDraw.Draw(screenshot)
                draw.rectangle([rect_start, rect_end], outline="red", width=5)
            global log_directory
            screenshot_path = os.path.join(log_directory, filename)
            screenshot.save(screenshot_path)
            logging.info(f"[DEBUG] Found location: {location}")
            if location:
                if highlight:
                    highlight_area(location)
                pyautogui.moveTo(location, duration=0.3)
                logging.info(f"[INFO] Đã di chuột đến {image_path}, chờ {wait_before_click}s rồi click...")
                time.sleep(wait_before_click)
                pyautogui.click()
                return True
            time.sleep(1)
        except pyautogui.ImageNotFoundException:
            pass
        try_time += 1

    logging.info(f"[WARN] Không tìm thấy nút: {image_path}")
    return False

def open_project(path):
    logging.info(f"[INFO] Mở project: {path}")
    os.startfile(path)
    time.sleep(10)

def wait_for_project_load():
    logging.info("[INFO] Chờ load project (~30s)...")
    time.sleep(30)

def export_video(IMG_DIR):
    if not locate_and_click(IMG_DIR, 'export_button.png', region_pos=RegionPosition.TOP_RIGHT):
        return False
    time.sleep(5)
    if not locate_and_click(IMG_DIR, 'confirm_export.png'):
        return False
    return True

def wait_render_done(IMG_DIR):
    logging.info("[INFO] Chờ render (tối đa 180 phút)...")
    timeout = 180 * 60
    start = time.time()
    image_path = f"{IMG_DIR}/done_popup.png"

   
    while time.time() - start < timeout:
        logging.info(f"[INFO] đợi render bằng {image_path}")
        try:
            found = pyautogui.locateOnScreen(image_path, confidence=0.8)
        except pyautogui.ImageNotFoundException:
            logging.info(f"[WARN] Không tìm thấy ảnh {image_path} - thử lại sau 10s.")
            found = None

        if found:
            logging.info("[INFO] Render xong!")
            locate_and_click(IMG_DIR, 'cancel_button.png', timeout=15)
            logging.info("[INFO] Render xong! Đã đóng popup. Nghỉ 5 giây...")
            time.sleep(5)
            logging.info("[INFO] Render xong! Đã đóng popup. Nghỉ 5 giây xong...")
            return True

        time.sleep(10)


    logging.info("[ERROR] Timeout render!")
    return False


def close_project(IMG_DIR):
    if locate_and_click(IMG_DIR, 'close_project.png', timeout=10, region_pos=RegionPosition.TOP_RIGHT):
        logging.info("[INFO] Đã đóng project.")
    else:
        logging.info("[INFO] fallback alt + f4... Đã đóng project.")
        pyautogui.hotkey('alt', 'f4')  # fallback

def wait_for_project_to_load(IMG_DIR):
    loading_image_path = f"{IMG_DIR}/project_loading.png"
    timeout = 300  # Giới hạn thời gian chờ là 120 giây
    start_time = time.time()
    region =get_region_from_enum(RegionPosition.CENTER)
    count = 0
    while time.time() - start_time < timeout:
        try:
            if pyautogui.locateOnScreen(loading_image_path, confidence=0.8, region= region):
                logging.info("[INFO] Waiting for project to load...")
                time.sleep(2)  # Kiểm tra mỗi 2 giây
                count += 1
        except Exception as e:
            # Xử lý các ngoại lệ phát sinh
            logging.error(f"[ERROR] Error while locating loading screen: {str(e)}") 
            return True, count
    
    logging.info("[ERROR] Timeout while waiting for project to load.")
    return False, count

def start_auto(projects, existing_names, project_path, IMG_DIR,capcut_exe, export_path):
    # Gọi hàm setup_logging ở đầu script hoặc trong hàm main/start_auto
    global log_directory
    log_directory = setup_logging()
    logging.info(f"start_auto log_directory = {log_directory}")
    logging.info(f"Thư mục chứa ảnh mẫu : {IMG_DIR}") 
    for project in projects:
        rename = False
        render_done = False
        try:
            original_path = os.path.join(project_path, project)
            safe_name = generate_unique_name(existing_names)
            new_path = os.path.join(project_path, safe_name)
            time.sleep(3)
            try:
                os.rename(original_path, new_path)
                rename = True
                print(f"Đổi tên '{original_path}' thành '{new_path}'")
            except Exception as e:
                logging.critical(f"Không thể đổi tên dự án '{project}': {e}")
            if rename:
             # Kill CapCut nếu đang chạy
                subprocess.run(["taskkill", "/f", "/im", "CapCut.exe"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(3)
                subprocess.Popen([capcut_exe])
                time.sleep(5)  # chờ CapCut load xong

                if click_on_project_by_name(safe_name) :
                    time.sleep(10)
                    wait_status, count = wait_for_project_to_load(IMG_DIR)
                    if not wait_status:
                        logging.info(f"[ERROR] Không thể load project sau khi chờ đợi {count * 2} giây ")
                        close_project(IMG_DIR)
                        time.sleep(10)
                        continue 
                    print(f"load project count  = {count}")
                    time.sleep(10*count)
                    start_time = time.time()
                    if export_video(IMG_DIR):
                        render_done = wait_render_done(IMG_DIR)
                        close_project(IMG_DIR)
                        logging.info(f"render_done = {render_done}")

                    if render_done:
                        for f in os.listdir(export_path):
                            logging.info(f"[INFO] Tìm thấy file xuất: {f}")
                            full_path = os.path.join(export_path, f)
                            if safe_name.lower() in f.lower():
                                if os.path.isfile(full_path) and os.path.getmtime(full_path) > start_time:
                                    full_path = os.path.join(export_path, f)
                                    ext = os.path.splitext(full_path)[1] 
                                    org_path = os.path.join(export_path, f"{project}{ext}")
                                    if os.path.exists(org_path):
                                        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                                        org_path = os.path.join(export_path, f"{project}_{timestamp}{ext}")
                                        for _ in range(3):
                                            if os.path.exists(full_path):
                                                try:
                                                    os.rename(full_path, org_path)
                                                    logging.info(f"[INFO] Đã đổi tên video {full_path} xuất thành: {org_path}")
                                                    break
                                                except Exception as e:
                                                    logging.error(f"[ERROR] Không thể đổi tên video {full_path} xuất thành: {org_path} - {e}")
                                                time.sleep(5)
                                        break
                else:
                    logging.info("[ERROR] Không thể tìm thấy project")
                time.sleep(10)
        except Exception as e:
            logging.error(f"[ERROR] Lỗi gì đó chưa xử lý được... {e}") 
        if rename:
            try:
                os.rename(new_path, original_path)
                print(f"Đổi tên '{new_path}' thành '{original_path}'")
            except Exception as e:
                logging.critical(f"Không thể đổi tên dự án '{project}': {e}")

    os.startfile(f"{log_directory}/log.txt")
    os.startfile(log_directory)

import difflib
import random
import string

def generate_unique_name(existing_names):
    while True:
        new_name = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        similarities = [
            difflib.SequenceMatcher(None, new_name.lower(), existing.lower()).ratio()
            for existing in existing_names
        ]
        if all(sim < 0.5 for sim in similarities):
            return new_name