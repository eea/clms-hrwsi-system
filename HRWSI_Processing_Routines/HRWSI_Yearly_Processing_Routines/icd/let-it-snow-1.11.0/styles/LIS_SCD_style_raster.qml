<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis maxScale="0" minScale="1e+08" styleCategories="AllStyleCategories" hasScaleBasedVisibilityFlag="0" version="3.6.0-Noosa">
  <flags>
    <Identifiable>1</Identifiable>
    <Removable>1</Removable>
    <Searchable>1</Searchable>
  </flags>
  <customproperties>
    <property value="false" key="WMSBackgroundLayer"/>
    <property value="false" key="WMSPublishDataSourceUrl"/>
    <property value="0" key="embeddedWidgets/count"/>
    <property value="Value" key="identify/format"/>
  </customproperties>
  <pipe>
    <rasterrenderer type="singlebandpseudocolor" band="1" classificationMin="0" classificationMax="366" alphaBand="-1" opacity="1">
      <rasterTransparency/>
      <minMaxOrigin>
        <limits>None</limits>
        <extent>WholeRaster</extent>
        <statAccuracy>Exact</statAccuracy>
        <cumulativeCutLower>0.02</cumulativeCutLower>
        <cumulativeCutUpper>0.98</cumulativeCutUpper>
        <stdDevFactor>2</stdDevFactor>
      </minMaxOrigin>
      <rastershader>
        <colorrampshader classificationMode="2" clip="0" colorRampType="INTERPOLATED">
          <colorramp type="gradient" name="[source]">
            <prop k="color1" v="8,48,107,255"/>
            <prop k="color2" v="247,251,255,255"/>
            <prop k="discrete" v="0"/>
            <prop k="rampType" v="gradient"/>
            <prop k="stops" v="0.1;8,81,156,255:0.22;33,113,181,255:0.35;66,146,198,255:0.48;107,174,214,255:0.61;158,202,225,255:0.74;198,219,239,255:0.87;222,235,247,255"/>
          </colorramp>
          <item label="0" value="0" color="#08306b" alpha="0"/>
          <item label="0-40" value="40" color="#0a549e" alpha="255"/>
          <item label="40-80" value="80" color="#2172b6" alpha="255"/>
          <item label="80-120" value="120" color="#3e8ec4" alpha="255"/>
          <item label="120-160" value="160" color="#60a6d2" alpha="255"/>
          <item label="160-200" value="200" color="#89bfdd" alpha="255"/>
          <item label="200-240" value="240" color="#b0d2e8" alpha="255"/>
          <item label="240-280" value="280" color="#cde0f2" alpha="255"/>
          <item label="280-320" value="320" color="#e2eef9" alpha="255"/>
          <item label="320-366" value="366" color="#f7fbff" alpha="255"/>
        </colorrampshader>
      </rastershader>
    </rasterrenderer>
    <brightnesscontrast contrast="0" brightness="0"/>
    <huesaturation colorizeOn="0" saturation="0" colorizeRed="255" colorizeStrength="100" grayscaleMode="0" colorizeGreen="128" colorizeBlue="128"/>
    <rasterresampler maxOversampling="2"/>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
