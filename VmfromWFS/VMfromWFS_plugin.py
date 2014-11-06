# -*- coding: utf-8 -*-
"""
/***************************************************************************
VmFromWfs
                                 A QGIS plugin
Value Map from WFS
                              -------------------
        begin                : 2014-09-24
        git sha              : $Format:%H$
        copyright            : (C) 2014 by Camptocamp SA
        email                : info@camptocamp.com
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
# Import the PyQt and QGIS libraries
import os
import qgis
from qgis.gui import QgsMessageBar
from PyQt4.QtGui import QAction, QIcon, QMessageBox, QDialog
import urllib
from PyQt4 import QtXml

# Initialize Qt resources from file resources.py
import resources

class VmFromWfs:
    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

    def initGui(self):
        # Create action that will start plugin configuration
        self.action = QAction(
            QIcon(":/plugins/VMfromWFS/icon.png"),
            u"Set Value Maps for selected layer", self.iface.mainWindow())
        # connect the action to the run method
        self.action.triggered.connect(self.run)

        # Add toolbar button and menu item
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu(u"&VM_WFS", self.action)

    def unload(self):
        # Remove the plugin menu item and icon
        self.iface.removePluginMenu(u"&VM_WFS", self.action)
        self.iface.removeToolBarIcon(self.action)

    def run(self):
        """For getting an automated updates of value map,
        the user select a layer in the legend tree and click on
        the plugin button. The present run function in launched
        and follow these steps:
        1. check that a wfs layer is selected
        2. get the DescribeFeatureType service and retrieve the layer element name
        3. From the name, getting the layer type element
        4. in the layer type element, getting all enumeration present
        5. for all attributes having an enumeration in the WFS, setting the valueMap
        widget with appropriate values
        """

        # get the current layer
        clayer = qgis.utils.iface.mapCanvas().currentLayer()
        if clayer == None:
            # check that a layer is selected
            self.iface.messageBar().pushMessage("VM from WFS", 'No layer selected', QgsMessageBar.WARNING, 5)
            return
        if clayer.providerType () != 'WFS':
            # check that the layer is a web feature sercvie
            self.iface.messageBar().pushMessage("VM from WFS", 'Layer not from WFS', QgsMessageBar.WARNING, 5)
            return
        source = clayer.source()
        try:
            # get the typeName, usefull in the DescribeFeatureType
            layerName = source.split('TYPENAME')[1].split('&')[0].split(':')[1]
        except:
            self.iface.messageBar().pushMessage("VM from WFS", 'annot retrieve source name\Set layer name as source name', QgsMessageBar.WARNING, 5)
            layerName = clayer.name()

        # Get the DescribeFeatureType
        urlPart1 = source.split('REQUEST')[0]
        urlPart2 = 'REQUEST=DescribeFeatureType'
        url = urlPart1 + urlPart2
        xmlconnect = urllib.urlopen(url)
        xmlbuffer = xmlconnect.read()
        xmlconnect.close()

        # parse the DescribeFeatureType
        doc = QtXml.QDomDocument("EnvironmentML");
        if(not doc.setContent(xmlbuffer)):
            QMessageBox.warning(self, "Error", "Could not parse xml from DescribeFeatureType.")
        root = doc.documentElement()
        self.particle = root.tagName().split(':')[0]

        # First, we retrieve the name of the Type element of the layer
        #
        # Here, the logic is not easy to capt. In the DescribeFeatureType,
        # The layerType is linked to the laye by an element containing
        # the name of the layer and the name of the type.
        # For example, the osm_buildings layer is linked to the osm_buildingsType:
        # <xsd:complexType name="osm_buildingsType">
        #     ...
        # </xsd:complexType>
        # <xsd:element name="osm_buildings" substitutionGroup="gml:_Feature" type="osm:osm_buildingsType"/>
        PFD = doc.elementsByTagName (self.particle + ":element")
        typeName = None
        for index in range(PFD.length()):
            element = PFD.item(index)
            if element.isNull ():
                break
            nodeAttributes = element.attributes()
            for indexAtt in range(nodeAttributes.length()):
                attributeItem = nodeAttributes.item(indexAtt) # pulls out first item
                attribute = attributeItem.toAttr()
                if attribute.name() == 'name':
                    if attribute.value() == layerName:
                        typeAttribute = nodeAttributes.namedItem('type')
                        typeName = typeAttribute.toAttr().value().split(':')[1]
                        break
        if typeName == None:
            return

        # Once we have the name of Type element, we look for it.
        focusType = QtXml.QDomNode()
        complexElmts = doc.elementsByTagName (self.particle + ":complexType")
        for index in range(complexElmts.length()):
            if not focusType.isNull():
                break
            element = complexElmts.item(index)
            if element.isNull():
                break
            nodeAttributes = element.attributes()
            for indexAtt in range(nodeAttributes.length()):
                attributeItem = nodeAttributes.item(indexAtt)
                attribute = attributeItem.toAttr()
                if attribute.name() == 'name':
                    if attribute.value() == typeName:
                        focusType = element
                        break

        # Once we have the Type element, we can extract the enumaration values
        # if there are some.
        dicEnum = {}
        self.getEnumeration(focusType, dicEnum)
        # And then apply modification the the qgis MapLayer.
        self.applyEnumeration(clayer, dicEnum)

        QMessageBox.information(QDialog(), "Value Map widgets", "Value map widgets are succesfully updated\nfor data layer %s" % layerName)

    def applyEnumeration(self, layer, dicEnum):
        fields = layer.pendingFields()
        id = 0
        for field in fields:
            if field.name() in dicEnum:
                values = dicEnum[field.name()]
                layer.setEditorWidgetV2(id, 'ValueMap')
                config = dict(zip(values, values))
                layer.setEditorWidgetV2Config(id, config)
            id += 1

    def getEnumeration(self, Node, dicEnum):
        if self.hasEnumeration(Node): # just a quick check for performance
            n = Node.firstChild()
            while (not n.isNull()):
                if n.nodeName() == self.particle + ':element': # attribute of the layer
                    if n.hasChildNodes(): # it will be a special type...
                        if self.hasEnumeration(n): # ... and it is enumeration
                            listValue = []
                            self.getEnumerationValues(n, listValue)
                            att = n.attributes().namedItem('name').toAttr().value()
                            dicEnum[att] = listValue
                else:
                    self.getEnumeration(n, dicEnum)
                n = n.nextSibling()

    def getEnumerationValues(self, node, listValue):
        n = node.firstChild()
        while (not n.isNull()):
            if n.nodeName() == self.particle + ':enumeration':
                nodeAttributes = n.attributes()
                for indexAtt in range(nodeAttributes.length()):
                    attributeItem = nodeAttributes.item(indexAtt)
                    attribute = attributeItem.toAttr()
                    if attribute.name() == 'value':
                        listValue.append(attribute.value())
            else:
                test = self.getEnumerationValues(n, listValue)
            n = n.nextSibling()

    def hasEnumeration(self, Node):
        test = False
        if Node.hasChildNodes():
            n = Node.firstChild()
            while (not n.isNull()) and not test:
                if n.nodeName() == self.particle + ':enumeration':
                    test = True
                    break
                else:
                    test = self.hasEnumeration(n)
                n = n.nextSibling()
        return test






