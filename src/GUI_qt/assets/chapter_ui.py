# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'chapter.ui'
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
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QPushButton,
    QSizePolicy, QWidget)

class Ui_chapter(object):
    def setupUi(self, chapter):
        if not chapter.objectName():
            chapter.setObjectName(u"chapter")
        chapter.resize(428, 49)
        self.horizontalLayout_2 = QHBoxLayout(chapter)
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.download = QPushButton(chapter)
        self.download.setObjectName(u"download")
        self.download.setMinimumSize(QSize(50, 0))
        self.download.setMaximumSize(QSize(70, 16777215))

        self.horizontalLayout.addWidget(self.download)

        self.numberLabel = QLabel(chapter)
        self.numberLabel.setObjectName(u"numberLabel")

        self.horizontalLayout.addWidget(self.numberLabel)


        self.horizontalLayout_2.addLayout(self.horizontalLayout)


        self.retranslateUi(chapter)

        QMetaObject.connectSlotsByName(chapter)
    # setupUi

    def retranslateUi(self, chapter):
        chapter.setWindowTitle(QCoreApplication.translate("chapter", u"Form", None))
        self.download.setText(QCoreApplication.translate("chapter", u"download", None))
        self.numberLabel.setText(QCoreApplication.translate("chapter", u"number", None))
    # retranslateUi

