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
    <rasterrenderer band="1" classificationMin="50" type="singlebandpseudocolor" opacity="1" classificationMax="150" alphaBand="-1" nodataColor="">
      <rasterTransparency>
        <singleValuePixelList>
          <pixelListEntry min="0" percentTransparent="100" max="10"/>
          <pixelListEntry min="181" percentTransparent="100" max="365"/>
        </singleValuePixelList>
      </rasterTransparency>
      <minMaxOrigin>
        <limits>None</limits>
        <extent>WholeRaster</extent>
        <statAccuracy>Estimated</statAccuracy>
        <cumulativeCutLower>0.02</cumulativeCutLower>
        <cumulativeCutUpper>0.98</cumulativeCutUpper>
        <stdDevFactor>2</stdDevFactor>
      </minMaxOrigin>
      <rastershader>
        <colorrampshader labelPrecision="0" colorRampType="DISCRETE" minimumValue="50" classificationMode="2" clip="0" maximumValue="150">
          <colorramp type="gradient" name="[source]">
            <prop k="color1" v="252,251,253,255"/>
            <prop k="color2" v="63,0,125,255"/>
            <prop k="discrete" v="0"/>
            <prop k="rampType" v="gradient"/>
            <prop k="stops" v="0.13;239,237,245,255:0.26;218,218,235,255:0.39;188,189,220,255:0.52;158,154,200,255:0.65;128,125,186,255:0.75;106,81,163,255:0.9;84,39,143,255"/>
          </colorramp>
          <item value="61" color="#fcfbfd" label="&lt; Oct" alpha="255"/>
          <item value="91" color="#dcdcec" label="Nov" alpha="255"/>
          <item value="122" color="#a3a0cb" label="Dec" alpha="255"/>
          <item value="153" color="#6a51a3" label="Jan" alpha="255"/>
          <item value="inf" color="#3f007d" label="> Feb" alpha="255"/>
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
