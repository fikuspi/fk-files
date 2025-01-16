import os
import sys
import json
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QFileSystemModel, QListView, QSplitter,
    QToolBar, QAction, QLineEdit, QStatusBar, QMessageBox, QMenu, QDockWidget, QListWidget, QListWidgetItem, QInputDialog
)
from PyQt5.QtGui import QIcon, QKeySequence
from PyQt5.QtCore import Qt, QDir, QSize, QMimeData, QTimer


class FileManager(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FK-Files")
        self.setGeometry(100, 100, 1024, 768)

        self.config_file = os.path.join(QDir.homePath(), ".fk_files_config.json")
        self.pinned_folders = self.load_pinned_folders()

        self.model = QFileSystemModel()
        self.model.setRootPath(QDir.homePath())
        self.model.setFilter(QDir.AllEntries | QDir.NoDotAndDotDot | QDir.Hidden)

        self.list_view = QListView()
        self.list_view.setModel(self.model)
        self.list_view.setRootIndex(self.model.index(QDir.homePath()))
        self.list_view.setViewMode(QListView.IconMode)
        self.list_view.setUniformItemSizes(True)
        self.list_view.setIconSize(QSize(64, 64))
        self.list_view.doubleClicked.connect(self.on_item_double_clicked)
        self.list_view.setDragEnabled(True)

        self.sidebar = QDockWidget("Panel", self)
        self.sidebar.setFeatures(QDockWidget.NoDockWidgetFeatures)
        self.sidebar_widget = QListWidget()
        self.sidebar_widget.itemClicked.connect(self.on_sidebar_item_clicked)
        self.sidebar_widget.setAcceptDrops(True)
        self.sidebar_widget.dragEnterEvent = self.dragEnterEvent
        self.sidebar_widget.dropEvent = self.dropEvent
        self.sidebar_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.sidebar_widget.customContextMenuRequested.connect(self.show_sidebar_context_menu)
        self.sidebar.setWidget(self.sidebar_widget)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.sidebar)
        self.update_sidebar()

        self.toolbar = QToolBar()
        self.addToolBar(self.toolbar)

        self.back_action = QAction(QIcon.fromTheme("go-previous"), "Back", self)
        self.back_action.setShortcut(QKeySequence("Backspace"))
        self.back_action.triggered.connect(self.go_back)
        self.toolbar.addAction(self.back_action)

        self.forward_action = QAction(QIcon.fromTheme("go-next"), "Forward", self)
        self.forward_action.setShortcut(QKeySequence("Ctrl+F"))
        self.forward_action.triggered.connect(self.go_forward)
        self.toolbar.addAction(self.forward_action)

        self.home_action = QAction(QIcon.fromTheme("go-home"), "Home", self)
        self.home_action.setShortcut(QKeySequence("Ctrl+H"))
        self.home_action.triggered.connect(self.go_home)
        self.toolbar.addAction(self.home_action)

        self.refresh_action = QAction(QIcon.fromTheme("view-refresh"), "Refresh", self)
        self.refresh_action.setShortcut(QKeySequence("F5"))
        self.refresh_action.triggered.connect(self.refresh)
        self.toolbar.addAction(self.refresh_action)

        self.pin_action = QAction(QIcon.fromTheme("list-add"), "Pin Folder", self)
        self.pin_action.triggered.connect(self.pin_current_folder)
        self.toolbar.addAction(self.pin_action)

        self.toggle_hidden_action = QAction(QIcon.fromTheme("view-hidden"), "Show Hidden", self)
        self.toggle_hidden_action.setCheckable(True)
        self.toggle_hidden_action.toggled.connect(self.toggle_hidden_files)
        self.toolbar.addAction(self.toggle_hidden_action)

        self.path_edit = QLineEdit()
        self.path_edit.returnPressed.connect(self.navigate_to_path)
        self.toolbar.addWidget(self.path_edit)

        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(self.list_view)
        self.setCentralWidget(self.splitter)

        self.history = []
        self.history_index = -1

        self.current_path = QDir.homePath()
        self.update_path(self.model.index(self.current_path))

        self.list_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_view.customContextMenuRequested.connect(self.show_context_menu)

        self.drive_check_timer = QTimer()
        self.drive_check_timer.timeout.connect(self.update_sidebar)
        self.drive_check_timer.start(5000)

    def load_pinned_folders(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, "r") as f:
                return json.load(f)
        return [
            QDir.homePath(),
            os.path.join(QDir.homePath(), "Documents"),
            os.path.join(QDir.homePath(), "Downloads"),
        ]

    def save_pinned_folders(self):
        with open(self.config_file, "w") as f:
            json.dump(self.pinned_folders, f)

    def update_sidebar(self):
        self.sidebar_widget.clear()
        self.pinned_folders = [folder for folder in self.pinned_folders if os.path.exists(folder)]
        self.save_pinned_folders()

        for folder in self.pinned_folders:
            item = QListWidgetItem(QIcon.fromTheme("folder"), os.path.basename(folder))
            item.setData(Qt.UserRole, folder)
            self.sidebar_widget.addItem(item)

        drives = QDir.drives()
        for drive in drives:
            drive_path = drive.absolutePath()
            item = QListWidgetItem(QIcon.fromTheme("drive-harddisk"), drive_path)
            item.setData(Qt.UserRole, drive_path)
            self.sidebar_widget.addItem(item)

    def pin_current_folder(self):
        if self.current_path not in self.pinned_folders:
            self.pinned_folders.append(self.current_path)
            self.update_sidebar()
            self.save_pinned_folders()

    def on_sidebar_item_clicked(self, item):
        path = item.data(Qt.UserRole)
        self.list_view.setRootIndex(self.model.index(path))
        self.add_to_history(path)

    def update_path(self, index):
        self.current_path = self.model.filePath(index)
        self.path_edit.setText(self.current_path)
        self.status_bar.showMessage(f"Files: {self.model.rowCount(index)}")

    def navigate_to_path(self):
        path = self.path_edit.text()
        if os.path.exists(path):
            self.list_view.setRootIndex(self.model.index(path))
            self.add_to_history(path)
        else:
            QMessageBox.warning(self, "Error", "The specified path does not exist.")

    def on_item_double_clicked(self, index):
        path = self.model.filePath(index)
        if os.path.isdir(path):
            self.list_view.setRootIndex(index)
            self.add_to_history(path)
        else:
            self.open_file(path)

    def open_file(self, path):
        try:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            program, ok = QInputDialog.getText(self, "Open With", "Enter the program to open the file:")
            if ok and program:
                try:
                    subprocess.Popen([program, path])
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"Failed to open file: {e}")

    def go_back(self):
        if self.history_index > 0:
            self.history_index -= 1
            self.navigate_to_history()

    def go_forward(self):
        if self.history_index < len(self.history) - 1:
            self.history_index += 1
            self.navigate_to_history()

    def go_home(self):
        self.list_view.setRootIndex(self.model.index(QDir.homePath()))
        self.add_to_history(QDir.homePath())

    def refresh(self):
        self.list_view.setRootIndex(self.model.index(self.current_path))

    def add_to_history(self, path):
        if self.history_index < len(self.history) - 1:
            self.history = self.history[:self.history_index + 1]
        self.history.append(path)
        self.history_index += 1

    def navigate_to_history(self):
        path = self.history[self.history_index]
        self.list_view.setRootIndex(self.model.index(path))
        self.path_edit.setText(path)

    def toggle_hidden_files(self, checked):
        if checked:
            self.model.setFilter(QDir.AllEntries | QDir.NoDotAndDotDot | QDir.Hidden)
        else:
            self.model.setFilter(QDir.AllEntries | QDir.NoDotAndDotDot)

    def show_context_menu(self, position):
        index = self.list_view.indexAt(position)
        if not index.isValid():
            return

        path = self.model.filePath(index)
        menu = QMenu()

        if os.path.isdir(path):
            open_action = menu.addAction("Open")
            open_with_action = menu.addAction("Open With...")
            rename_action = menu.addAction("Rename")
            delete_action = menu.addAction("Delete")
            pin_action = menu.addAction("Pin to Panel")

            open_action.triggered.connect(lambda: self.on_item_double_clicked(index))
            open_with_action.triggered.connect(lambda: self.open_with(path))
            rename_action.triggered.connect(lambda: self.rename_item(index))
            delete_action.triggered.connect(lambda: self.delete_item(index))
            pin_action.triggered.connect(lambda: self.pin_folder(path))
        else:
            open_action = menu.addAction("Open")
            open_with_action = menu.addAction("Open With...")
            rename_action = menu.addAction("Rename")
            delete_action = menu.addAction("Delete")

            open_action.triggered.connect(lambda: self.open_file(path))
            open_with_action.triggered.connect(lambda: self.open_with(path))
            rename_action.triggered.connect(lambda: self.rename_item(index))
            delete_action.triggered.connect(lambda: self.delete_item(index))

        menu.exec_(self.list_view.mapToGlobal(position))

    def show_sidebar_context_menu(self, position):
        item = self.sidebar_widget.itemAt(position)
        if item:
            path = item.data(Qt.UserRole)
            menu = QMenu()

            if path in self.pinned_folders:
                unpin_action = menu.addAction("Unpin")
                unpin_action.triggered.connect(lambda: self.unpin_folder(path))

            menu.exec_(self.sidebar_widget.mapToGlobal(position))

    def unpin_folder(self, path):
        if path in self.pinned_folders:
            self.pinned_folders.remove(path)
            self.update_sidebar()
            self.save_pinned_folders()

    def open_with(self, path):
        program, ok = QInputDialog.getText(self, "Open With", "Enter the program to open the file:")
        if ok and program:
            try:
                subprocess.Popen([program, path])
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to open file: {e}")

    def pin_folder(self, path):
        if path not in self.pinned_folders:
            self.pinned_folders.append(path)
            self.update_sidebar()
            self.save_pinned_folders()

    def delete_item(self, index):
        path = self.model.filePath(index)
        reply = QMessageBox.question(
            self, "Delete", f"Are you sure you want to delete {path}?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            try:
                if os.path.isdir(path):
                    os.rmdir(path)
                else:
                    os.remove(path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete: {e}")

    def rename_item(self, index):
        old_path = self.model.filePath(index)
        new_name, ok = QInputDialog.getText(
            self, "Rename", "Enter new name:", text=os.path.basename(old_path)
        )
        if ok and new_name:
            new_path = os.path.join(os.path.dirname(old_path), new_name)
            try:
                os.rename(old_path, new_path)
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to rename: {e}")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                item = self.sidebar_widget.itemAt(event.pos())
                if item:
                    destination = item.data(Qt.UserRole)
                    if os.path.isdir(destination):
                        try:
                            os.rename(file_path, os.path.join(destination, os.path.basename(file_path)))
                        except Exception as e:
                            QMessageBox.critical(self, "Error", f"Failed to move file: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    file_manager = FileManager()
    file_manager.show()
    sys.exit(app.exec_())
