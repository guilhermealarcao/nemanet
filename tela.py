#!/usr/bin/python3
# -*- coding: utf-8 -*-
import glob, os
import object_detection_api as tf
from libs.functions import * 
from libs.utils import *
from libs.constants import *
from libs.settings import Settings
from libs.ustr import ustr
# from PyQt5.QtCore import Qt,pyqtSlot, QSize
# from PyQt5.QtGui import QImage, QPixmap, QPalette, QPainter , QIcon , QImageReader
from PyQt5.QtPrintSupport import QPrintDialog, QPrinter
# from PyQt5.QtWidgets import QListWidget,QLabel,QToolBar , QSizePolicy, QScrollArea, QMessageBox, QMainWindow, QMenu, QAction, \
#     qApp, QFileDialog, QTableWidget, QTableWidgetItem, QVBoxLayout, QPushButton, QDockWidget, QWidget
from PyQt5.QtGui import *
from PyQt5.QtCore import *
from PyQt5.QtWidgets import *
import json

import xlwt
# Add internal libs
from libs.settings import Settings
from libs.pascal_voc_io import PascalVocReader
from libs.pascal_voc_io import XML_EXT
from libs.ustr import ustr

class CloneThread(QThread):
    signal = pyqtSignal('PyQt_PyObject')

    def __init__(self):
        QThread.__init__(self)
        self.git_url = []
        self.git_status = ""
        self.add=""
        self.tabela=""
        self.save=""
        self.alerta=""

    # run method gets called when we start the thread
    def run(self):
        self.git_status("Analisado 0 /"+str(len(self.git_url)))
        i = 0
        total = 0
        vivo = 0
        paralisado = 0
        for index in range(0,len(self.git_url) , 2):
            self.tabela.setRowCount(self.tabela.rowCount()+1)
            json = tf.get_teste(self.git_url[index],self.git_url[index+1], 0.98)
            print(json)
            self.add(i,0 , json.path)
            self.add(i,1 , str(json.gabarito['total']))
            self.add(i,2 , str(json.gabarito['vivo']))
            self.add(i,3 , str(json.gabarito['paralisado']))
            total = total + int(json.gabarito['total'])
            vivo  = vivo + int(json.gabarito['vivo'])
            paralisado = paralisado + int(json.gabarito['paralisado'])
            i = i + 1
            self.git_status("Analisado "+str(i)+" /"+str(len(self.git_url[index])))
        self.tabela.setRowCount(self.tabela.rowCount()+1)
        self.add(i,0 , "TOTAL")
        self.add(i,1 , str(total))
        self.add(i,2 , str(vivo))
        self.add(i,3 , str(paralisado))
        self.tabela.setRowCount(self.tabela.rowCount()+1)
        # self.alerta("Analise finalizada, os resultados foram salvos.")
        self.save()
         

