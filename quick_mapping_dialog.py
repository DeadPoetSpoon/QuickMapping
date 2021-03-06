# -*- coding: utf-8 -*-
"""
/***************************************************************************
 QuickMappingDialog
                                 A QGIS plugin
 Quick Mapping
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                             -------------------
        begin                : 2020-09-07
        git sha              : $Format:%H$
        copyright            : (C) 2020 by DeadPoetSpoon
        email                : 1149097040@qq.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

import os
import csv

from qgis.PyQt import uic
from qgis.PyQt import QtWidgets
from qgis.PyQt.QtWidgets import QFileDialog
from qgis.core import *
from qgis.gui import *

# This loads your .ui file so that PyQt can populate your plugin
# with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'quick_mapping_dialog_base.ui'))


class QuickMappingDialog(QtWidgets.QDialog, FORM_CLASS):
    """Main Dialog"""

    def __init__(self, iface, parent=None):
        """Constructor."""
        super(QuickMappingDialog, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        self.iface = iface
        self.layer = None
        self.joinlayer = None
        self.layout = None
        # self.categorizedSRWidget = None
        # ============================================================
        # connet
        # loadmap
        self.pb_loadmap.clicked.connect(lambda:
            self.addLayer(self.cbb_search.currentText()))
        # join
        self.pb_join.clicked.connect(lambda:
            self.joinItems(QFileDialog.getOpenFileName(self,
                "Open Join Table",
                "/home",
                "table(*.csv *.xls *.xlsx)")[0]))
        # style
        self.rendererDlg = None
        self.pb_symbolize.clicked.connect(self.symbolize)
        # self.pb_single.clicked.connect(self.singleSymbol)
        # self.pb_graduated.clicked.connect(self.graduatedSymbol)
        # map opt
        self.pb_setCRS.clicked.connect(self.setCRS)
        # labeling map
        self.pb_labeling.clicked.connect(self.labeling)
        # ExportD
        self.pb_exportD.clicked.connect(lambda:
                self.exportD(QFileDialog.getSaveFileName(self,
                "Choose Save File Name",
                "/home",
                "(*)")[0]))
        # layout
        self.pb_createlayout.clicked.connect(self.printlayout)
        # =============================================================
        # load AreaCode
        self.dir = os.path.dirname(__file__)
        self.areaCode = []
        self.areaName = []
        with open(os.path.join(self.dir,
                               'static/ChinaAreaCode.csv'), 'r')as f:
            for row in csv.reader(f):
                self.areaCode.append(row[0])
                self.areaName.append(row[1])
        self.cbb_search.addItems(self.areaCode)
        self.cbb_search.addItems(self.areaName)
        # init QgsMessageBar
        self.msgBar = iface.messageBar()
    def getUrl(self, area: str):
        """Get GeoJson from https://geo.datav.aliyun.com/areas_v2/bound/
           Tool https://datav.aliyun.com/tools/atlas/"""
        # code?
        purl = 'https://geo.datav.aliyun.com/areas_v2/bound/'
        if area in self.areaCode:
            if area[4:6] == "00":
                if self.cb_include.isChecked():
                    dataurl = purl+area+'_full.json'
                else:
                    dataurl = purl+area+'.json'
            else:
                dataurl = purl+area+'.json'
        # name?
        elif area in self.areaName:
            area = self.areaCode[self.areaName.index(area)]
            if area[4:6] == "00":
                if self.cb_include.isChecked():
                    dataurl = purl+area+'_full.json'
                else:
                    dataurl = purl+area+'.json'
            else:
                dataurl = purl+area+'.json'
        else:
            dataurl = ""
        return dataurl
    # ====================================================================
    def joinItems(self, filePath: str):
        """set join layer items"""
        if self.layer is not None:
            self.joinlayer = self.iface.addVectorLayer(
                filePath, "joinlayer", "ogr")
            if self.joinlayer is not None:
                # Add joinfield combobox
                for i in range(self.cbb_joinfield.count()-1, -1, -1):
                    self.cbb_joinfield.removeItem(i)
                for col in self.joinlayer.fields():
                    self.cbb_joinfield.addItem(col.name())
                # set prefix
                self.le_pre.setText("joinlayer_")
                #Add targetfield combobx
                for i in range(self.cbb_targetfield.count()-1, -1, -1):
                    self.cbb_targetfield.removeItem(i)
                for col in self.layer.fields():
                    self.cbb_targetfield.addItem(col.name())
                # connect
                self.pb_joinattr.clicked.connect(self.join)
            else:
                self.showError("连接表打开失败！")
        else:
            self.showError("请先加载地图！")

    def join(self):
        """join layer"""
        joininfo = QgsVectorLayerJoinInfo()
        joininfo.setDynamicFormEnabled(self.cb_dynamic.isChecked())
        joininfo.setEditable(self.cb_editable.isChecked())
        joininfo.setJoinFieldName(self.cbb_joinfield.currentText())
        joininfo.setJoinLayer(self.joinlayer)
        joininfo.setPrefix(self.le_pre.text())
        joininfo.setTargetFieldName(self.cbb_targetfield.currentText())
        if self.layer.addJoin(joininfo):
            self.showMsg("连接成功！")
        else:
            self.showError("连接失败！")
    # =============================================================
    def addLayer(self, area: str):
        """Main Method"""
        # Get Json
        dataurl = self.getUrl(area)
        if dataurl != "":
            if not self.iface.newProject(True):
                self.showError("需要创建新工程~")
                return
            self.layer = self.iface.addVectorLayer(dataurl, area, "ogr")
            # 标记标记字段
            for i in range(self.cbb_labelingfield.count()-1, -1, -1):
                self.cbb_labelingfield.removeItem(i)
            for col in self.layer.fields():
                self.cbb_labelingfield.addItem(col.name())
            # 设置符号化
            if self.rendererDlg is not None:
                del self.rendererDlg
                self.rendererDlg = None
            self.rendererDlg = QgsRendererPropertiesDialog(self.layer,QgsStyle(),True,self)
            self.sa_symbolize.setWidget(self.rendererDlg)
        else:
            self.showError("地区不存在，或地区名不完整。")
    # ==============================================================
    # 符号化
    def symbolize(self):
        """apply symbol"""
        if self.layer is None:
            self.showError("请先加载地图!")
            return
        self.rendererDlg.apply()
        self.layer.triggerRepaint()
    # wo shi sha bi
    # def singleSymbol(self):
    #     if self.layer is None:
    #         self.showError("请先加载地图！")
    #         return
    #     # 选择颜色
    #     colorDlg = QgsColorDialog(self)
    #     colorDlg.show()
    #     colorDlg.exec_()
    #     color = colorDlg.color().getRgb()
    #     # self.showLog(color)
    #     renderer = self.layer.renderer()
    #     # self.showLog(str(color).replace('(','').replace(')',''))
    #     symbol = QgsFillSymbol.createSimple({'color':str(color).replace('(','').replace(')','')})
    #     renderer.setSymbol(symbol)
    #     self.layer.triggerRepaint()
    #     self.showLog(self.layer.renderer().symbol().symbolLayers()[0].properties())
    #     # def graduatedSymbol(self):
    #     dlg = QgsRendererPropertiesDialog(self.layer,QgsStyle(),true,self)
    #     dlg.show()
    #     dlg.exec_()
    #     graduatedRenderer = QgsGraduatedSymbolRenderer()
    #     self.layer.setRenderer(QgsGraduatedSymbolRenderer())
    #     self.layer.triggerRepaint()
    # ===========================================================
    def exportD(self,filepath):
        """save map"""
        save_options = QgsVectorFileWriter.SaveVectorOptions()
        save_options.driverName = "ESRI Shapefile"
        save_options.fileEncoding = "UTF-8"
        transform_context = QgsProject.instance().transformContext()
        error = QgsVectorFileWriter.writeAsVectorFormatV2(self.layer,
                                                        filepath,
                                                        transform_context,
                                                        save_options)
        if error[0] == QgsVectorFileWriter.NoError:
            self.showMsg("导出成功!")
        else:
            self.showError(error[1])
    # ===========================================================
    def printlayout(self):
        """layout"""
        if self.layer is None:
            self.showError("请先加载地图!")
            return
        if self.le_layoutname.text() == '':
            self.showError("请输入打印布局名")
            return
        if self.layout is None:
            self.layout = QgsPrintLayout(QgsProject.instance())
            self.layout.initializeDefaults()
            self.layout.setName(self.le_layoutname.text())
        # can not add right map QAQ
        mmap = QgsLayoutItemMap(self.layout)
        mmap.setLayers([self.layer])
        # mmap.setExtent(self.layer.extent())
        # mmap.setCrs(self.layer.sourceCrs())
        mmap.attemptMove(QgsLayoutPoint(6, 10, QgsUnitTypes.LayoutMillimeters))
        mmap.attemptResize(QgsLayoutSize(90, 80, QgsUnitTypes.LayoutMillimeters))
        # self.layout.addLayoutItem(mmap)
        if self.cb_mapname.isChecked():
            label = QgsLayoutItemLabel(self.layout)
            label.setText(self.le_mapname.text())
            label.adjustSizeToText()
            self.layout.addLayoutItem(label)
        if self.cb_scale.isChecked():
            item = QgsLayoutItemScaleBar(self.layout)
            item.setStyle('Numeric')
            item.setLinkedMap(mmap) 
            item.applyDefaultSize()
            self.layout.addLayoutItem(item)
        if self.cb_legend.isChecked():
            legend = QgsLayoutItemLegend(self.layout)
            legend.setLinkedMap(mmap)
            self.layout.addLayoutItem(legend)
        layoutManager = QgsProject.instance().layoutManager()
        if layoutManager.layoutByName(self.layout.name()) is None:
            layoutManager.addLayout(self.layout)
        self.iface.openLayoutDesigner(self.layout)
    # ===========================================================
    def labeling(self):
        """labeling layer"""
        if self.layer is None:
            self.showError("请先加载地图!")
            return
        pal_layer = QgsPalLayerSettings()
        pal_layer.fieldName = self.cbb_labelingfield.currentText()
        pal_layer.enabled = True
        pal_layer.placement = QgsPalLayerSettings.OverPoint
        labels = QgsVectorLayerSimpleLabeling(pal_layer)
        self.layer.setLabeling(labels)
        self.layer.setLabelsEnabled(True)
        self.layer.triggerRepaint()
    # ===========================================================
    def setCRS(self):
        """Set CRS"""
        if self.layer is None:
            self.showError("请先加载地图!")
            return
        QgsProject.instance().setCrs(QgsCoordinateReferenceSystem(self.le_CRS.text()))
        self.layer.triggerRepaint()
        self.iface.zoomFull()
    # ===========================================================
    def showError(self, msg):
        """show error dialog"""
        # QgsErrorDialog.show(
        #     QgsError(msg, "Quick Mapping"), "Error")
        self.msgBar.pushWarning("Quick Mapping",str(msg))
    def showMsg(self, msg):
        """show msg"""
        self.msgBar.pushSuccess("Quick Mapping",str(msg))
    def showLog(self, log):
        """show log"""
        QgsMessageLog.logMessage(str(log), 'Quick Mapping', level=Qgis.Info)
