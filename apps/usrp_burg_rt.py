#!/usr/bin/env python
#
# Copyright 2004,2005,2007,2008,2010 Free Software Foundation, Inc.
# 
# This file is part of GNU Radio
# 
# GNU Radio is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
# 
# GNU Radio is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with GNU Radio; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
# 

from gnuradio import gr, gru, window
import specest
from gnuradio import usrp
from gnuradio import eng_notation
from gnuradio.eng_option import eng_option
from gnuradio.wxgui import stdgui2, scopesink2, fftsink2, waterfallsink2, form, slider
from optparse import OptionParser
import wx
import sys
import numpy

def pick_subdevice(u):
    """
    The user didn't specify a subdevice on the command line.
    If there's a daughterboard on A, select A.
    If there's a daughterboard on B, select B.
    Otherwise, select A.
    """
    if u.db(0, 0).dbid() >= 0:       # dbid is < 0 if there's no d'board or a problem
        return (0, 0)
    if u.db(0, 0).dbid() >= 0:
        return (1, 0)
    return (0, 0)


class app_top_block(stdgui2.std_top_block):
    def __init__(self, frame, panel, vbox, argv):
        stdgui2.std_top_block.__init__(self, frame, panel, vbox, argv)

        self.frame = frame
        self.panel = panel
        
        parser = OptionParser(option_class=eng_option)
        parser.add_option("-w", "--which", type="int", default=0,
                          help="select which USRP (0, 1, ...) default is %default",
			  metavar="NUM")
        parser.add_option("-R", "--rx-subdev-spec", type="subdev", default=None,
                          help="select USRP Rx side A or B (default=first one with a daughterboard)")
        parser.add_option("-A", "--antenna", default=None,
                          help="select Rx Antenna (only on RFX-series boards)")
        parser.add_option("-d", "--decim", type="int", default=16,
                          help="set fgpa decimation rate to DECIM [default=%default]")
        parser.add_option("-f", "--freq", type="eng_float", default=None,
                          help="set frequency to FREQ", metavar="FREQ")
        parser.add_option("-g", "--gain", type="eng_float", default=None,
                          help="set gain in dB [default is midpoint]")
        parser.add_option("-8", "--width-8", action="store_true", default=False,
                          help="Enable 8-bit samples across USB")
        parser.add_option( "--no-hb", action="store_true", default=False,
                          help="don't use halfband filter in usrp")
        parser.add_option("-S", "--oscilloscope", action="store_true", default=False,
                          help="Enable oscilloscope display")
	parser.add_option("", "--avg-alpha", type="eng_float", default=1e-1,
			  help="Set fftsink averaging factor, [default=%default]")
	parser.add_option("", "--ref-scale", type="eng_float", default=13490.0,
			  help="Set dBFS=0dB input value, [default=%default]")
        parser.add_option("", "--fft-size", type="int", default=512,
                          help="Set FFT frame size, [default=%default]");
	parser.add_option("-e", "--order", type="int", default=4,
                	  help="order of the AR filter for burg estimator")
	parser.add_option("", "--shift-fft", action="store_true", default=True,
                	  help="shift the DC carrier to the middle.")
        parser.add_option("-W", "--waterfall", action="store_true", default=False,
                          help="Enable waterfall display")

        (options, args) = parser.parse_args()
        if len(args) != 0:
            parser.print_help()
            sys.exit(1)
	self.options = options
        self.show_debug_info = True
        
        # build the graph
        if options.no_hb or (options.decim<8):
          #Min decimation of this firmware is 4. 
          #contains 4 Rx paths without halfbands and 0 tx paths.
          self.fpga_filename="std_4rx_0tx.rbf"
          self.u = usrp.source_c(which=options.which, decim_rate=options.decim, fpga_filename=self.fpga_filename)
        else:
          #Min decimation of standard firmware is 8. 
          #standard fpga firmware "std_2rxhb_2tx.rbf" 
          #contains 2 Rx paths with halfband filters and 2 tx paths (the default)
          self.u = usrp.source_c(which=options.which, decim_rate=options.decim)

        if options.rx_subdev_spec is None:
            options.rx_subdev_spec = pick_subdevice(self.u)
        self.u.set_mux(usrp.determine_rx_mux_value(self.u, options.rx_subdev_spec))

        if options.width_8:
            width = 8
            shift = 8
            format = self.u.make_format(width, shift)
            print "format =", hex(format)
            r = self.u.set_format(format)
            print "set_format =", r
            
        # determine the daughterboard subdevice we're using
        self.subdev = usrp.selected_subdev(self.u, options.rx_subdev_spec)

        input_rate = self.u.adc_freq() / self.u.decim_rate()

        self.scope = fftsink2.fft_sink_c (panel, fft_size=options.fft_size, sample_rate=input_rate, 
					      ref_scale=options.ref_scale, ref_level=80, y_divs = 20,
					      avg_alpha=options.avg_alpha)


	toskip = 1

	self.head = gr.head(gr.sizeof_gr_complex, (toskip+1)*options.fft_size)
	self.skip = gr.skiphead(gr.sizeof_gr_complex, toskip*options.fft_size)
	self.burg = specest.burg (options.fft_size, options.fft_size, options.order, options.shift_fft)
	self.f2c = gr.float_to_complex(options.fft_size)
	mywindow2 = window.rectangular(options.fft_size)
	self.ifft = gr.fft_vcc(options.fft_size, False, mywindow2, True)
	self.v2s = gr.vector_to_stream(gr.sizeof_gr_complex, options.fft_size)
        self.connect(self.u, self.burg, self.f2c, self.ifft, self.v2s, self.scope)

        self._build_gui(vbox)
	self._setup_events()
	
        # set initial values

        if options.gain is None:
            # if no gain was specified, use the mid-point in dB
            g = self.subdev.gain_range()
            options.gain = float(g[0]+g[1])/2

        if options.freq is None:
            # if no freq was specified, use the mid-point
            r = self.subdev.freq_range()
            options.freq = float(r[0]+r[1])/2

        self.set_gain(options.gain)

	if options.antenna is not None:
            print "Selecting antenna %s" % (options.antenna,)
            self.subdev.select_rx_antenna(options.antenna)

        if self.show_debug_info:
            self.myform['decim'].set_value(self.u.decim_rate())
            self.myform['fs@usb'].set_value(self.u.adc_freq() / self.u.decim_rate())
            self.myform['dbname'].set_value(self.subdev.name())
            self.myform['baseband'].set_value(0)
            self.myform['ddc'].set_value(0)

        if not(self.set_freq(options.freq)):
            self._set_status_msg("Failed to set initial frequency")

    def _set_status_msg(self, msg):
        self.frame.GetStatusBar().SetStatusText(msg, 0)

    def _build_gui(self, vbox):

        def _form_set_freq(kv):
            return self.set_freq(kv['freq'])
            
        vbox.Add(self.scope.win, 10, wx.EXPAND)
        
        # add control area at the bottom
        self.myform = myform = form.form()
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add((5,0), 0, 0)
        myform['freq'] = form.float_field(
            parent=self.panel, sizer=hbox, label="Center freq", weight=1,
            callback=myform.check_input_and_call(_form_set_freq, self._set_status_msg))

        hbox.Add((5,0), 0, 0)
        g = self.subdev.gain_range()
        myform['gain'] = form.slider_field(parent=self.panel, sizer=hbox, label="Gain",
                                           weight=3,
                                           min=int(g[0]), max=int(g[1]),
                                           callback=self.set_gain)

        hbox.Add((5,0), 0, 0)
        vbox.Add(hbox, 0, wx.EXPAND)

        self._build_subpanel(vbox)

    def _build_subpanel(self, vbox_arg):
        # build a secondary information panel (sometimes hidden)

        # FIXME figure out how to have this be a subpanel that is always
        # created, but has its visibility controlled by foo.Show(True/False)
        
        def _form_set_decim(kv):
            return self.set_decim(kv['decim'])

        if not(self.show_debug_info):
            return

        panel = self.panel
        vbox = vbox_arg
        myform = self.myform

        #panel = wx.Panel(self.panel, -1)
        #vbox = wx.BoxSizer(wx.VERTICAL)

        hbox = wx.BoxSizer(wx.HORIZONTAL)
        hbox.Add((5,0), 0)

        myform['decim'] = form.int_field(
            parent=panel, sizer=hbox, label="Decim",
            callback=myform.check_input_and_call(_form_set_decim, self._set_status_msg))

        hbox.Add((5,0), 1)
        myform['fs@usb'] = form.static_float_field(
            parent=panel, sizer=hbox, label="Fs@USB")

        hbox.Add((5,0), 1)
        myform['dbname'] = form.static_text_field(
            parent=panel, sizer=hbox)

        hbox.Add((5,0), 1)
        myform['baseband'] = form.static_float_field(
            parent=panel, sizer=hbox, label="Analog BB")

        hbox.Add((5,0), 1)
        myform['ddc'] = form.static_float_field(
            parent=panel, sizer=hbox, label="DDC")

        hbox.Add((5,0), 0)
        vbox.Add(hbox, 0, wx.EXPAND)

        
    def set_freq(self, target_freq):
        """
        Set the center frequency we're interested in.

        @param target_freq: frequency in Hz
        @rypte: bool

        Tuning is a two step process.  First we ask the front-end to
        tune as close to the desired frequency as it can.  Then we use
        the result of that operation and our target_frequency to
        determine the value for the digital down converter.
        """
        r = self.u.tune(0, self.subdev, target_freq)
        
        if r:
            self.myform['freq'].set_value(target_freq)     # update displayed value
            if self.show_debug_info:
                self.myform['baseband'].set_value(r.baseband_freq)
                self.myform['ddc'].set_value(r.dxc_freq)
	    #if not self.options.oscilloscope:
		#self.scope.set_baseband_freq(target_freq)
    	    return True

        return False

    def set_gain(self, gain):
        self.myform['gain'].set_value(gain)     # update displayed value
        self.subdev.set_gain(gain)

    def set_decim(self, decim):
        ok = self.u.set_decim_rate(decim)
        if not ok:
            print "set_decim failed"
        input_rate = self.u.adc_freq() / self.u.decim_rate()
        self.scope.set_sample_rate(input_rate)
        if self.show_debug_info:  # update displayed values
            self.myform['decim'].set_value(self.u.decim_rate())
            self.myform['fs@usb'].set_value(self.u.adc_freq() / self.u.decim_rate())
        return ok

    def _setup_events(self):
	if not self.options.waterfall and not self.options.oscilloscope:
	    self.scope.win.Bind(wx.EVT_LEFT_DCLICK, self.evt_left_dclick)
	    
    def evt_left_dclick(self, event):
	(ux, uy) = self.scope.win.GetXY(event)
	if event.CmdDown():
	    # Re-center on maximum power
	    points = self.scope.win._points
	    if self.scope.win.peak_hold:
		if self.scope.win.peak_vals is not None:
		    ind = numpy.argmax(self.scope.win.peak_vals)
		else:
		    ind = int(points.shape()[0]/2)
	    else:
        	ind = numpy.argmax(points[:,1])
            (freq, pwr) = points[ind]
	    target_freq = freq/self.scope.win._scale_factor
	    print ind, freq, pwr
            self.set_freq(target_freq)            
	else:
	    # Re-center on clicked frequency
	    target_freq = ux/self.scope.win._scale_factor
	    self.set_freq(target_freq)
	    
	
def main ():
    app = stdgui2.stdapp(app_top_block, "USRP Burg", nstatus=1)
    app.MainLoop()

if __name__ == '__main__':
    main ()
