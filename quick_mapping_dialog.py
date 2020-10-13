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
        self.categorizedSRWidget = None
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
                "table(*.csv *.xlsx)")[0]))
        # style
        self.pb_single.clicked.connect(self.singleSymbol)
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
        if area in self.areaCode:
            if area[4:6] == "00":
                if self.cb_include.isChecked():
                    dataurl = 'https://geo.datav.aliyun.com/areas_v2/bound/' + \
                        area+'_full.json'
                else:
                    dataurl = 'https://geo.datav.aliyun.com/areas_v2/bound/' + \
                        area+'.json'
            else:
                dataurl = 'https://geo.datav.aliyun.com/areas_v2/bound/' + \
                    area+'.json'
        # name?
        elif area in self.areaName:
            area = self.areaCode[self.areaName.index(area)]
            if area[4:6] == "00":
                if self.cb_include.isChecked():
                    dataurl = 'https://geo.datav.aliyun.com/areas_v2/bound/' + \
                        area+'_full.json'
                else:
                    dataurl = 'https://geo.datav.aliyun.com/areas_v2/bound/' + \
                        area+'.json'
            else:
                dataurl = 'https://geo.datav.aliyun.com/areas_v2/bound/' + \
                    area+'.json'
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
            self.iface.newProject(True)
            self.layer = self.iface.addVectorLayer(dataurl, area, "ogr")
        else:
            self.showError("地区不存在，或地区名不完整。")
    def singleSymbol(self):
        if self.layer is None:
            self.showError("请先加载地图！")
            return
        # 选择颜色
        colorDlg = QgsColorDialog(self)
        colorDlg.show()
        colorDlg.exec_()
        color = colorDlg.color().getRgbF()
        renderer = self.layer.renderer()
        symbol = QgsFillSymbol.createSimple({'color': color})
        self.layer.renderer().setSymbol(symbol)
        self.layer.triggerRepaint()
        
    def applySymbol(self):
        self.categorizedSRWidget.renderer().startRender()
        self.categorizedSRWidget.applyChangeToSymbol()
        self.categorizedSRWidget.applyChanges()
        self.categorizedSRWidget.renderer().stopRender()
        self.layer.triggerRepaint()
    # ===========================================================
    def showError(self, msg: str):
        """show error dialog"""
        # QgsErrorDialog.show(
        #     QgsError(msg, "Quick Mapping"), "Error")
        self.msgBar.pushWarning("Quick Mapping",msg)
    def showMsg(self, msg: str):
        """show msg"""
        self.msgBar.pushSuccess("Quick Mapping",msg)
    def showLog(self, log: str):
        """show log"""
        QgsMessageLog.logMessage(log, 'Quick Mapping', level=Qgis.Info)
