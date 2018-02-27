import sys
import POC_LIB


test = POC_LIB.nifty_parser(sys.argv[1])
POC_LIB.save_slice(POC_LIB.format_image(*test), sys.argv[2])