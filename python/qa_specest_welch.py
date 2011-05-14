#!/usr/bin/env python
#
# Copyright 2001-2008 Free Software Foundation, Inc.
# Copyright 2009 Institut fuer Nachrichtentechnik / Uni Karlsruhe
#
# This is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software; see the file COPYING.  If not, write to
# the Free Software Foundation, Inc., 51 Franklin Street,
# Boston, MA 02110-1301, USA.
#

from gnuradio import gr, gr_unittest
import specest_swig as specest
from numpy import *

class test_specest_welch(gr_unittest.TestCase):
    def setUp (self):
        self.tb = gr.top_block ()

    def tearDown (self):
        self.tb = None

    def test_001(self):
        """ Run test:
        - No overlap
        - Hamming window from Python
        - Constant input signal of amplitude 1

        The given input signal has a known power of 1. Therefore, the integral of the
        PSD estimation result should be pretty close to 1."""
        fft_len = 256
        overlap = 0
        ma_len = 1
        window = hamming(fft_len)

        src_data = (1,) * ((ma_len + 1) * fft_len)
        src = gr.vector_source_c(src_data, False)
        welch = specest.welch(fft_len, overlap, ma_len, False, window)
        sink = gr.vector_sink_f(fft_len)

        self.tb.connect(src, welch, sink)
        self.tb.run()

        dst_data =  sink.data()
        dst_data = array(dst_data[-fft_len:])
        power_est = sum(dst_data) * 2 * pi / fft_len

        self.assertAlmostEqual(power_est, 1, 5)


    def test_default_002(self):
        """ Same test as before, but different parameters (FFT length, moving average and
        the window comes from C++). """
        fft_len = 1024
        ma_len = 8

        src_data = (1,) * ((ma_len/2 + 1) * fft_len)
        src = gr.vector_source_c(src_data, False)
        welch = specest.welch(fft_len)
        sink = gr.vector_sink_f(fft_len)

        self.tb.connect(src, welch, sink)
        self.tb.run()

        dst_data =  sink.data()
        dst_data = array(dst_data[-fft_len:])
        power_est = sum(dst_data) * 2 * pi / fft_len

        self.assertAlmostEqual(power_est, 1, 5)


    def test_exception1_003(self):
        """ Make sure an exception is thrown when an invalid overlap is chosen. """
        self.assertRaises(ValueError, specest.welch, 1024, -5)


    def test_exception2_004(self):
        """ Make sure an exception is thrown when an invalid window is given. """
        self.assertRaises(ValueError, specest.welch, 1024, 5, 5, False, (1,2,3))



if __name__ == '__main__':
    gr_unittest.main ()

