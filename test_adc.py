import spidev
import time
import os

spi = spidev.SpiDev()
spi.open(0,0)

# List of pins to read voltage from
adc_pins = (0, 2, 3, 5)

# read SPI data from MCP3008 chip, 8 possible adc's (0 thru 7)
def readadc(adcnum):
        if ((adcnum > 7) or (adcnum < 0)):
                return -1
	r = spi.xfer2([1,(8+adcnum)<<4,0])
	adcout = ((r[1]&3) << 8) + r[2]
	return adcout

samples = 1000
start = time.time()

v = [0.0, 0.0, 0.0, 0.0]
for i in range(0,samples):
        for i,p in enumerate(adc_pins):
                v[i] = v[i]+readadc(p)

stop = time.time()

print "time for",samples,"*3 readings =",stop-start

while True:
        for p in adc_pins:
                v = readadc(p)
                print v,
        print
        
        # hang out and do nothing for a half second
        time.sleep(0.2)
