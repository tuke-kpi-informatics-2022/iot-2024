from my.mq7 import MQ7
import utime

pin=26

sensor = MQ7(pinData = pin, baseVoltage = 3)

print("Calibrating")
sensor.calibrate()
print("Calibration completed")
print("Base resistance:{0}".format(sensor._ro))

while True:
    print("CarbonMonoxide: {:.6f}".format(sensor.readCarbonMonoxide())+" - ", end="\n")
    utime.sleep(0.5)