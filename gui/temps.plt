<?xml version="1.0" encoding="UTF-8"?>
<databrowser>
  <title></title>
  <show_toolbar>true</show_toolbar>
  <update_period>3.0</update_period>
  <scroll_step>5</scroll_step>
  <scroll>true</scroll>
  <start>-30 minutes</start>
  <end>now</end>
  <archive_rescale>STAGGER</archive_rescale>
  <foreground>
    <red>0</red>
    <green>0</green>
    <blue>0</blue>
  </foreground>
  <background>
    <red>255</red>
    <green>255</green>
    <blue>255</blue>
  </background>
  <title_font>Liberation Sans|20|1</title_font>
  <label_font>Liberation Sans|14|1</label_font>
  <scale_font>Liberation Sans|12|0</scale_font>
  <legend_font>Liberation Sans|14|0</legend_font>
  <axes>
    <axis>
      <visible>true</visible>
      <name>Value 1</name>
      <use_axis_name>false</use_axis_name>
      <use_trace_names>true</use_trace_names>
      <right>false</right>
      <color>
        <red>0</red>
        <green>0</green>
        <blue>0</blue>
      </color>
      <min>2.1255593715640077E-10</min>
      <max>3.0708145682493695E-5</max>
      <grid>true</grid>
      <autoscale>false</autoscale>
      <log_scale>true</log_scale>
    </axis>
    <axis>
      <visible>true</visible>
      <name>Value 2</name>
      <use_axis_name>false</use_axis_name>
      <use_trace_names>true</use_trace_names>
      <right>false</right>
      <color>
        <red>0</red>
        <green>0</green>
        <blue>0</blue>
      </color>
      <min>55.18718644067797</min>
      <max>74.54718644067796</max>
      <grid>false</grid>
      <autoscale>false</autoscale>
      <log_scale>false</log_scale>
    </axis>
    <axis>
      <visible>true</visible>
      <name>Value 3</name>
      <use_axis_name>false</use_axis_name>
      <use_trace_names>true</use_trace_names>
      <right>true</right>
      <color>
        <red>0</red>
        <green>0</green>
        <blue>0</blue>
      </color>
      <min>4.0</min>
      <max>45.0</max>
      <grid>false</grid>
      <autoscale>false</autoscale>
      <log_scale>false</log_scale>
    </axis>
    <axis>
      <visible>false</visible>
      <name>Value 4</name>
      <use_axis_name>false</use_axis_name>
      <use_trace_names>true</use_trace_names>
      <right>true</right>
      <color>
        <red>153</red>
        <green>153</green>
        <blue>153</blue>
      </color>
      <min>3.498305084745766</min>
      <max>299.49830508474577</max>
      <grid>false</grid>
      <autoscale>false</autoscale>
      <log_scale>false</log_scale>
    </axis>
    <axis>
      <visible>true</visible>
      <name>Value 5</name>
      <use_axis_name>false</use_axis_name>
      <use_trace_names>true</use_trace_names>
      <right>false</right>
      <color>
        <red>0</red>
        <green>0</green>
        <blue>0</blue>
      </color>
      <min>14.5</min>
      <max>22.0</max>
      <grid>false</grid>
      <autoscale>false</autoscale>
      <log_scale>false</log_scale>
    </axis>
  </axes>
  <annotations>
  </annotations>
  <pvlist>
    <pv>
      <display_name>OVC_Pirani_PI</display_name>
      <visible>false</visible>
      <name>TGT:BTARG:OVC_Pirani_PI</name>
      <axis>0</axis>
      <color>
        <red>77</red>
        <green>128</green>
        <blue>77</blue>
      </color>
      <trace_type>AREA</trace_type>
      <linewidth>1</linewidth>
      <line_style>SOLID</line_style>
      <point_type>NONE</point_type>
      <point_size>2</point_size>
      <waveform_index>0</waveform_index>
      <period>0.0</period>
      <ring_size>5000</ring_size>
      <request>OPTIMIZED</request>
    </pv>
    <pv>
      <display_name>OVC_CC_PI</display_name>
      <visible>true</visible>
      <name>TGT:BTARG:OVC_CC_PI</name>
      <axis>0</axis>
      <color>
        <red>255</red>
        <green>0</green>
        <blue>255</blue>
      </color>
      <trace_type>AREA</trace_type>
      <linewidth>1</linewidth>
      <line_style>DOT</line_style>
      <point_type>NONE</point_type>
      <point_size>2</point_size>
      <waveform_index>0</waveform_index>
      <period>0.0</period>
      <ring_size>5000</ring_size>
      <request>OPTIMIZED</request>
    </pv>
    <pv>
      <display_name>Shield_Flow</display_name>
      <visible>false</visible>
      <name>TGT:BTARG:Shield_FI</name>
      <axis>1</axis>
      <color>
        <red>255</red>
        <green>0</green>
        <blue>0</blue>
      </color>
      <trace_type>AREA</trace_type>
      <linewidth>1</linewidth>
      <line_style>DASHDOT</line_style>
      <point_type>NONE</point_type>
      <point_size>2</point_size>
      <waveform_index>0</waveform_index>
      <period>0.0</period>
      <ring_size>5000</ring_size>
      <request>OPTIMIZED</request>
    </pv>
    <pv>
      <display_name>Evaporator_Flow</display_name>
      <visible>false</visible>
      <name>TGT:BTARG:Evaporator_FI</name>
      <axis>1</axis>
      <color>
        <red>0</red>
        <green>0</green>
        <blue>255</blue>
      </color>
      <trace_type>AREA</trace_type>
      <linewidth>1</linewidth>
      <line_style>DASHDOT</line_style>
      <point_type>NONE</point_type>
      <point_size>2</point_size>
      <waveform_index>0</waveform_index>
      <period>0.0</period>
      <ring_size>5000</ring_size>
      <request>OPTIMIZED</request>
    </pv>
    <pv>
      <display_name>TgtShld=Precool_Flow</display_name>
      <visible>false</visible>
      <name>pva://TGT:BTARG:Precool_FI</name>
      <axis>1</axis>
      <color>
        <red>153</red>
        <green>153</green>
        <blue>153</blue>
      </color>
      <trace_type>AREA</trace_type>
      <linewidth>1</linewidth>
      <line_style>DASH</line_style>
      <point_type>NONE</point_type>
      <point_size>2</point_size>
      <waveform_index>0</waveform_index>
      <period>0.0</period>
      <ring_size>5000</ring_size>
      <request>OPTIMIZED</request>
    </pv>
    <pv>
      <display_name>Coolant_TI</display_name>
      <visible>true</visible>
      <name>TGT:BTARG:Coolant_TI</name>
      <axis>2</axis>
      <color>
        <red>26</red>
        <green>77</green>
        <blue>77</blue>
      </color>
      <trace_type>AREA</trace_type>
      <linewidth>2</linewidth>
      <line_style>SOLID</line_style>
      <point_type>NONE</point_type>
      <point_size>2</point_size>
      <waveform_index>0</waveform_index>
      <period>0.0</period>
      <ring_size>5000</ring_size>
      <request>OPTIMIZED</request>
    </pv>
    <pv>
      <display_name>Reservoir_Bottom_TI</display_name>
      <visible>true</visible>
      <name>TGT:BTARG:Reservoir_Bottom_TI</name>
      <axis>2</axis>
      <color>
        <red>51</red>
        <green>26</green>
        <blue>128</blue>
      </color>
      <trace_type>AREA</trace_type>
      <linewidth>2</linewidth>
      <line_style>SOLID</line_style>
      <point_type>NONE</point_type>
      <point_size>2</point_size>
      <waveform_index>0</waveform_index>
      <period>0.0</period>
      <ring_size>5000</ring_size>
      <request>OPTIMIZED</request>
    </pv>
    <pv>
      <display_name>Reservoir_Top_TI</display_name>
      <visible>false</visible>
      <name>TGT:BTARG:Reservoir_Top_TI</name>
      <axis>2</axis>
      <color>
        <red>153</red>
        <green>128</green>
        <blue>230</blue>
      </color>
      <trace_type>AREA</trace_type>
      <linewidth>2</linewidth>
      <line_style>SOLID</line_style>
      <point_type>NONE</point_type>
      <point_size>2</point_size>
      <waveform_index>0</waveform_index>
      <period>0.0</period>
      <ring_size>5000</ring_size>
      <request>OPTIMIZED</request>
    </pv>
    <pv>
      <display_name>Evaporator_TI</display_name>
      <visible>true</visible>
      <name>TGT:BTARG:Evaporator_TI</name>
      <axis>2</axis>
      <color>
        <red>102</red>
        <green>128</green>
        <blue>230</blue>
      </color>
      <trace_type>AREA</trace_type>
      <linewidth>2</linewidth>
      <line_style>SOLID</line_style>
      <point_type>NONE</point_type>
      <point_size>2</point_size>
      <waveform_index>0</waveform_index>
      <period>0.0</period>
      <ring_size>5000</ring_size>
      <request>OPTIMIZED</request>
    </pv>
    <pv>
      <display_name>Shield_Plate_TI</display_name>
      <visible>true</visible>
      <name>pva://TGT:BTARG:Shield_Plate_TI</name>
      <axis>2</axis>
      <color>
        <red>255</red>
        <green>127</green>
        <blue>0</blue>
      </color>
      <trace_type>AREA</trace_type>
      <linewidth>2</linewidth>
      <line_style>SOLID</line_style>
      <point_type>NONE</point_type>
      <point_size>2</point_size>
      <waveform_index>0</waveform_index>
      <period>0.0</period>
      <ring_size>5000</ring_size>
      <request>OPTIMIZED</request>
    </pv>
    <pv>
      <display_name>Cell_Top_TI</display_name>
      <visible>true</visible>
      <name>TGT:BTARG:Cell_Top_TI</name>
      <axis>2</axis>
      <color>
        <red>128</red>
        <green>0</green>
        <blue>0</blue>
      </color>
      <trace_type>AREA</trace_type>
      <linewidth>2</linewidth>
      <line_style>SOLID</line_style>
      <point_type>NONE</point_type>
      <point_size>2</point_size>
      <waveform_index>0</waveform_index>
      <period>0.0</period>
      <ring_size>5000</ring_size>
      <request>OPTIMIZED</request>
    </pv>
    <pv>
      <display_name>Cell_Bottom_TI</display_name>
      <visible>true</visible>
      <name>pva://TGT:BTARG:Cell_Bottom_TI</name>
      <axis>2</axis>
      <color>
        <red>255</red>
        <green>0</green>
        <blue>0</blue>
      </color>
      <trace_type>AREA</trace_type>
      <linewidth>2</linewidth>
      <line_style>SOLID</line_style>
      <point_type>NONE</point_type>
      <point_size>2</point_size>
      <waveform_index>0</waveform_index>
      <period>0.0</period>
      <ring_size>5000</ring_size>
      <request>OPTIMIZED</request>
    </pv>
    <pv>
      <display_name>Shield_DS_TI</display_name>
      <visible>true</visible>
      <name>pva://TGT:BTARG:Shield_DS_TI</name>
      <axis>2</axis>
      <color>
        <red>255</red>
        <green>128</green>
        <blue>128</blue>
      </color>
      <trace_type>AREA</trace_type>
      <linewidth>1</linewidth>
      <line_style>DOT</line_style>
      <point_type>NONE</point_type>
      <point_size>2</point_size>
      <waveform_index>0</waveform_index>
      <period>0.0</period>
      <ring_size>5000</ring_size>
      <request>OPTIMIZED</request>
    </pv>
    <pv>
      <display_name>Res Shield_Top_TI</display_name>
      <visible>false</visible>
      <name>TGT:BTARG:Shield_Top_TI</name>
      <axis>3</axis>
      <color>
        <red>127</red>
        <green>63</green>
        <blue>0</blue>
      </color>
      <trace_type>AREA</trace_type>
      <linewidth>1</linewidth>
      <line_style>DOT</line_style>
      <point_type>NONE</point_type>
      <point_size>2</point_size>
      <waveform_index>0</waveform_index>
      <period>0.0</period>
      <ring_size>5000</ring_size>
      <request>OPTIMIZED</request>
    </pv>
    <pv>
      <display_name>Evaporator_Out_TI</display_name>
      <visible>true</visible>
      <name>pva://TGT:BTARG:Evaporator_Out_TI</name>
      <axis>2</axis>
      <color>
        <red>153</red>
        <green>179</green>
        <blue>255</blue>
      </color>
      <trace_type>AREA</trace_type>
      <linewidth>2</linewidth>
      <line_style>SOLID</line_style>
      <point_type>NONE</point_type>
      <point_size>2</point_size>
      <waveform_index>0</waveform_index>
      <period>0.0</period>
      <ring_size>5000</ring_size>
      <request>OPTIMIZED</request>
    </pv>
    <pv>
      <display_name>TGT:BTARG:Target_Supply_PI</display_name>
      <visible>true</visible>
      <name>TGT:BTARG:Target_Supply_PI</name>
      <axis>4</axis>
      <color>
        <red>0</red>
        <green>128</green>
        <blue>0</blue>
      </color>
      <trace_type>AREA</trace_type>
      <linewidth>2</linewidth>
      <line_style>SOLID</line_style>
      <point_type>NONE</point_type>
      <point_size>2</point_size>
      <waveform_index>0</waveform_index>
      <period>0.0</period>
      <ring_size>5000</ring_size>
      <request>OPTIMIZED</request>
    </pv>
  </pvlist>
</databrowser>
