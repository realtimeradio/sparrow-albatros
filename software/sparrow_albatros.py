import os
import struct
import time
import numpy as np
import ads5404
import adf4351

# Design register names
SS_NAME = "ss_adc"

def str2ip(ip):
	iplist = list(map(int, ip.split('.')))
	ipint = 0
	for i in range(4):
		ipint += (iplist[i] << (8*(3-i)))
	return ipint

class SparrowAlbatros():
	def __init__(self, cfpga, fpgfile=None, adc_clk=500.):
		"""
		Constuctor for SparrowAdc2Tge control instance.

		:param cfpga: CasperFpga instance for Sparrow board connection
		:type cfpga: casperfpga.Casperfpga

		:param fpgfile: .fpg file to associate with running firmware. If
			none is provided, certain methods will be unavailable until
			either `program_fpga` or `read_fpgfile` are called.
		:type fpgfile: str

                :param adc_clk: ADC sample rate in MHz
                :type adc_clk: float
		"""
		self.cfpga = cfpga
		self.adc_clk = adc_clk
		self.adc = ads5404.Ads5404(cfpga)
		self.pll = adf4351.Adf4351(cfpga, out_freq=adc_clk)
		self.fpgfile = None
		if fpgfile is not None:
			self.read_fpgfile(fpgfile)

	def initialize_adc(self):
		"""
		Initialize ADC interface.
		"""
		self.adc.chip_reset()
		self.adc.hw_reset()
		self.adc.enable_readback()
		self.adc.init()
		self.sync_adc()

	def sync_adc(self):
		"""
		Send a sync pulse to the ADC
		"""
		self.cfpga.write_int("sync", 0)
		self.cfpga.write_int("sync", 1)
		self.cfpga.write_int("sync", 0)

	def get_adc_temp(self):
		"""
		Get ADC temperature.

		:return: temerature in degrees C
		:rtype: int
		"""
		return self.adc.get_temp()

	def read_fpgfile(self, fpgfile):
		"""
		Associate running firmware with give .fpg file.
		This does _not_ program the FPGA. For that, use `program_fpga()`.
		This is a shortcut to casperfpga's get_system_information.

		:param fpgfile: .fpg file to read
		:type fpgfile: str
		"""
		if not os.path.isfile(fpgfile):
				raise RuntimeError("%s is not a file" % fpgfile)
		self.fpgfile = fpgfile
		try:
			self.cfpga.get_system_information(fpgfile)
		except:
			print("Could not process fpgfile %s. Maybe the FPGA is not programmed yet?" % fpgfile)

	def program_fpga(self, fpgfile=None):
		"""
		Program the FPGA with the provided fpgfile,
		or self.fpgfile if none is provided.

		:param fpgfile: .fpg file to program. If None, the fpgfile
			provided at instantiation time will be programmed.
		:type fpgfile: str
		"""
		self.fpgfile = fpgfile or self.fpgfile
		if self.fpgfile is None:
			raise RuntimeError("Don't know what .fpg file to program!")
		self.cfpga.upload_to_ram_and_program(self.fpgfile)
		time.sleep(0.3)
		self.pll.configure()
		time.sleep(0.3)
		self.adc.power_enable()

	def get_adc_snapshot(self, use_pps_trigger=False):
		"""
		Get a snapshot of ADC samples simultaneously captured from
		both ADC channels.

		:param use_pps_trigger: If True, use the DSP pipeline's PPS trigger to
			start capture. Otherwise, capture immediately.
		:type use_pps_trigger: bool

		:return: x, y; a pair of numpy arrays containing a snapshot of ADC
			samples from ADC channel 0 and 1, respectively.
		:rtype: (numpy.ndarray, numpy.ndarray)
		"""
		if not SS_NAME in self.cfpga.snapshots.keys():
			raise RuntimeError("%s not found in design. Have you provided an appropriate .fpg file?" % SS_NAME)
		ss = self.cfpga.snapshots[SS_NAME]
		d, t = ss.read_raw(man_trig=not use_pps_trigger)	
		v = np.array(struct.unpack(">%dh" % (d["length"]//2), d["data"]))
		x = v[0::2]
		y = v[1::2]
		return x, y
