<!DOCTYPE qgis PUBLIC 'http://mrcc.com/qgis.dtd' 'SYSTEM'>
<qgis styleCategories="AllStyleCategories" hasScaleBasedVisibilityFlag="0" minScale="1e+08" maxScale="0" version="3.16.4-Hannover">
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
    <property key="WMSBackgroundLayer" value="false"/>
    <property key="WMSPublishDataSourceUrl" value="false"/>
    <property key="embeddedWidgets/count" value="0"/>
    <property key="identify/format" value="Value"/>
  </customproperties>
  <pipe>
    <provider>
      <resampling enabled="false" zoomedOutResamplingMethod="bilinear" zoomedInResamplingMethod="bilinear" maxOversampling="2"/>
    </provider>
    <rasterrenderer band="1" classificationMin="181" type="singlebandpseudocolor" opacity="1" classificationMax="334" alphaBand="-1" nodataColor="">
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
        <colorrampshader labelPrecision="0" colorRampType="DISCRETE" minimumValue="181" classificationMode="2" clip="0" maximumValue="334">
          <colorramp type="gradient" name="[source]">
            <prop k="color1" v="247,251,255,255"/>
            <prop k="color2" v="8,48,107,255"/>
            <prop k="discrete" v="0"/>
            <prop k="rampType" v="gradient"/>
            <prop k="stops" v="0.13;222,235,247,255:0.26;198,219,239,255:0.39;158,202,225,255:0.52;107,174,214,255:0.65;66,146,198,255:0.78;33,113,181,255:0.9;8,81,156,255"/>
          </colorramp>
          <item value="181" color="#f7fbff" label="&lt; Mar" alpha="255"/>
          <item value="212" color="#d1e3f3" label="Mar" alpha="255"/>
          <item value="242" color="#9ac8e1" label="Apr" alpha="255"/>
          <item value="273" color="#529dcc" label="May" alpha="255"/>
          <item value="303" color="#1c6cb1" label="Jun" alpha="255"/>
          <item value="inf" color="#08306b" label="> July" alpha="255"/>
        </colorrampshader>
      </rastershader>
    </rasterrenderer>
    <brightnesscontrast gamma="1" contrast="0" brightness="0"/>
    <huesaturation colorizeRed="255" colorizeOn="0" colorizeBlue="128" colorizeGreen="128" grayscaleMode="0" saturation="0" colorizeStrength="100"/>
    <rasterresampler zoomedOutResampler="bilinear" zoomedInResampler="bilinear" maxOversampling="2"/>
    <resamplingStage>resamplingFilter</resamplingStage>
  </pipe>
  <blendMode>0</blendMode>
</qgis>
