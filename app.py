import os
import re
import threading
from typing import Optional

import cv2
from PyQt5.QtWidgets import (QFileDialog, QGridLayout, QMessageBox,
                             QPushButton, QWidget)

from analyzer import Analyzer, Object


class App(QWidget):
    def __init__(self) -> None:
        super().__init__()

        self.source_path: Optional[str] = None
        self.cropped_directory: Optional[str] = None
        self.objects: Optional[list[Object]] = None

        self.__init_UI()

    def __init_UI(self) -> None:
        self.main_layout = QGridLayout(self)

        crop_button = QPushButton('Crop')
        crop_button.clicked.connect(self.__crop)
        self.main_layout.addWidget(crop_button, 0, 0)

        analyze_button = QPushButton('Analyze')
        analyze_button.clicked.connect(self.__analyze)
        self.main_layout.addWidget(analyze_button, 1, 0)

        visualize_button = QPushButton('Visualize')
        visualize_button.clicked.connect(self.__visualize)
        self.main_layout.addWidget(visualize_button, 2, 0)

        self.setWindowTitle('Space Data Analyzer')
        self.show()

    def __crop(self) -> None:
        self.source_path = QFileDialog.getOpenFileName(
            self, caption='Select source image', directory='.', filter='Image files (*.jpg *.png)')[0]
        if not self.source_path:
            err = QMessageBox(QMessageBox.Icon.Warning,
                              'Error', 'Select source image')
            err.exec_()
            return

        self.cropped_directory = QFileDialog.getExistingDirectory(
            self, caption='Select output directory', directory='.')
        if not self.cropped_directory:
            err = QMessageBox(QMessageBox.Icon.Warning,
                              'Error', 'Select output directory')
            err.exec_()
            return

        Analyzer.crop(self.source_path, self.cropped_directory, (100, 100))

    def __analyze(self) -> None:
        if not self.cropped_directory:
            self.cropped_directory = QFileDialog.getExistingDirectory(
                self, caption='Select cropped images directory', directory='.')
            if not self.cropped_directory:
                err = QMessageBox(QMessageBox.Icon.Warning,
                                  'Error', 'Select cropped images directory')
                err.exec_()
                return

        self.objects = []

        threads: list[threading.Thread] = []
        for img_name in os.listdir(self.cropped_directory):
            thread = threading.Thread(
                target=self.__worker, args=(img_name,))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        with open('statistic.txt', 'w') as file:
            for stat in self.objects:
                file.write(f'{stat}\n')

    def __worker(self, img_name: str) -> None:
        if not self.cropped_directory or self.objects is None:
            return

        if (match := re.findall(r'img(\d+)x(\d+)\.png', img_name)) and len(match) == 1 and len(match[0]) == 2:
            x, y = int(match[0][0]), int(match[0][1])

            img_path = os.path.join(self.cropped_directory, img_name)
            img = cv2.imread(img_path)
            self.objects.extend(Analyzer.analyze(img, (x, y), 50))

    def __visualize(self) -> None:
        if not self.objects:
            err = QMessageBox(QMessageBox.Icon.Warning,
                    'Error', 'Analyze data first')
            err.exec_()
            return

        if not self.source_path:
            self.source_path = QFileDialog.getOpenFileName(
            self, caption='Select source image', directory='.', filter='Image files (*.jpg *.png)')[0]
            if not self.source_path:
                err = QMessageBox(QMessageBox.Icon.Warning,
                                'Error', 'Select source image')
                err.exec_()
                return
            

        img = cv2.imread(self.source_path)
        result = Analyzer.draw_overlay(img, self.objects, 20)
        cv2.imwrite('result.png', result)
