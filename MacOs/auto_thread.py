import threading
import time
from auto import start_auto

# Hàm khởi tạo và bắt đầu thread
def initiate_auto_thread(projects, IMG_DIR):
    auto_thread = threading.Thread(target=start_auto, args=(projects,IMG_DIR,))
    auto_thread.start()
    return auto_thread

# Cách sử dụng:
# projects = ["Project1", "Project2", "Project3"]
# thread = initiate_auto_thread(projects)
