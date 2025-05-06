import sys
import os
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QListWidget, QVBoxLayout,
                               QHBoxLayout, QWidget, QGroupBox, QListWidgetItem, QPushButton,
                               QMessageBox, QFileDialog)
from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon


from auto_thread import initiate_auto_thread
from auto import is_similar

def read_project_path():
    """ Đọc đường dẫn đến thư mục dự án từ file config, sử dụng đường dẫn động. """
    config_path = os.path.join(
        os.path.expanduser("~"),
        "AppData", "Local", "CapCut", "User Data", "Config", "globalSetting"
    )
    try:
        with open(config_path, 'r') as file:
            for line in file:
                if line.startswith('currentCustomDraftPath='):
                    return line.strip().split('=')[1]
    except FileNotFoundError:
        print("File config không tồn tại.")

    return None

def read_language():
    language_path = os.path.join(
        os.path.expanduser("~"),
        "AppData", "Local", "CapCut", "User Data", "Config", "Language"
    )
    try:
        with open(language_path, 'r') as file:
            for line in file:
                if line.startswith('cur_lan='):
                    return line.strip().split('=')[1]
    except FileNotFoundError:
        print("File config không tồn tại.")
    return None

class ProjectSelector(QMainWindow):
    def __init__(self):
        super().__init__()
        self.project_path = read_project_path()  # Lấy đường dẫn từ file config
        if not self.project_path or not os.path.exists(self.project_path):
            self.handle_missing_path()
        self.language = int(read_language())
        if self.language is None:
            self.handle_missing_language()
        print(f"project_path = {self.project_path}")
        print(f"language = {self.language}")
        self.IMG_DIR = "images/vi"
        if self.language == 0: #English
            self.IMG_DIR = "images/en"
            print(f"IMG_DIR changed to {self.IMG_DIR}")

        self.initUI()

    
    def handle_missing_language(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Question)
        msg.setWindowTitle("Chọn Ngôn Ngữ")
        msg.setText("Không thể tự động phát hiện ngôn ngữ của Capcut, hãy chọn ngôn ngữ phù hợp:")

        # Thêm các nút lựa chọn
        btn_english = msg.addButton("Tiếng Anh", QMessageBox.AcceptRole)
        btn_vietnamese = msg.addButton("Tiếng Việt", QMessageBox.AcceptRole)

        # Hiển thị MessageBox và chờ người dùng phản hồi
        msg.exec_()

        # Kiểm tra kết quả và lưu vào self.language
        if msg.clickedButton() == btn_english:
            self.language = 0
        else:
            # Nếu người dùng không chọn "Tiếng Anh" hoặc đóng cửa sổ, mặc định là "Tiếng Việt"
            self.language = 20

        

    def handle_missing_path(self):
        # Hiển thị thông báo lỗi
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setText("Không thể tự động tìm đường dẫn. Hãy chọn folder chứa dự án.")
        msg.setWindowTitle("Lỗi Đường Dẫn")
        msg.setStandardButtons(QMessageBox.Ok)
        msg.exec()

        # Mở dialog để chọn folder
        folder = QFileDialog.getExistingDirectory(self, "Chọn Folder Chứa Dự Án")
        if folder:
            self.project_path = folder
        else:
            sys.exit(0)  # Thoát chương trình nếu không chọn folder

    def initUI(self):
        
        self.centralWidget = QWidget()
        self.setCentralWidget(self.centralWidget)
        mainLayout = QHBoxLayout(self.centralWidget)
        
        self.leftGroupBox = QGroupBox("Danh sách dự án")
        self.rightGroupBox = QGroupBox("Dự án được chọn")
        
        leftLayout = QVBoxLayout()
        rightLayout = QVBoxLayout()

        self.projectList = QListWidget()
        self.selectedProjectList = QListWidget()
        
        self.projectList.doubleClicked.connect(self.moveItemToRight)
        self.selectedProjectList.doubleClicked.connect(self.moveItemToLeft)
        
        self.projects = [(f, os.path.getmtime(os.path.join(self.project_path, f)))
                    for f in os.listdir(self.project_path)
                    if os.path.isdir(os.path.join(self.project_path, f)) and not f.startswith('.')]
        self.projects.sort(key=lambda x: x[1], reverse=True)
        self.projects = self.projects[:20]

        for project, _ in self.projects:
            self.projectList.addItem(QListWidgetItem(project))

        leftLayout.addWidget(self.projectList)
        rightLayout.addWidget(self.selectedProjectList)

        self.startButton = QPushButton("Bắt đầu")
        self.startButton.clicked.connect(self.displaySelectedProjects)
        rightLayout.addWidget(self.startButton)

        self.leftGroupBox.setLayout(leftLayout)
        self.rightGroupBox.setLayout(rightLayout)

        mainLayout.addWidget(self.leftGroupBox)
        mainLayout.addWidget(self.rightGroupBox)

        self.resetButton = QPushButton("Reset")
        self.resetButton.clicked.connect(self.resetLists)  # Kết nối nút với hàm resetLists
        leftLayout.addWidget(self.resetButton)  # Thêm nút vào layout bên trái

        self.leftGroupBox.setLayout(leftLayout)

        self.setWindowTitle('Chọn Dự Án')
        self.resize(800, 400)

    def resetLists(self):
        """Hàm này reset các danh sách và tải lại danh sách dự án."""
        self.projectList.clear()  # Xóa danh sách hiện tại
        self.selectedProjectList.clear()  # Xóa danh sách dự án được chọn
        self.loadProjects()  # Tải lại danh sách dự án

    def loadProjects(self):
        """Tải và hiển thị danh sách dự án từ thư mục dự án."""
        self.projectList.clear()
        self.projects = [(f, os.path.getmtime(os.path.join(self.project_path, f)))
                            for f in os.listdir(self.project_path)
                            if os.path.isdir(os.path.join(self.project_path, f)) and not f.startswith('.')]
        self.projects.sort(key=lambda x: x[1], reverse=True)
        self.projects = self.projects[:20]  # Giới hạn lấy 20 dự án mới nhất

        for project, _ in self.projects:
            self.projectList.addItem(QListWidgetItem(project))

    def moveItemToRight(self):
        selected_item = self.projectList.currentItem()
        if selected_item:
            self.selectedProjectList.insertItem(0, QListWidgetItem(selected_item.text()))
            row = self.projectList.row(selected_item)
            self.projectList.takeItem(row)

    def moveItemToLeft(self):
        selected_item = self.selectedProjectList.currentItem()
        if selected_item:
            self.projectList.insertItem(0, QListWidgetItem(selected_item.text()))
            row = self.selectedProjectList.row(selected_item)
            self.selectedProjectList.takeItem(row)

    def displaySelectedProjects(self):
        selected_projects = [self.selectedProjectList.item(i).text() for i in range(self.selectedProjectList.count())]
        
        print("Các dự án đã chọn để xử lý:", selected_projects)
        selected_projects.reverse()
        print("Các dự án đã chọn để xử lý:", selected_projects)
        if any(" " in project for project in selected_projects):
            is_remove = self.remove_space()
            if is_remove:
                print("Ok remove space in project name...")
                return  # Hủy thực thi nếu người dùng không muốn tiếp tục
            else:
                print("Continue without remove space in project name...")
        all_projects = selected_projects + [item[0] for item in self.projects]
        print(all_projects)
        if not self.ignore_project_similarity(selected_projects=selected_projects, all_projects=all_projects):
            print("Ok edit project...")
            return
        print(
            "Continue without edit project...")

        if selected_projects and len(selected_projects) > 0:
            self.showMinimized()
            initiate_auto_thread(selected_projects, self.IMG_DIR)

        
    def remove_space(self):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Cảnh Báo Tên Dự Án")
        msg.setText("Tên dự án có chứa khoảng trắng có thể khiến Auto không nhận diện được đúng dự án. \n Hãy đổi tên dự án tránh nhầm lẫn!!!")
        msg.setInformativeText("Tiếp tục mà không đổi tên chứ?")
        btn_cancel = msg.addButton("Để tôi sửa", QMessageBox.ButtonRole.RejectRole)  # Đặt vai trò là RejectRole
        btn_ok = msg.addButton("Tiếp tục, không cần sửa", QMessageBox.ButtonRole.AcceptRole)  # Đặt vai trò là AcceptRole
        msg.setDefaultButton(btn_cancel)  # Đặt nút mặc định

        msg.exec()
        # Kiểm tra kết quả để xem nút nào đã được nhấn
        if msg.clickedButton() == btn_ok:
            print("remove_space User chose to continue without renaming.")
            return False
        print("remove_space  chose to cancel.")
        return True
    

    def ignore_project_similarity(self, selected_projects, all_projects):
        similar_projects = set()
        for i, proj1 in enumerate(selected_projects):
            for proj2 in selected_projects[i+1:] + all_projects:
                is_same, ratio = is_similar(proj1, proj2)
                if is_same and ratio < 1.0:
                    ordered_pair = tuple(sorted((proj1, proj2)))
                    similar_projects.add(ordered_pair)
            
        if similar_projects:
            return self.show_warning_similar(similar_projects)
        return True

    def show_warning_similar(self, similar_pairs):
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Warning)
        msg.setWindowTitle("Cảnh báo tương đồng dự án")
        message_text = "Các dự án sau đây khá giống nhau, auto có thể nhầm lẫn giữa chúng:\n\n"
        message_text += "\n".join(f"{proj1} và {proj2}" for proj1, proj2 in similar_pairs)
        msg.setText(message_text)
        msg.setInformativeText("Bạn hãy đổi tên dự án để tránh nhầm lẫn")
         # Thêm các nút tùy chỉnh với nhãn và vai trò
        btn_cancel = msg.addButton("Để tôi sửa", QMessageBox.ButtonRole.RejectRole)
        btn_continue = msg.addButton("Tiếp tục, không cần sửa", QMessageBox.ButtonRole.AcceptRole)
        
        msg.setDefaultButton(btn_cancel)
        msg.exec_()
        # Kiểm tra kết quả để xem nút nào đã được nhấn
        if msg.clickedButton() == btn_continue:
            print("User chose to continue without renaming.")
            return True
        print("User chose to cancel.")
        return False

def main():
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon("icon.ico"))
    ex = ProjectSelector()
    ex.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
