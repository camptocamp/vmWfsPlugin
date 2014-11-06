VmWfsPlugin
===========

Problematic
------------

Currently, the auto-generated attribute form has always the lineEdit widget for all attributes, even if some informations are available in the layer source. In some cases, constrains on fields are easily accessible and settable.

Situation
----------

In a web feature service (WFS), a common restriction is the enumeration. It constrains the value of an attribute to be one of the elements of the enumeration. Graphically speaking, the enumeration is similar to a combo box. In QGIS, a such enumeration would be displayed through a value map widget. Unfortunately, the only behavior hold by the auto-generated form for attribute edition is to set a simple blank line for text edition. It would be very useful for the amateur user of QGIS to have the combox box automatically read from the WFS.

Proposition
------------

A very light plugin has been developed in python allowing the user to set automatically the attributes with valueMap widget based on enumeration present in the WFS
For getting an automated updates of value map,  the user select a layer in the legend tree and click on the plugin button. The mechanism follows these steps:

1.   Check that a wfs layer is selected
2.   Get the DescribeFeatureType service and retrieve the layer element name
3.   From the name, getting the layer type element
4.   In the layer type element, getting all enumeration present
5.   for all attributes having an enumeration in the WFS, setting the valueMap widget with appropriate values

Conclusion
------------

As the plugin seems relevant and usable, it would be pleasant to get the functionality ported in the core.
As this proposition breaks the current state of the  auto-generated attribute form (based on line edit only), we can expect larger developments in the direction of default widgets; for example setting a date widget for a date field present in a database.

