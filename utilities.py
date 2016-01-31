import math
import commands

basedir='/home/pi/code'
hw_volume_level = (0, 0)

def is_wired():
    # Identify if a network cable is plugged or not
    netCablePlugged = True
    checkCableCmd = 'ip link show | grep eth0'
    cmdOutput = commands.getoutput(checkCableCmd)
    try:
        foundAt = cmdOutput.index('LOWER_UP')
    except ValueError:
        print "cable unplugged"
        netCablePlugged = False
    else:
        print "cable plugged"
    return netCablePlugged


def power_usb_bus(desired_state):    
    # Turn on of off the usb bus and network
    # Return true if network connectivity is ok after powering on,
    # false otherwise, or none when powering down (no feedback)
    # Only perform function if board is not wired!
    global basedir

    if desired_state :
        print("Turning the USB bus ON")
        powerUsbBusCmd = basedir + "/mcclock/usbBusUp.bash"
        result = commands.getstatusoutput(powerUsbBusCmd)
        cmdOutput = result[1]
        if int(result[0]) == 0:
            network_state = True
            print("network connectivity ok")
        else:
            network_state = False
            print("no network connectivity")
    else :
        wired = is_wired()
        # (wired is considered debug mode, we do not want the usb bus
        # to go down, certainly after startup...)
        network_state = None
        if not wired:
            print("Turning the USB bus OFF")
            powerUsbBusCmd = basedir + "/mcclock/usbBusDown.bash"
            cmdOutput = commands.getoutput(powerUsbBusCmd)
            print("Result from: "+powerUsbBusCmd+" -> "+cmdOutput)
    return network_state


def set_hw_volume(input):
    global hw_volume_level
    
    if input < 1.0:
        vol = 0
    else:
        vol = round(50.0*math.log10(0.96*input))
    print "linear input volume",input,"-> log output volume=",vol,"%"
    cmd = 'amixer cset numid=3 '+str(vol)+'%'
    ret = commands.getstatusoutput(cmd)
    if ret[0] != 0:
        print "command [",cmd,"]failed"
    else:
        hw_volume_level = (input, vol)
        
def get_hw_volume():
    global hw_volume_level
    return hw_volume_level

