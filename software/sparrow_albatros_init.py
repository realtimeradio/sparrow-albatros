#! /usr/bin/env python
import sys
import time
import argparse
import logging
import casperfpga
from sparrow_albatros import SparrowAlbatros

def run(host, fpgfile,
        adc_clk=500,
        skipprog=False,
        ):

    logger = logging.getLogger(__file__)
    logger.setLevel(logging.INFO)
    #handler = logging.StreamHandler(sys.stdout)
    #handler.setLevel(logging.INFO)
    #logger.addHandler(handler)

    logger.info("Connecting to board with hostname %s" % host)
    cfpga = casperfpga.CasperFpga(host, transport=casperfpga.KatcpTransport)

    logger.info("Instantiating control object with fpgfile %s" % fpgfile)
    sparrow = SparrowAlbatros(cfpga, fpgfile=fpgfile, adc_clk=adc_clk)

    if not skipprog:
        logger.info("Programming FPGA at %s with %s" % (host, fpgfile))
        sparrow.program_fpga()

    fpga_clock_mhz = sparrow.cfpga.estimate_fpga_clock()
    logger.info("Estimated FPGA clock is %.2f MHz" % fpga_clock_mhz)

    if fpga_clock_mhz < 1:
        raise RuntimeError("FPGA doesn't seem to be clocking correctly")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Program and initialize a Sparrow ADC->10GbE design',
                                 formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('host', type=str,
                        help = 'Hostname / IP of Sparrow board')
    parser.add_argument('fpgfile', type=str, 
                        help = '.fpgfile to program or /read')
    parser.add_argument('--adc_clk', type=float, default=500.0,
                        help ='ADC sample rate in MHz')
    parser.add_argument('--skipprog', dest='skipprog', action='store_true', default=False,
                        help='Skip programming .fpg file')

    args = parser.parse_args()
    run(args.host, args.fpgfile,
        adc_clk = args.adc_clk,
        skipprog=args.skipprog,
        )
