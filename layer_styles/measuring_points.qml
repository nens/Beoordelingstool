<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="2.18.17" simplifyAlgorithm="0" minimumScale="0" maximumScale="1e+08" simplifyDrawingHints="0" minLabelScale="0" maxLabelScale="1e+08" simplifyDrawingTol="1" readOnly="0" simplifyMaxScale="1" hasScaleBasedVisibilityFlag="0" simplifyLocal="1" scaleBasedLabelVisibilityFlag="0">
 <edittypes>
  <edittype widgetv2type="TextEdit" name="PIPE_ID">
   <widgetv2config IsMultiline="0" fieldEditable="1" constraint="" UseHtml="0" labelOnTop="0" constraintDescription="" notNull="0"/>
  </edittype>
  <edittype widgetv2type="TextEdit" name="x">
   <widgetv2config IsMultiline="0" fieldEditable="1" constraint="" UseHtml="0" labelOnTop="0" constraintDescription="" notNull="0"/>
  </edittype>
  <edittype widgetv2type="TextEdit" name="y">
   <widgetv2config IsMultiline="0" fieldEditable="1" constraint="" UseHtml="0" labelOnTop="0" constraintDescription="" notNull="0"/>
  </edittype>
  <edittype widgetv2type="TextEdit" name="A">
   <widgetv2config IsMultiline="0" fieldEditable="1" constraint="" UseHtml="0" labelOnTop="0" constraintDescription="" notNull="0"/>
  </edittype>
  <edittype widgetv2type="TextEdit" name="B">
   <widgetv2config IsMultiline="0" fieldEditable="1" constraint="" UseHtml="0" labelOnTop="0" constraintDescription="" notNull="0"/>
  </edittype>
  <edittype widgetv2type="TextEdit" name="C">
   <widgetv2config IsMultiline="0" fieldEditable="1" constraint="" UseHtml="0" labelOnTop="0" constraintDescription="" notNull="0"/>
  </edittype>
  <edittype widgetv2type="TextEdit" name="D">
   <widgetv2config IsMultiline="0" fieldEditable="1" constraint="" UseHtml="0" labelOnTop="0" constraintDescription="" notNull="0"/>
  </edittype>
  <edittype widgetv2type="TextEdit" name="E">
   <widgetv2config IsMultiline="0" fieldEditable="1" constraint="" UseHtml="0" labelOnTop="0" constraintDescription="" notNull="0"/>
  </edittype>
  <edittype widgetv2type="TextEdit" name="F">
   <widgetv2config IsMultiline="0" fieldEditable="1" constraint="" UseHtml="0" labelOnTop="0" constraintDescription="" notNull="0"/>
  </edittype>
  <edittype widgetv2type="TextEdit" name="G">
   <widgetv2config IsMultiline="0" fieldEditable="1" constraint="" UseHtml="0" labelOnTop="0" constraintDescription="" notNull="0"/>
  </edittype>
  <edittype widgetv2type="TextEdit" name="I">
   <widgetv2config IsMultiline="0" fieldEditable="1" constraint="" UseHtml="0" labelOnTop="0" constraintDescription="" notNull="0"/>
  </edittype>
  <edittype widgetv2type="TextEdit" name="J">
   <widgetv2config IsMultiline="0" fieldEditable="1" constraint="" UseHtml="0" labelOnTop="0" constraintDescription="" notNull="0"/>
  </edittype>
  <edittype widgetv2type="TextEdit" name="K">
   <widgetv2config IsMultiline="0" fieldEditable="1" constraint="" UseHtml="0" labelOnTop="0" constraintDescription="" notNull="0"/>
  </edittype>
  <edittype widgetv2type="TextEdit" name="M">
   <widgetv2config IsMultiline="0" fieldEditable="1" constraint="" UseHtml="0" labelOnTop="0" constraintDescription="" notNull="0"/>
  </edittype>
  <edittype widgetv2type="TextEdit" name="N">
   <widgetv2config IsMultiline="0" fieldEditable="1" constraint="" UseHtml="0" labelOnTop="0" constraintDescription="" notNull="0"/>
  </edittype>
  <edittype widgetv2type="TextEdit" name="O">
   <widgetv2config IsMultiline="0" fieldEditable="1" constraint="" UseHtml="0" labelOnTop="0" constraintDescription="" notNull="0"/>
  </edittype>
  <edittype widgetv2type="TextEdit" name="Herstelmaa">
   <widgetv2config IsMultiline="0" fieldEditable="1" constraint="" UseHtml="0" labelOnTop="0" constraintDescription="" notNull="0"/>
  </edittype>
  <edittype widgetv2type="TextEdit" name="Opmerking">
   <widgetv2config IsMultiline="0" fieldEditable="1" constraint="" UseHtml="0" labelOnTop="0" constraintDescription="" notNull="0"/>
  </edittype>
  <edittype widgetv2type="TextEdit" name="Trigger">
   <widgetv2config IsMultiline="0" fieldEditable="1" constraint="" UseHtml="0" labelOnTop="0" constraintDescription="" notNull="0"/>
  </edittype>
 </edittypes>
 <renderer-v2 forceraster="0" symbollevels="0" type="RuleRenderer" enableorderby="0">
  <rules key="{eae7d24f-325f-4021-9ed3-0f5983e75447}">
   <rule filter="&quot;Trigger&quot; = 'Ingrijp' AND (&quot;Herstelmaa&quot; = '' OR &quot;Herstelmaa&quot; IS NULL)" key="{93759a70-289d-4258-b057-8a54b6ea631c}" symbol="0" label="Niet beoordeeld - Ingrijp"/>
   <rule description="Niet beoordeeld - Waarschuwing" filter="&quot;Trigger&quot; = 'Waarschuwing' AND (&quot;Herstelmaa&quot; = '' OR &quot;Herstelmaa&quot; IS NULL)" key="{9b01ac1f-8423-4e07-8dea-855d55ea9bcb}" symbol="1" label="Niet beoordeeld - Waarschuwing"/>
   <rule filter="&quot;Herstelmaa&quot; != '' OR &quot;Herstelmaa&quot; IS NOT NULL" key="{0f43af2b-4f12-4457-ae98-e55f200618d0}" symbol="2" label="Beoordeeld"/>
  </rules>
  <symbols>
   <symbol alpha="1" clip_to_extent="1" type="marker" name="0">
    <layer pass="0" class="SimpleMarker" locked="0">
     <prop k="angle" v="0"/>
     <prop k="color" v="245,15,3,255"/>
     <prop k="horizontal_anchor_point" v="1"/>
     <prop k="joinstyle" v="bevel"/>
     <prop k="name" v="circle"/>
     <prop k="offset" v="0,0"/>
     <prop k="offset_map_unit_scale" v="0,0,0,0,0,0"/>
     <prop k="offset_unit" v="MM"/>
     <prop k="outline_color" v="0,0,0,255"/>
     <prop k="outline_style" v="solid"/>
     <prop k="outline_width" v="0"/>
     <prop k="outline_width_map_unit_scale" v="0,0,0,0,0,0"/>
     <prop k="outline_width_unit" v="MM"/>
     <prop k="scale_method" v="diameter"/>
     <prop k="size" v="2"/>
     <prop k="size_map_unit_scale" v="0,0,0,0,0,0"/>
     <prop k="size_unit" v="MM"/>
     <prop k="vertical_anchor_point" v="1"/>
    </layer>
   </symbol>
   <symbol alpha="1" clip_to_extent="1" type="marker" name="1">
    <layer pass="0" class="SimpleMarker" locked="0">
     <prop k="angle" v="0"/>
     <prop k="color" v="234,163,11,255"/>
     <prop k="horizontal_anchor_point" v="1"/>
     <prop k="joinstyle" v="bevel"/>
     <prop k="name" v="circle"/>
     <prop k="offset" v="0,0"/>
     <prop k="offset_map_unit_scale" v="0,0,0,0,0,0"/>
     <prop k="offset_unit" v="MM"/>
     <prop k="outline_color" v="0,0,0,255"/>
     <prop k="outline_style" v="solid"/>
     <prop k="outline_width" v="0"/>
     <prop k="outline_width_map_unit_scale" v="0,0,0,0,0,0"/>
     <prop k="outline_width_unit" v="MM"/>
     <prop k="scale_method" v="diameter"/>
     <prop k="size" v="2"/>
     <prop k="size_map_unit_scale" v="0,0,0,0,0,0"/>
     <prop k="size_unit" v="MM"/>
     <prop k="vertical_anchor_point" v="1"/>
    </layer>
   </symbol>
   <symbol alpha="1" clip_to_extent="1" type="marker" name="2">
    <layer pass="0" class="SimpleMarker" locked="0">
     <prop k="angle" v="0"/>
     <prop k="color" v="68,128,67,255"/>
     <prop k="horizontal_anchor_point" v="1"/>
     <prop k="joinstyle" v="bevel"/>
     <prop k="name" v="circle"/>
     <prop k="offset" v="0,0"/>
     <prop k="offset_map_unit_scale" v="0,0,0,0,0,0"/>
     <prop k="offset_unit" v="MM"/>
     <prop k="outline_color" v="0,0,0,255"/>
     <prop k="outline_style" v="solid"/>
     <prop k="outline_width" v="0"/>
     <prop k="outline_width_map_unit_scale" v="0,0,0,0,0,0"/>
     <prop k="outline_width_unit" v="MM"/>
     <prop k="scale_method" v="diameter"/>
     <prop k="size" v="2"/>
     <prop k="size_map_unit_scale" v="0,0,0,0,0,0"/>
     <prop k="size_unit" v="MM"/>
     <prop k="vertical_anchor_point" v="1"/>
    </layer>
   </symbol>
  </symbols>
 </renderer-v2>
 <labeling type="simple"/>
 <customproperties>
  <property key="embeddedWidgets/count" value="0"/>
  <property key="labeling" value="pal"/>
  <property key="labeling/addDirectionSymbol" value="false"/>
  <property key="labeling/angleOffset" value="0"/>
  <property key="labeling/blendMode" value="0"/>
  <property key="labeling/bufferBlendMode" value="0"/>
  <property key="labeling/bufferColorA" value="255"/>
  <property key="labeling/bufferColorB" value="255"/>
  <property key="labeling/bufferColorG" value="255"/>
  <property key="labeling/bufferColorR" value="255"/>
  <property key="labeling/bufferDraw" value="false"/>
  <property key="labeling/bufferJoinStyle" value="64"/>
  <property key="labeling/bufferNoFill" value="false"/>
  <property key="labeling/bufferSize" value="1"/>
  <property key="labeling/bufferSizeInMapUnits" value="false"/>
  <property key="labeling/bufferSizeMapUnitScale" value="0,0,0,0,0,0"/>
  <property key="labeling/bufferTransp" value="0"/>
  <property key="labeling/centroidInside" value="false"/>
  <property key="labeling/centroidWhole" value="false"/>
  <property key="labeling/decimals" value="3"/>
  <property key="labeling/displayAll" value="false"/>
  <property key="labeling/dist" value="0"/>
  <property key="labeling/distInMapUnits" value="false"/>
  <property key="labeling/distMapUnitScale" value="0,0,0,0,0,0"/>
  <property key="labeling/drawLabels" value="false"/>
  <property key="labeling/enabled" value="false"/>
  <property key="labeling/fieldName" value=""/>
  <property key="labeling/fitInPolygonOnly" value="false"/>
  <property key="labeling/fontCapitals" value="0"/>
  <property key="labeling/fontFamily" value="Ubuntu"/>
  <property key="labeling/fontItalic" value="true"/>
  <property key="labeling/fontLetterSpacing" value="0"/>
  <property key="labeling/fontLimitPixelSize" value="false"/>
  <property key="labeling/fontMaxPixelSize" value="10000"/>
  <property key="labeling/fontMinPixelSize" value="3"/>
  <property key="labeling/fontSize" value="11"/>
  <property key="labeling/fontSizeInMapUnits" value="false"/>
  <property key="labeling/fontSizeMapUnitScale" value="0,0,0,0,0,0"/>
  <property key="labeling/fontStrikeout" value="false"/>
  <property key="labeling/fontUnderline" value="false"/>
  <property key="labeling/fontWeight" value="63"/>
  <property key="labeling/fontWordSpacing" value="0"/>
  <property key="labeling/formatNumbers" value="false"/>
  <property key="labeling/isExpression" value="true"/>
  <property key="labeling/labelOffsetInMapUnits" value="true"/>
  <property key="labeling/labelOffsetMapUnitScale" value="0,0,0,0,0,0"/>
  <property key="labeling/labelPerPart" value="false"/>
  <property key="labeling/leftDirectionSymbol" value="&lt;"/>
  <property key="labeling/limitNumLabels" value="false"/>
  <property key="labeling/maxCurvedCharAngleIn" value="20"/>
  <property key="labeling/maxCurvedCharAngleOut" value="-20"/>
  <property key="labeling/maxNumLabels" value="2000"/>
  <property key="labeling/mergeLines" value="false"/>
  <property key="labeling/minFeatureSize" value="0"/>
  <property key="labeling/multilineAlign" value="0"/>
  <property key="labeling/multilineHeight" value="1"/>
  <property key="labeling/namedStyle" value="Medium Italic"/>
  <property key="labeling/obstacle" value="true"/>
  <property key="labeling/obstacleFactor" value="1"/>
  <property key="labeling/obstacleType" value="0"/>
  <property key="labeling/offsetType" value="0"/>
  <property key="labeling/placeDirectionSymbol" value="0"/>
  <property key="labeling/placement" value="0"/>
  <property key="labeling/placementFlags" value="10"/>
  <property key="labeling/plussign" value="false"/>
  <property key="labeling/predefinedPositionOrder" value="TR,TL,BR,BL,R,L,TSR,BSR"/>
  <property key="labeling/preserveRotation" value="true"/>
  <property key="labeling/previewBkgrdColor" value="#ffffff"/>
  <property key="labeling/priority" value="5"/>
  <property key="labeling/quadOffset" value="4"/>
  <property key="labeling/repeatDistance" value="0"/>
  <property key="labeling/repeatDistanceMapUnitScale" value="0,0,0,0,0,0"/>
  <property key="labeling/repeatDistanceUnit" value="1"/>
  <property key="labeling/reverseDirectionSymbol" value="false"/>
  <property key="labeling/rightDirectionSymbol" value=">"/>
  <property key="labeling/scaleMax" value="10000000"/>
  <property key="labeling/scaleMin" value="1"/>
  <property key="labeling/scaleVisibility" value="false"/>
  <property key="labeling/shadowBlendMode" value="6"/>
  <property key="labeling/shadowColorB" value="0"/>
  <property key="labeling/shadowColorG" value="0"/>
  <property key="labeling/shadowColorR" value="0"/>
  <property key="labeling/shadowDraw" value="false"/>
  <property key="labeling/shadowOffsetAngle" value="135"/>
  <property key="labeling/shadowOffsetDist" value="1"/>
  <property key="labeling/shadowOffsetGlobal" value="true"/>
  <property key="labeling/shadowOffsetMapUnitScale" value="0,0,0,0,0,0"/>
  <property key="labeling/shadowOffsetUnits" value="1"/>
  <property key="labeling/shadowRadius" value="1.5"/>
  <property key="labeling/shadowRadiusAlphaOnly" value="false"/>
  <property key="labeling/shadowRadiusMapUnitScale" value="0,0,0,0,0,0"/>
  <property key="labeling/shadowRadiusUnits" value="1"/>
  <property key="labeling/shadowScale" value="100"/>
  <property key="labeling/shadowTransparency" value="30"/>
  <property key="labeling/shadowUnder" value="0"/>
  <property key="labeling/shapeBlendMode" value="0"/>
  <property key="labeling/shapeBorderColorA" value="255"/>
  <property key="labeling/shapeBorderColorB" value="128"/>
  <property key="labeling/shapeBorderColorG" value="128"/>
  <property key="labeling/shapeBorderColorR" value="128"/>
  <property key="labeling/shapeBorderWidth" value="0"/>
  <property key="labeling/shapeBorderWidthMapUnitScale" value="0,0,0,0,0,0"/>
  <property key="labeling/shapeBorderWidthUnits" value="1"/>
  <property key="labeling/shapeDraw" value="false"/>
  <property key="labeling/shapeFillColorA" value="255"/>
  <property key="labeling/shapeFillColorB" value="255"/>
  <property key="labeling/shapeFillColorG" value="255"/>
  <property key="labeling/shapeFillColorR" value="255"/>
  <property key="labeling/shapeJoinStyle" value="64"/>
  <property key="labeling/shapeOffsetMapUnitScale" value="0,0,0,0,0,0"/>
  <property key="labeling/shapeOffsetUnits" value="1"/>
  <property key="labeling/shapeOffsetX" value="0"/>
  <property key="labeling/shapeOffsetY" value="0"/>
  <property key="labeling/shapeRadiiMapUnitScale" value="0,0,0,0,0,0"/>
  <property key="labeling/shapeRadiiUnits" value="1"/>
  <property key="labeling/shapeRadiiX" value="0"/>
  <property key="labeling/shapeRadiiY" value="0"/>
  <property key="labeling/shapeRotation" value="0"/>
  <property key="labeling/shapeRotationType" value="0"/>
  <property key="labeling/shapeSVGFile" value=""/>
  <property key="labeling/shapeSizeMapUnitScale" value="0,0,0,0,0,0"/>
  <property key="labeling/shapeSizeType" value="0"/>
  <property key="labeling/shapeSizeUnits" value="1"/>
  <property key="labeling/shapeSizeX" value="0"/>
  <property key="labeling/shapeSizeY" value="0"/>
  <property key="labeling/shapeTransparency" value="0"/>
  <property key="labeling/shapeType" value="0"/>
  <property key="labeling/substitutions" value="&lt;substitutions/>"/>
  <property key="labeling/textColorA" value="255"/>
  <property key="labeling/textColorB" value="0"/>
  <property key="labeling/textColorG" value="0"/>
  <property key="labeling/textColorR" value="0"/>
  <property key="labeling/textTransp" value="0"/>
  <property key="labeling/upsidedownLabels" value="0"/>
  <property key="labeling/useSubstitutions" value="false"/>
  <property key="labeling/wrapChar" value=""/>
  <property key="labeling/xOffset" value="0"/>
  <property key="labeling/yOffset" value="0"/>
  <property key="labeling/zIndex" value="0"/>
  <property key="variableNames"/>
  <property key="variableValues"/>
 </customproperties>
 <blendMode>0</blendMode>
 <featureBlendMode>0</featureBlendMode>
 <layerTransparency>0</layerTransparency>
 <displayfield>CAA</displayfield>
 <label>0</label>
 <labelattributes>
  <label fieldname="" text="Label"/>
  <family fieldname="" name="Ubuntu"/>
  <size fieldname="" units="pt" value="12"/>
  <bold fieldname="" on="0"/>
  <italic fieldname="" on="0"/>
  <underline fieldname="" on="0"/>
  <strikeout fieldname="" on="0"/>
  <color fieldname="" red="0" blue="0" green="0"/>
  <x fieldname=""/>
  <y fieldname=""/>
  <offset x="0" y="0" units="pt" yfieldname="" xfieldname=""/>
  <angle fieldname="" value="0" auto="0"/>
  <alignment fieldname="" value="center"/>
  <buffercolor fieldname="" red="255" blue="255" green="255"/>
  <buffersize fieldname="" units="pt" value="1"/>
  <bufferenabled fieldname="" on=""/>
  <multilineenabled fieldname="" on=""/>
  <selectedonly on=""/>
 </labelattributes>
 <SingleCategoryDiagramRenderer diagramType="Pie" sizeLegend="0" attributeLegend="1">
  <DiagramCategory penColor="#000000" labelPlacementMethod="XHeight" penWidth="0" diagramOrientation="Up" sizeScale="0,0,0,0,0,0" minimumSize="0" barWidth="5" penAlpha="255" maxScaleDenominator="1e+08" backgroundColor="#ffffff" transparency="0" width="15" scaleDependency="Area" backgroundAlpha="255" angleOffset="1440" scaleBasedVisibility="0" enabled="0" height="15" lineSizeScale="0,0,0,0,0,0" sizeType="MM" lineSizeType="MM" minScaleDenominator="inf">
   <fontProperties description="Ubuntu,11,-1,5,50,0,0,0,0,0" style=""/>
   <attribute field="" color="#000000" label=""/>
  </DiagramCategory>
  <symbol alpha="1" clip_to_extent="1" type="marker" name="sizeSymbol">
   <layer pass="0" class="SimpleMarker" locked="0">
    <prop k="angle" v="0"/>
    <prop k="color" v="255,0,0,255"/>
    <prop k="horizontal_anchor_point" v="1"/>
    <prop k="joinstyle" v="bevel"/>
    <prop k="name" v="circle"/>
    <prop k="offset" v="0,0"/>
    <prop k="offset_map_unit_scale" v="0,0,0,0,0,0"/>
    <prop k="offset_unit" v="MM"/>
    <prop k="outline_color" v="0,0,0,255"/>
    <prop k="outline_style" v="solid"/>
    <prop k="outline_width" v="0"/>
    <prop k="outline_width_map_unit_scale" v="0,0,0,0,0,0"/>
    <prop k="outline_width_unit" v="MM"/>
    <prop k="scale_method" v="diameter"/>
    <prop k="size" v="2"/>
    <prop k="size_map_unit_scale" v="0,0,0,0,0,0"/>
    <prop k="size_unit" v="MM"/>
    <prop k="vertical_anchor_point" v="1"/>
   </layer>
  </symbol>
 </SingleCategoryDiagramRenderer>
 <DiagramLayerSettings yPosColumn="-1" showColumn="0" linePlacementFlags="10" placement="0" dist="0" xPosColumn="-1" priority="0" obstacle="0" zIndex="0" showAll="1"/>
 <annotationform></annotationform>
 <aliases>
  <alias field="PIPE_ID" index="0" name=""/>
  <alias field="x" index="1" name=""/>
  <alias field="y" index="2" name=""/>
  <alias field="A" index="3" name=""/>
  <alias field="B" index="4" name=""/>
  <alias field="C" index="5" name=""/>
  <alias field="D" index="6" name=""/>
  <alias field="E" index="7" name=""/>
  <alias field="F" index="8" name=""/>
  <alias field="G" index="9" name=""/>
  <alias field="I" index="10" name=""/>
  <alias field="J" index="11" name=""/>
  <alias field="K" index="12" name=""/>
  <alias field="M" index="13" name=""/>
  <alias field="N" index="14" name=""/>
  <alias field="O" index="15" name=""/>
  <alias field="Herstelmaa" index="16" name=""/>
  <alias field="Opmerking" index="17" name=""/>
  <alias field="Trigger" index="18" name=""/>
 </aliases>
 <excludeAttributesWMS/>
 <excludeAttributesWFS/>
 <attributeactions default="-1"/>
 <attributetableconfig actionWidgetStyle="dropDown" sortExpression="" sortOrder="0">
  <columns>
   <column width="-1" hidden="0" type="field" name="PIPE_ID"/>
   <column width="-1" hidden="0" type="field" name="x"/>
   <column width="-1" hidden="0" type="field" name="y"/>
   <column width="-1" hidden="0" type="field" name="A"/>
   <column width="-1" hidden="0" type="field" name="B"/>
   <column width="-1" hidden="0" type="field" name="C"/>
   <column width="-1" hidden="0" type="field" name="D"/>
   <column width="-1" hidden="0" type="field" name="E"/>
   <column width="-1" hidden="0" type="field" name="F"/>
   <column width="-1" hidden="0" type="field" name="G"/>
   <column width="-1" hidden="0" type="field" name="I"/>
   <column width="-1" hidden="0" type="field" name="J"/>
   <column width="-1" hidden="0" type="field" name="K"/>
   <column width="-1" hidden="0" type="field" name="M"/>
   <column width="-1" hidden="0" type="field" name="N"/>
   <column width="-1" hidden="0" type="field" name="O"/>
   <column width="-1" hidden="0" type="field" name="Herstelmaa"/>
   <column width="-1" hidden="0" type="field" name="Opmerking"/>
   <column width="-1" hidden="0" type="field" name="Trigger"/>
   <column width="-1" hidden="1" type="actions"/>
  </columns>
 </attributetableconfig>
 <editform></editform>
 <editforminit/>
 <editforminitcodesource>0</editforminitcodesource>
 <editforminitfilepath></editforminitfilepath>
 <editforminitcode><![CDATA[# -*- coding: utf-8 -*-
"""
QGIS forms can have a Python function that is called when the form is
opened.

Use this function to add extra logic to your forms.

Enter the name of the function in the "Python Init function"
field.
An example follows:
"""
from PyQt4.QtGui import QWidget

def my_form_open(dialog, layer, feature):
	geom = feature.geometry()
	control = dialog.findChild(QWidget, "MyLineEdit")
]]></editforminitcode>
 <featformsuppress>0</featformsuppress>
 <editorlayout>generatedlayout</editorlayout>
 <widgets/>
 <conditionalstyles>
  <rowstyles/>
  <fieldstyles/>
 </conditionalstyles>
 <defaults>
  <default field="PIPE_ID" expression=""/>
  <default field="x" expression=""/>
  <default field="y" expression=""/>
  <default field="A" expression=""/>
  <default field="B" expression=""/>
  <default field="C" expression=""/>
  <default field="D" expression=""/>
  <default field="E" expression=""/>
  <default field="F" expression=""/>
  <default field="G" expression=""/>
  <default field="I" expression=""/>
  <default field="J" expression=""/>
  <default field="K" expression=""/>
  <default field="M" expression=""/>
  <default field="N" expression=""/>
  <default field="O" expression=""/>
  <default field="Herstelmaa" expression=""/>
  <default field="Opmerking" expression=""/>
  <default field="Trigger" expression=""/>
 </defaults>
 <previewExpression>COALESCE("CAA", '&lt;NULL>')</previewExpression>
 <layerGeometryType>0</layerGeometryType>
</qgis>