class QImageViewer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.git_thread = CloneThread()  # This is the thread object
        # Connect the signal from the thread to the finished method
        # self.git_thread.signal.connect(self.finished)
     
        self.defaultSaveDir = None
        self.usingPascalVocFormat = True
        self.mImgList = []
        self.dirname = None
        self.labelHist = []
        self.lastOpenDir = None
        self.itemsToShapes = {}
        self.shapesToItems = {}
        self.prevLabelText = ''

        # Application state.
        
        self.filePath = None
        self.recentFiles = []
    

        self.mImgList = []
        self.dirname = None
        self.labelHist = []
        self.lastOpenDir = None

        self.tableWidget = QTableWidget(0,4)
        self.tableWidget.setHorizontalHeaderLabels(['Imagem', 'Encontrados', 'Movimentando', 'Paralisados'])
        self.tableWidget.horizontalHeader().setStretchLastSection(True) 
        self.tableWidget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        # lista de arquivos
        self.fileListWidget = QListWidget()
        self.fileListWidget.itemDoubleClicked.connect(self.fileitemDoubleClicked)
        filelistLayout = QVBoxLayout()
        filelistLayout.setContentsMargins(0, 0, 0, 0)
        filelistLayout.addWidget(self.fileListWidget)
        fileListContainer = QWidget()
        fileListContainer.setLayout(filelistLayout)
        self.filedock = QDockWidget('Lista de imagens', self)
        self.filedock.setObjectName('files')
        self.filedock.setWidget(fileListContainer)
        

        listLayout = QVBoxLayout()
        listLayout.setContentsMargins(0, 0, 0, 0)
        

        self.labelList = QListWidget()
        listLayout.addWidget(self.labelList)
    

        self.createActions()
        self.createMenus()

        
        self.setCentralWidget(self.tableWidget)
        self.addDockWidget(Qt.RightDockWidgetArea, self.filedock)
        

        
        self.statusBar().showMessage('Todos os modulos foram carregados com sucesso.')
        self.statusBar().show()


        self.setWindowTitle("NematoNET")
        self.resize(1200, 800)   

    
    def savefile(self):
        # filename,_ = QFileDialog.getSaveFileName(self, 'Save File', '', ".xls(*.xls)")
        print(self.lastOpenDir)
        filename = self.lastOpenDir + "/resultado.xls"
        wbk = xlwt.Workbook()
        sheet = wbk.add_sheet("sheet", cell_overwrite_ok=True)
        style = xlwt.XFStyle()
        font = xlwt.Font()
        font.bold = True
        style.font = font
        model = self.tableWidget.model()
        sheet.write(0, 0, "Imagem")
        sheet.write(0, 1, "Contados")
        sheet.write(0, 2, "Movimentando")
        sheet.write(0, 3, "Paralisado")
        for r in range(model.rowCount()):
            text = model.data(model.index(r, 0))
            sheet.write(r, 0, text)
            text = model.data(model.index(r, 1))
            sheet.write(r, 1, text)
            text = model.data(model.index(r, 2))
            sheet.write(r, 2, text)
            text = model.data(model.index(r, 3))
            sheet.write(r, 3, text)
        wbk.save(filename)
        self.status("Resultado foi salvo na pasta.")

    def scanAllImages(self, folderPath):
        extensions = ['.%s' % fmt.data().decode("ascii").lower() for fmt in QImageReader.supportedImageFormats()]
        images = []
        for file in os.listdir(folderPath):
            if file.lower().endswith(tuple(extensions)):
                relativePath = file
                relativePath = os.path.join(folderPath, file)
                path = ustr(os.path.abspath(relativePath))
                images.append(path)

        natural_sort(images, key=lambda x: x.lower())
        return images 
        
    def status(self, message, delay=5000):
        self.statusBar().showMessage(message, delay)


    def addRow(self, linha , coluna , texto):
        self.tableWidget.setItem(linha,coluna,QTableWidgetItem(texto))

    def analisar(self):    
        self.git_thread.git_url = self.mImgList
        self.git_thread.git_status = self.status
        self.git_thread.add = self.addRow
        self.git_thread.tabela = self.tableWidget
        self.git_thread.save = self.savefile
        self.git_thread.alerta = self.alerta
        self.git_thread.start()  # Finally starts the thread


    def fileitemDoubleClicked(self, item=None):
        currIndex = self.mImgList.index(ustr(item.text()))
        if currIndex < len(self.mImgList):
            filename = self.mImgList[currIndex]
            if filename:
                print("s")

    def importDirImages(self, dirpath):
        self.lastOpenDir = dirpath
        self.dirname = dirpath
        self.filePath = None
        self.fileListWidget.clear()
        self.mImgList = self.scanAllImages(dirpath)
        if len(self.mImgList) % 2 != 0:
            self.alerta("Por favor, quantidade de imagens está errada.")
        else:
            for imgPath in self.mImgList:
                item = QListWidgetItem(imgPath)
                self.fileListWidget.addItem(item)

    def openDir(self):
        options = QFileDialog.Options()
        my_dir = QFileDialog.getExistingDirectory(self, "Abrir pasta", '', QFileDialog.ShowDirsOnly )
        if my_dir:
            for x in range(0,self.tableWidget.rowCount()):
                self.tableWidget.removeRow(x)
            self.updateActions()
            self.importDirImages(my_dir)

            
    def createActions(self):
        self.openDirAct = QAction("&Abrir pasta", self, shortcut="Ctrl+t", triggered=self.openDir)
        self.openDirToolAct = QAction(QIcon("/Users/guilhermealarcao/tfObjWebrtc/resources/icons/open.png"), "&Abrir Pasta", self, shortcut="Ctrl+t", triggered=self.openDir)
        self.analisarAct = QAction(QIcon("/Users/guilhermealarcao/tfObjWebrtc/resources/icons/database.png") , "Analisar", self, enabled=False, triggered=self.analisar)

        
    def updateActions(self):
        self.analisarAct.setEnabled(True)
        

    def createMenus(self):
        self.fileMenu = QMenu("&Arquivo", self)        
        self.fileMenu.addAction(self.openDirAct)
        self.fileMenu.addSeparator()
        self.menuBar().addMenu(self.fileMenu)
        self.toolbar = QToolBar( "My main toolbar")
        self.toolbar.addAction(self.openDirToolAct)
        self.toolbar.addSeparator()
        self.toolbar.addAction(self.analisarAct)
        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)
        self.addToolBar(Qt.LeftToolBarArea, self.toolbar)

    def alerta(self, texto):
        QMessageBox.about(self, "Alerta", texto)

    def currentItem(self):
        items = self.labelList.selectedItems()
        if items:
            return items[0]
        return None
    
    

if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    imageViewer = QImageViewer()
    imageViewer.show()
    sys.exit(app.exec_())
    # TODO QScrollArea support mouse