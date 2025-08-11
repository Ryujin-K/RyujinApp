# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main.ui'
##
## Created by: Qt User Interface Compiler version 6.6.3
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDoubleSpinBox,
    QFrame, QGroupBox, QHBoxLayout, QLabel,
    QLineEdit, QMainWindow, QProgressBar, QPushButton,
    QScrollArea, QSizePolicy, QSpacerItem, QSpinBox,
    QStackedWidget, QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(828, 548)
        icon = QIcon()
        icon.addFile(u"icon.ico", QSize(), QIcon.Normal, QIcon.Off)
        MainWindow.setWindowIcon(icon)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.horizontalLayout_4 = QHBoxLayout(self.centralwidget)
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.pages = QStackedWidget(self.centralwidget)
        self.pages.setObjectName(u"pages")
        self.app = QWidget()
        self.app.setObjectName(u"app")
        self.verticalLayout_5 = QVBoxLayout(self.app)
        self.verticalLayout_5.setObjectName(u"verticalLayout_5")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.websites = QPushButton(self.app)
        self.websites.setObjectName(u"websites")

        self.horizontalLayout.addWidget(self.websites)

        self.link = QPushButton(self.app)
        self.link.setObjectName(u"link")

        self.horizontalLayout.addWidget(self.link)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.downloadAll = QPushButton(self.app)
        self.downloadAll.setObjectName(u"downloadAll")

        self.verticalLayout.addWidget(self.downloadAll)


        self.verticalLayout_5.addLayout(self.verticalLayout)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout_2.setContentsMargins(-1, -1, -1, 0)
        self.search = QLineEdit(self.app)
        self.search.setObjectName(u"search")
        self.search.setAutoFillBackground(False)

        self.horizontalLayout_2.addWidget(self.search)

        self.invert = QPushButton(self.app)
        self.invert.setObjectName(u"invert")

        self.horizontalLayout_2.addWidget(self.invert)


        self.verticalLayout_5.addLayout(self.horizontalLayout_2)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.horizontalLayout_6.setContentsMargins(-1, -1, 0, 0)
        self.scrollArea = QScrollArea(self.app)
        self.scrollArea.setObjectName(u"scrollArea")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.scrollArea.sizePolicy().hasHeightForWidth())
        self.scrollArea.setSizePolicy(sizePolicy)
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 394, 350))
        self.verticalLayout_4 = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.verticalChapter = QVBoxLayout()
        self.verticalChapter.setObjectName(u"verticalChapter")

        self.verticalLayout_4.addLayout(self.verticalChapter)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.horizontalLayout_6.addWidget(self.scrollArea)

        self.progress_scroll = QScrollArea(self.app)
        self.progress_scroll.setObjectName(u"progress_scroll")
        self.progress_scroll.setWidgetResizable(True)
        self.scrollAreaWidgetContents_3 = QWidget()
        self.scrollAreaWidgetContents_3.setObjectName(u"scrollAreaWidgetContents_3")
        self.scrollAreaWidgetContents_3.setGeometry(QRect(0, 0, 394, 350))
        self.verticalLayout_3 = QVBoxLayout(self.scrollAreaWidgetContents_3)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.verticalProgress = QVBoxLayout()
        self.verticalProgress.setObjectName(u"verticalProgress")

        self.verticalLayout_3.addLayout(self.verticalProgress)

        self.progress_scroll.setWidget(self.scrollAreaWidgetContents_3)

        self.horizontalLayout_6.addWidget(self.progress_scroll)


        self.verticalLayout_5.addLayout(self.horizontalLayout_6)

        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.horizontalLayout_3.setContentsMargins(-1, -1, -1, 0)
        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_3.addItem(self.horizontalSpacer)

        self.logs = QPushButton(self.app)
        self.logs.setObjectName(u"logs")

        self.horizontalLayout_3.addWidget(self.logs)

        self.progress = QPushButton(self.app)
        self.progress.setObjectName(u"progress")

        self.horizontalLayout_3.addWidget(self.progress)

        self.config = QPushButton(self.app)
        self.config.setObjectName(u"config")

        self.horizontalLayout_3.addWidget(self.config)


        self.verticalLayout_5.addLayout(self.horizontalLayout_3)

        self.pages.addWidget(self.app)
        self.loading = QWidget()
        self.loading.setObjectName(u"loading")
        self.horizontalLayout_5 = QHBoxLayout(self.loading)
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_2)

        self.verticalLayout_21 = QVBoxLayout()
        self.verticalLayout_21.setObjectName(u"verticalLayout_21")
        self.verticalLayout_21.setContentsMargins(-1, -1, 0, -1)
        self.verticalSpacer_3 = QSpacerItem(20, 40, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.verticalLayout_21.addItem(self.verticalSpacer_3)

        self.horizontalLayout_13 = QHBoxLayout()
        self.horizontalLayout_13.setObjectName(u"horizontalLayout_13")
        self.horizontalLayout_13.setContentsMargins(-1, 20, -1, -1)
        self.horizontalSpacer_5 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_13.addItem(self.horizontalSpacer_5)

        self.label = QLabel(self.loading)
        self.label.setObjectName(u"label")
        font = QFont()
        font.setPointSize(20)
        self.label.setFont(font)

        self.horizontalLayout_13.addWidget(self.label)

        self.horizontalSpacer_6 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_13.addItem(self.horizontalSpacer_6)


        self.verticalLayout_21.addLayout(self.horizontalLayout_13)

        self.progressBar = QProgressBar(self.loading)
        self.progressBar.setObjectName(u"progressBar")
        self.progressBar.setMaximum(0)
        self.progressBar.setValue(0)
        self.progressBar.setTextVisible(False)

        self.verticalLayout_21.addWidget(self.progressBar)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.verticalLayout_21.addItem(self.verticalSpacer_2)


        self.horizontalLayout_5.addLayout(self.verticalLayout_21)

        self.horizontalSpacer_3 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_5.addItem(self.horizontalSpacer_3)

        self.pages.addWidget(self.loading)
        self.page = QWidget()
        self.page.setObjectName(u"page")
        self.verticalLayout_6 = QVBoxLayout(self.page)
        self.verticalLayout_6.setObjectName(u"verticalLayout_6")
        self.horizontalLayout_7 = QHBoxLayout()
        self.horizontalLayout_7.setObjectName(u"horizontalLayout_7")
        self.config_back = QPushButton(self.page)
        self.config_back.setObjectName(u"config_back")

        self.horizontalLayout_7.addWidget(self.config_back)

        self.horizontalSpacer_4 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.horizontalLayout_7.addItem(self.horizontalSpacer_4)


        self.verticalLayout_6.addLayout(self.horizontalLayout_7)

        self.line_2 = QFrame(self.page)
        self.line_2.setObjectName(u"line_2")
        self.line_2.setFrameShape(QFrame.VLine)
        self.line_2.setFrameShadow(QFrame.Sunken)

        self.verticalLayout_6.addWidget(self.line_2)

        self.scrollArea_2 = QScrollArea(self.page)
        self.scrollArea_2.setObjectName(u"scrollArea_2")
        self.scrollArea_2.setWidgetResizable(True)
        self.scrollAreaWidgetContents_2 = QWidget()
        self.scrollAreaWidgetContents_2.setObjectName(u"scrollAreaWidgetContents_2")
        self.scrollAreaWidgetContents_2.setGeometry(QRect(0, -479, 779, 994))
        self.verticalLayout_7 = QVBoxLayout(self.scrollAreaWidgetContents_2)
        self.verticalLayout_7.setObjectName(u"verticalLayout_7")
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(-1, 0, -1, -1)
        self.language_label = QLabel(self.scrollAreaWidgetContents_2)
        self.language_label.setObjectName(u"language_label")

        self.verticalLayout_2.addWidget(self.language_label)

        self.langs = QComboBox(self.scrollAreaWidgetContents_2)
        self.langs.addItem("")
        self.langs.addItem("")
        self.langs.addItem("")
        self.langs.addItem("")
        self.langs.addItem("")
        self.langs.addItem("")
        self.langs.addItem("")
        self.langs.addItem("")
        self.langs.addItem("")
        self.langs.addItem("")
        self.langs.setObjectName(u"langs")

        self.verticalLayout_2.addWidget(self.langs)

        self.horizontalLayout_9 = QHBoxLayout()
        self.horizontalLayout_9.setObjectName(u"horizontalLayout_9")
        self.horizontalLayout_9.setContentsMargins(-1, 0, -1, -1)
        self.verticalLayout_8 = QVBoxLayout()
        self.verticalLayout_8.setObjectName(u"verticalLayout_8")
        self.verticalLayout_8.setContentsMargins(-1, 0, -1, -1)
        self.img_format = QLabel(self.scrollAreaWidgetContents_2)
        self.img_format.setObjectName(u"img_format")

        self.verticalLayout_8.addWidget(self.img_format)

        self.format_img = QComboBox(self.scrollAreaWidgetContents_2)
        self.format_img.addItem("")
        self.format_img.addItem("")
        self.format_img.addItem("")
        self.format_img.addItem("")
        self.format_img.setObjectName(u"format_img")

        self.verticalLayout_8.addWidget(self.format_img)


        self.horizontalLayout_9.addLayout(self.verticalLayout_8)

        self.verticalLayout_9 = QVBoxLayout()
        self.verticalLayout_9.setObjectName(u"verticalLayout_9")
        self.simul_label = QLabel(self.scrollAreaWidgetContents_2)
        self.simul_label.setObjectName(u"simul_label")

        self.verticalLayout_9.addWidget(self.simul_label)

        self.simul_qtd = QSpinBox(self.scrollAreaWidgetContents_2)
        self.simul_qtd.setObjectName(u"simul_qtd")
        self.simul_qtd.setMinimum(1)
        self.simul_qtd.setMaximum(10)
        self.simul_qtd.setValue(3)

        self.verticalLayout_9.addWidget(self.simul_qtd)


        self.horizontalLayout_9.addLayout(self.verticalLayout_9)


        self.verticalLayout_2.addLayout(self.horizontalLayout_9)

        self.path_label = QLabel(self.scrollAreaWidgetContents_2)
        self.path_label.setObjectName(u"path_label")

        self.verticalLayout_2.addWidget(self.path_label)

        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.horizontalLayout_8.setContentsMargins(-1, 0, -1, -1)
        self.open_folder = QPushButton(self.scrollAreaWidgetContents_2)
        self.open_folder.setObjectName(u"open_folder")

        self.horizontalLayout_8.addWidget(self.open_folder)

        self.path = QLineEdit(self.scrollAreaWidgetContents_2)
        self.path.setObjectName(u"path")
        self.path.setEnabled(False)

        self.horizontalLayout_8.addWidget(self.path)

        self.setSaveFolder = QPushButton(self.scrollAreaWidgetContents_2)
        self.setSaveFolder.setObjectName(u"setSaveFolder")
        self.setSaveFolder.setMinimumSize(QSize(0, 0))
        self.setSaveFolder.setMaximumSize(QSize(30, 16777215))

        self.horizontalLayout_8.addWidget(self.setSaveFolder)


        self.verticalLayout_2.addLayout(self.horizontalLayout_8)

        self.verticalLayout_17 = QVBoxLayout()
        self.verticalLayout_17.setObjectName(u"verticalLayout_17")
        self.verticalLayout_17.setContentsMargins(-1, 20, -1, -1)

        self.verticalLayout_2.addLayout(self.verticalLayout_17)

        self.group_imgs = QGroupBox(self.scrollAreaWidgetContents_2)
        self.group_imgs.setObjectName(u"group_imgs")
        self.group_imgs.setFlat(True)
        self.group_imgs.setCheckable(True)
        self.group_imgs.setChecked(False)
        self.verticalLayout_18 = QVBoxLayout(self.group_imgs)
        self.verticalLayout_18.setObjectName(u"verticalLayout_18")
        self.group_imgs_combo = QComboBox(self.group_imgs)
        self.group_imgs_combo.addItem("")
        self.group_imgs_combo.addItem("")
        self.group_imgs_combo.setObjectName(u"group_imgs_combo")

        self.verticalLayout_18.addWidget(self.group_imgs_combo)

        self.replacegroupcheckBox = QCheckBox(self.group_imgs)
        self.replacegroupcheckBox.setObjectName(u"replacegroupcheckBox")

        self.verticalLayout_18.addWidget(self.replacegroupcheckBox)


        self.verticalLayout_2.addWidget(self.group_imgs)

        self.verticalLayout_16 = QVBoxLayout()
        self.verticalLayout_16.setObjectName(u"verticalLayout_16")
        self.verticalLayout_16.setContentsMargins(-1, 20, -1, -1)

        self.verticalLayout_2.addLayout(self.verticalLayout_16)

        self.slicer_box = QGroupBox(self.scrollAreaWidgetContents_2)
        self.slicer_box.setObjectName(u"slicer_box")
        self.slicer_box.setMinimumSize(QSize(0, 0))
        self.slicer_box.setFlat(True)
        self.slicer_box.setCheckable(True)
        self.slicer_box.setChecked(False)
        self.verticalLayout_11 = QVBoxLayout(self.slicer_box)
        self.verticalLayout_11.setObjectName(u"verticalLayout_11")
        self.slicer_height_label = QLabel(self.slicer_box)
        self.slicer_height_label.setObjectName(u"slicer_height_label")

        self.verticalLayout_11.addWidget(self.slicer_height_label)

        self.slicer_height = QDoubleSpinBox(self.slicer_box)
        self.slicer_height.setObjectName(u"slicer_height")
        self.slicer_height.setDecimals(0)
        self.slicer_height.setMaximum(999999999.000000000000000)

        self.verticalLayout_11.addWidget(self.slicer_height)

        self.horizontalLayout_10 = QHBoxLayout()
        self.horizontalLayout_10.setObjectName(u"horizontalLayout_10")
        self.horizontalLayout_10.setContentsMargins(-1, 0, -1, -1)
        self.verticalLayout_10 = QVBoxLayout()
        self.verticalLayout_10.setObjectName(u"verticalLayout_10")
        self.verticalLayout_10.setContentsMargins(-1, 0, -1, -1)
        self.slicer_width_label = QLabel(self.slicer_box)
        self.slicer_width_label.setObjectName(u"slicer_width_label")

        self.verticalLayout_10.addWidget(self.slicer_width_label)

        self.slicer_width_select = QComboBox(self.slicer_box)
        self.slicer_width_select.addItem("")
        self.slicer_width_select.addItem("")
        self.slicer_width_select.addItem("")
        self.slicer_width_select.setObjectName(u"slicer_width_select")

        self.verticalLayout_10.addWidget(self.slicer_width_select)


        self.horizontalLayout_10.addLayout(self.verticalLayout_10)

        self.verticalLayout_12 = QVBoxLayout()
        self.verticalLayout_12.setObjectName(u"verticalLayout_12")
        self.verticalLayout_12.setContentsMargins(-1, 0, -1, -1)
        self.slicer_width_spin_label = QLabel(self.slicer_box)
        self.slicer_width_spin_label.setObjectName(u"slicer_width_spin_label")

        self.verticalLayout_12.addWidget(self.slicer_width_spin_label)

        self.slicer_width_spin = QDoubleSpinBox(self.slicer_box)
        self.slicer_width_spin.setObjectName(u"slicer_width_spin")
        self.slicer_width_spin.setDecimals(0)
        self.slicer_width_spin.setMaximum(999999999.000000000000000)

        self.verticalLayout_12.addWidget(self.slicer_width_spin)


        self.horizontalLayout_10.addLayout(self.verticalLayout_12)


        self.verticalLayout_11.addLayout(self.horizontalLayout_10)

        self.slicer_detector_label = QLabel(self.slicer_box)
        self.slicer_detector_label.setObjectName(u"slicer_detector_label")

        self.verticalLayout_11.addWidget(self.slicer_detector_label)

        self.slicer_detector_select = QComboBox(self.slicer_box)
        self.slicer_detector_select.addItem("")
        self.slicer_detector_select.addItem("")
        self.slicer_detector_select.setObjectName(u"slicer_detector_select")

        self.verticalLayout_11.addWidget(self.slicer_detector_select)

        self.horizontalLayout_12 = QHBoxLayout()
        self.horizontalLayout_12.setObjectName(u"horizontalLayout_12")
        self.horizontalLayout_12.setContentsMargins(-1, 0, -1, -1)
        self.verticalLayout_19 = QVBoxLayout()
        self.verticalLayout_19.setObjectName(u"verticalLayout_19")
        self.verticalLayout_19.setContentsMargins(-1, 0, -1, -1)
        self.slicer_detection_sensivity_label = QLabel(self.slicer_box)
        self.slicer_detection_sensivity_label.setObjectName(u"slicer_detection_sensivity_label")

        self.verticalLayout_19.addWidget(self.slicer_detection_sensivity_label)

        self.slicer_detection_sensivity = QSpinBox(self.slicer_box)
        self.slicer_detection_sensivity.setObjectName(u"slicer_detection_sensivity")
        self.slicer_detection_sensivity.setMinimum(1)
        self.slicer_detection_sensivity.setMaximum(100)

        self.verticalLayout_19.addWidget(self.slicer_detection_sensivity)


        self.horizontalLayout_12.addLayout(self.verticalLayout_19)

        self.verticalLayout_20 = QVBoxLayout()
        self.verticalLayout_20.setObjectName(u"verticalLayout_20")
        self.slicer_scan_line_label = QLabel(self.slicer_box)
        self.slicer_scan_line_label.setObjectName(u"slicer_scan_line_label")

        self.verticalLayout_20.addWidget(self.slicer_scan_line_label)

        self.slicer_scan_line = QSpinBox(self.slicer_box)
        self.slicer_scan_line.setObjectName(u"slicer_scan_line")
        self.slicer_scan_line.setMinimum(1)
        self.slicer_scan_line.setMaximum(25)

        self.verticalLayout_20.addWidget(self.slicer_scan_line)


        self.horizontalLayout_12.addLayout(self.verticalLayout_20)


        self.verticalLayout_11.addLayout(self.horizontalLayout_12)

        self.slicer_ignorable_margin_label = QLabel(self.slicer_box)
        self.slicer_ignorable_margin_label.setObjectName(u"slicer_ignorable_margin_label")

        self.verticalLayout_11.addWidget(self.slicer_ignorable_margin_label)

        self.slicer_ignorable_margin = QSpinBox(self.slicer_box)
        self.slicer_ignorable_margin.setObjectName(u"slicer_ignorable_margin")
        self.slicer_ignorable_margin.setMaximum(999999)

        self.verticalLayout_11.addWidget(self.slicer_ignorable_margin)

        self.replaceslicecheckBox = QCheckBox(self.slicer_box)
        self.replaceslicecheckBox.setObjectName(u"replaceslicecheckBox")

        self.verticalLayout_11.addWidget(self.replaceslicecheckBox)


        self.verticalLayout_2.addWidget(self.slicer_box)

        self.verticalLayout_14 = QVBoxLayout()
        self.verticalLayout_14.setObjectName(u"verticalLayout_14")
        self.verticalLayout_14.setContentsMargins(-1, 20, -1, -1)

        self.verticalLayout_2.addLayout(self.verticalLayout_14)

        self.external = QGroupBox(self.scrollAreaWidgetContents_2)
        self.external.setObjectName(u"external")
        self.external.setFlat(True)
        self.external.setCheckable(True)
        self.external.setChecked(False)
        self.verticalLayout_13 = QVBoxLayout(self.external)
        self.verticalLayout_13.setObjectName(u"verticalLayout_13")
        self.horizontalLayout_11 = QHBoxLayout()
        self.horizontalLayout_11.setObjectName(u"horizontalLayout_11")
        self.horizontalLayout_11.setContentsMargins(-1, 0, -1, -1)
        self.open_external_folder = QPushButton(self.external)
        self.open_external_folder.setObjectName(u"open_external_folder")

        self.horizontalLayout_11.addWidget(self.open_external_folder)

        self.selected_external = QLineEdit(self.external)
        self.selected_external.setObjectName(u"selected_external")
        self.selected_external.setEnabled(False)
        self.selected_external.setReadOnly(False)

        self.horizontalLayout_11.addWidget(self.selected_external)

        self.select_external = QPushButton(self.external)
        self.select_external.setObjectName(u"select_external")
        self.select_external.setMaximumSize(QSize(30, 16777215))

        self.horizontalLayout_11.addWidget(self.select_external)


        self.verticalLayout_13.addLayout(self.horizontalLayout_11)


        self.verticalLayout_2.addWidget(self.external)

        self.verticalLayout_15 = QVBoxLayout()
        self.verticalLayout_15.setObjectName(u"verticalLayout_15")
        self.verticalLayout_15.setContentsMargins(-1, 20, -1, -1)

        self.verticalLayout_2.addLayout(self.verticalLayout_15)

        self.dev_label = QLabel(self.scrollAreaWidgetContents_2)
        self.dev_label.setObjectName(u"dev_label")

        self.verticalLayout_2.addWidget(self.dev_label)

        self.dev_check = QCheckBox(self.scrollAreaWidgetContents_2)
        self.dev_check.setObjectName(u"dev_check")

        self.verticalLayout_2.addWidget(self.dev_check)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.verticalLayout_2.addItem(self.verticalSpacer)


        self.verticalLayout_7.addLayout(self.verticalLayout_2)

        self.scrollArea_2.setWidget(self.scrollAreaWidgetContents_2)

        self.verticalLayout_6.addWidget(self.scrollArea_2)

        self.pages.addWidget(self.page)

        self.horizontalLayout_4.addWidget(self.pages)

        MainWindow.setCentralWidget(self.centralwidget)

        self.retranslateUi(MainWindow)

        self.pages.setCurrentIndex(0)
        self.langs.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"RyujinApp", None))
        self.websites.setText(QCoreApplication.translate("MainWindow", u"Sites", None))
        self.link.setText(QCoreApplication.translate("MainWindow", u"Colar link", None))
        self.downloadAll.setText(QCoreApplication.translate("MainWindow", u"Baixar tudo", None))
        self.search.setPlaceholderText(QCoreApplication.translate("MainWindow", u"Filtrar caps... ex: 23", None))
        self.invert.setText(QCoreApplication.translate("MainWindow", u"Inverter", None))
        self.logs.setText(QCoreApplication.translate("MainWindow", u"Logs", None))
        self.progress.setText(QCoreApplication.translate("MainWindow", u"Progresso", None))
        self.config.setText(QCoreApplication.translate("MainWindow", u"Configurar", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"Buscando obra...", None))
        self.config_back.setText(QCoreApplication.translate("MainWindow", u"Voltar", None))
        self.language_label.setText(QCoreApplication.translate("MainWindow", u"Selecione a lingua:", None))
        self.langs.setItemText(0, QCoreApplication.translate("MainWindow", u"en", None))
        self.langs.setItemText(1, QCoreApplication.translate("MainWindow", u"pt_BR", None))
        self.langs.setItemText(2, QCoreApplication.translate("MainWindow", u"es", None))
        self.langs.setItemText(3, QCoreApplication.translate("MainWindow", u"fr", None))
        self.langs.setItemText(4, QCoreApplication.translate("MainWindow", u"de", None))
        self.langs.setItemText(5, QCoreApplication.translate("MainWindow", u"it", None))
        self.langs.setItemText(6, QCoreApplication.translate("MainWindow", u"ja", None))
        self.langs.setItemText(7, QCoreApplication.translate("MainWindow", u"zh_CN", None))
        self.langs.setItemText(8, QCoreApplication.translate("MainWindow", u"ru", None))
        self.langs.setItemText(9, QCoreApplication.translate("MainWindow", u"ar", None))

        self.langs.setCurrentText(QCoreApplication.translate("MainWindow", u"en", None))
        self.img_format.setText(QCoreApplication.translate("MainWindow", u"Selecione o formato da imagem:", None))
        self.format_img.setItemText(0, QCoreApplication.translate("MainWindow", u".jpg", None))
        self.format_img.setItemText(1, QCoreApplication.translate("MainWindow", u".png", None))
        self.format_img.setItemText(2, QCoreApplication.translate("MainWindow", u".webp", None))
        self.format_img.setItemText(3, QCoreApplication.translate("MainWindow", u".avif", None))

        self.simul_label.setText(QCoreApplication.translate("MainWindow", u"Downloads simult\u00e2neos:", None))
        self.path_label.setText(QCoreApplication.translate("MainWindow", u"Defina o caminho dos arquivos:", None))
        self.open_folder.setText(QCoreApplication.translate("MainWindow", u"Abrir a pasta", None))
        self.setSaveFolder.setText(QCoreApplication.translate("MainWindow", u"...", None))
        self.group_imgs.setTitle(QCoreApplication.translate("MainWindow", u"Agrupar Imagens (PDF/ZIP):", None))
        self.group_imgs_combo.setItemText(0, QCoreApplication.translate("MainWindow", u".pdf", None))
        self.group_imgs_combo.setItemText(1, QCoreApplication.translate("MainWindow", u".zip", None))

        self.replacegroupcheckBox.setText(QCoreApplication.translate("MainWindow", u"Sobreescrever", None))
        self.slicer_box.setTitle(QCoreApplication.translate("MainWindow", u"Slicer", None))
        self.slicer_height_label.setText(QCoreApplication.translate("MainWindow", u"Rough Output Height:", None))
        self.slicer_width_label.setText(QCoreApplication.translate("MainWindow", u"Width Enforcement Type:", None))
        self.slicer_width_select.setItemText(0, QCoreApplication.translate("MainWindow", u"No Enforcement", None))
        self.slicer_width_select.setItemText(1, QCoreApplication.translate("MainWindow", u"Automatic Uniform Width", None))
        self.slicer_width_select.setItemText(2, QCoreApplication.translate("MainWindow", u"User Customized Width", None))

        self.slicer_width_spin_label.setText(QCoreApplication.translate("MainWindow", u"Manual Custom Width [in pixels]:", None))
        self.slicer_detector_label.setText(QCoreApplication.translate("MainWindow", u"Detector Type:", None))
        self.slicer_detector_select.setItemText(0, QCoreApplication.translate("MainWindow", u"Smart Pixel Comparison", None))
        self.slicer_detector_select.setItemText(1, QCoreApplication.translate("MainWindow", u"Direct Slicing", None))

        self.slicer_detection_sensivity_label.setText(QCoreApplication.translate("MainWindow", u"Object Detection Sensitivity [1-100%]", None))
        self.slicer_scan_line_label.setText(QCoreApplication.translate("MainWindow", u"Scan Line Step [1-25 in pixels]", None))
        self.slicer_ignorable_margin_label.setText(QCoreApplication.translate("MainWindow", u"Ignorable Horizontal Margins [in pixels]", None))
        self.replaceslicecheckBox.setText(QCoreApplication.translate("MainWindow", u"Sobreescrever", None))
        self.external.setTitle(QCoreApplication.translate("MainWindow", u"external providers", None))
        self.open_external_folder.setText(QCoreApplication.translate("MainWindow", u"PushButton", None))
        self.select_external.setText(QCoreApplication.translate("MainWindow", u"...", None))
        self.dev_label.setText(QCoreApplication.translate("MainWindow", u"Modo desenvolvedor:", None))
        self.dev_check.setText(QCoreApplication.translate("MainWindow", u"Ativar", None))
    # retranslateUi

