<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis version="3.14.0-Pi" minScale="1e+08" maxScale="0" styleCategories="AllStyleCategories" hasScaleBasedVisibilityFlag="0">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <temporal fetchMode="0" enabled="0" mode="0">
    <fixedRange>
      <start></start>
      <end></end>
    </fixedRange>
  </temporal>
  <customproperties>
    <property value="false" key="WMSBackgroundLayer"/>
    <property value="false" key="WMSPublishDataSourceUrl"/>
    <property value="0" key="embeddedWidgets/count"/>
    <property value="Value" key="identify/format"/>
  </customproperties>
  <pipe>
    <rasterrenderer classificationMax="110" classificationMin="20" alphaBand="-1" nodataColor="" type="singlebandpseudocolor" opacity="1" band="1">
      <rasterTransparency/>
      <minMaxOrigin>
        <limits>None</limits>
        <extent>WholeRaster</extent>
        <statAccuracy>Estimated</statAccuracy>
        <cumulativeCutLower>0.02</cumulativeCutLower>
        <cumulativeCutUpper>0.98</cumulativeCutUpper>
        <stdDevFactor>2</stdDevFactor>
      </minMaxOrigin>
      <rastershader>
        <colorrampshader clip="0" maximumValue="110" minimumValue="20" colorRampType="DISCRETE" classificationMode="2">
          <colorramp name="[source]" type="gradient">
            <prop k="color1" v="255,255,178,255"/>
            <prop k="color2" v="189,0,38,255"/>
            <prop k="discrete" v="0"/>
            <prop k="rampType" v="gradient"/>
            <prop k="stops" v="0.25;254,204,92,255:0.5;253,141,60,255:0.75;240,59,32,255"/>
          </colorramp>
          <item alpha="255" label="&lt;= 35" value="35" color="#ffffb2"/>
          <item alpha="255" label="35 - 50" value="50" color="#ffd76d"/>
          <item alpha="255" label="50 - 65" value="65" color="#fea649"/>
          <item alpha="255" label="65 - 80" value="80" color="#f86c30"/>
          <item alpha="255" label="80 - 95" value="95" color="#e62f21"/>
          <item alpha="255" label="> 95" value="inf" color="#bd0026"/>
        </colorrampshader>
      </rastershader>
    </rasterrenderer>
    <brightnesscontrast contrast="0" brightness="0"/>
    <huesaturation colorizeStrength="100" grayscaleMode="0" colorizeOn="0" colorizeRed="255" colorizeBlue="128" saturation="0" colorizeGreen="128"/>
    <rasterresampler maxOversampling="2" zoomedOutResampler="bilinear"/>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
