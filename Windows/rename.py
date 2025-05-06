import os
from glob import glob
import tkinter as tk
from tkinter import filedialog
def rename_files_in_directory():
    # Thiết lập giao diện chọn folder
    root = tk.Tk()
    root.withdraw()  # Giấu cửa sổ Tkinter
    directory = filedialog.askdirectory()  # Hiển thị dialog chọn thư mục

    if not directory:
        print("Không có thư mục nào được chọn.")
        return

    # Lấy tất cả các file .png và .PNG trong thư mục
    files = glob(os.path.join(directory, '*.png')) + glob(os.path.join(directory, '*.PNG'))

    # Đổi tên các file
    for file_path in files:
        new_file_path = os.path.join(directory, os.path.splitext(os.path.basename(file_path))[0] + ".png")
        if file_path != new_file_path:  # Chỉ đổi tên nếu cần thiết
            os.rename(file_path, new_file_path)
            print(f"Đã đổi tên: {file_path} -> {new_file_path}")
        else:
            print(f"Không cần đổi tên: {file_path}")

    print("Hoàn thành đổi tên các file.")

# Chạy hàm
rename_files_in_directory()
