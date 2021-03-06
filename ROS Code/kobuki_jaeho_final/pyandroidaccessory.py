#!/usr/bin/python
from math import *


import usb.core
import usb.util
import sys
import struct
import time
import random
import rospy
from motion_travel_forward import TravelForward 

VID_GALAXY_NEXUS_DEBUG = 0x04e8
PID_GALAXY_NEXUS_DEBUG = 0x6860

VID_ANDROID_ACCESSORY = 0x18d1
PID_ANDROID_ACCESSORY = 0x2d01

WAITING_STATE = 0
RECEIVING_STATE = 1

R_EARTH = 6371000

#add the sign to the angle value
def addSign(i,angleArr) :
    if i==0 :
        return 0
    else :
        lat1 = angleArr[i-1][0]
        long1 = angleArr[i-1][1]
        lat2 = angleArr[i][0]
        long2 = angleArr[i][1]
        lat3 = angleArr[i+1][0]
        long3 = angleArr[i+1][1]
        dlat1 = lat2-lat1
        dlat2 = lat3-lat2
        dlong1 = long2-long1
        dlong2 = long3-long2
        crossProduct = dlat1*dlong2-dlat2*dlong1
        if crossProduct>=0 :
            return 1
        else :
            return -1;

# unit conversion
def degToRad(deg) :
    return deg*pi/180

def radToDeg(rad) :
    return  rad*180/pi

# angle difference Method
def angleDiffMethod(angleArr, NUM) :
    NUM = len(angleArr)
    diffDistanceConti = [0 for i in range(NUM)]
    diffDistancePrev = [0 for i in range(NUM)]
    diffAngle = [0 for i in range(NUM)]
    returnArr = [ [0 for i in range(2)] for j in range(NUM-1)]

    for i in range(0,NUM):
        for j in range(0,2):
            angleArr[i][j]=degToRad(angleArr[i][j])

    # diffDistancePrev[i] refers 'from i to i+1'
    for i in range(0,NUM-1) :
        pi1 = angleArr[i][0]
        pi2 = angleArr[i+1][0]
        dpi = angleArr[i+1][0]-angleArr[i][0]
        dlambda = angleArr[i+1][1]-angleArr[i][1]
        a = sin(dpi/2)*sin(dpi/2)+cos(pi1)*cos(pi2)*sin(dlambda/2)*sin(dlambda/2)
        c = 2*atan2(sqrt(a),sqrt(1-a))
        diffDistancePrev[i]=R_EARTH*c

    #diffDistanceConti[i] refers 'from i to i+2'
    for i in range(0,NUM-2) :
        pi1 = angleArr[i][0]
        pi2 = angleArr[i+2][0]
        dpi = angleArr[i+2][0]-angleArr[i][0]
        dlambda = angleArr[i+2][1]-angleArr[i][1]
        a = sin(dpi/2)*sin(dpi/2)+cos(pi1)*cos(pi2)*sin(dlambda/2)*sin(dlambda/2)
        c = 2*atan2(sqrt(a),sqrt(1-a))
        diffDistanceConti[i]=R_EARTH*c
    # anglediff  means the vector difference between two pathes,and It measured  the clockwise from the origin Vector
    for i in range(1,NUM-1) :
        a = diffDistanceConti[i-1]
        b = diffDistancePrev[i-1]
        c = diffDistancePrev[i]
        cosValue= (b*b+c*c-a*a)/(2*b*c);
        if cosValue>1 :
            cosValue = 1
        elif cosValue<-1 :
            cosValue = -1
        #add degree of Sign 'acos (-1 to 1) (0 to PI)'
        diffAngle[i]=(180-radToDeg(acos(cosValue)))*addSign(i,angleArr)
    print(returnValue(diffDistancePrev, diffAngle, NUM))
    return returnValue(diffDistancePrev, diffAngle, NUM)

def printValue() :
    for i in range(0,NUM-1) :
        print "trial%d\tdistance : %f\tangle %f"  % (i+1,diffDistancePrev[i],diffAngle[i])

def returnValue(diffDistancePrev, diffAngle, NUM) : 
    returnArr = [ [0 for i in range(2)] for j in range(NUM-1)]
    for i in range(0,NUM-1) :
       # if i == 0:
        #    returnArr[i][0]= diffDistancePrev[i]
        #else:
		#	for k in range(0,i+1):
		#		returnArr[i][0]=returnArr[i][0] + diffDistancePrev[k]
        returnArr[i][0]= diffDistancePrev[i]
        returnArr[i][1]=diffAngle[i]
    return returnArr

# To develop :
#   - remove Accessory mode ?
#   - start application when already in accessory mode

def get_accessory():
    print('Looking for Android Accessory')
    print('VID: 0x%0.4x - PID: 0x%0.4x'
        % (VID_ANDROID_ACCESSORY, PID_ANDROID_ACCESSORY))
    dev = usb.core.find(idVendor=VID_ANDROID_ACCESSORY, 
                        idProduct=PID_ANDROID_ACCESSORY)
    return dev

def get_android_device():
    print('Looking for Galaxy Nexus')
    print('VID: 0x%0.4x - PID: 0x%0.4x'
        % (VID_GALAXY_NEXUS_DEBUG, PID_GALAXY_NEXUS_DEBUG))
    android_dev = usb.core.find(idVendor=VID_GALAXY_NEXUS_DEBUG, 
        idProduct=PID_GALAXY_NEXUS_DEBUG)
    if android_dev:
        print('Samsung Galaxy Nexus (debug) found')
    else:
        sys.exit('No Android device found')
    return android_dev


def set_protocol(ldev):

    try:
        ldev.set_configuration()
    except usb.core.USBError as e:
        if  e.errno == 16:
            print('Device already configured, should be OK')
        else:
	    print(e.errno)
            sys.exit('Configuration failed')

    ret = ldev.ctrl_transfer(0xC0, 51, 0, 0, 2)

# Dunno how to translate: array('B', [2, 0])
    protocol = ret[0]

    print('Protocol version: %i' % protocol)
   # if protocol < 2:
    #    sys.exit('Android Open Accessory protocol v2 not supported')

    return

def set_strings(ldev):
    send_string(ldev, 0, 'KIMHOON')
    send_string(ldev, 1, 'PyAndroidAccessory')
    send_string(ldev, 2, 'A Python based Android accessory')
    send_string(ldev, 3, '0.1.0')
    send_string(ldev, 4, 
        'http://zombiebrainzjuice.cc/py-android-accessory/')
    send_string(ldev, 5, '2254711SerialNo.')    
    return

def set_accessory_mode(ldev):
    ret = ldev.ctrl_transfer(0x40, 53, 0, 0, '', 0)    
    if ret:
        sys.exit('Start-up failed')
    time.sleep(1)
    return

def send_string(ldev, str_id, str_val):
    ret = ldev.ctrl_transfer(0x40, 52, 0, str_id, str_val, 0)
    if ret != len(str_val):
        sys.exit('Failed to send string %i' % str_id) 
    return 

def start_accessory_mode():
    dev = get_accessory()
    if not dev:
        print('Android accessory not found')
        print('Try to start accessory mode')
        dev = get_android_device()
        set_protocol(dev)
        set_strings(dev)
        set_accessory_mode(dev)
        dev = get_accessory()
        if not dev:
            sys.exit('Unable to start accessory mode')
    print('Accessory mode started')
    return dev

def sensor_variation(toss):
    return {
        -10: -1,
        10: 1
    }.get(toss, 0)

def sensor_output(lsensor, variation):
    output = lsensor + variation
    if output < 0:
        output = 0
    else:
        if output > 100:
            output = 100
    return output

def wait_for_command(ldev):
    state = WAITING_STATE
    lat_i = 0
    lng_i = 0
    #sensor = 50

    while True:
        try:
            #print ('Sensor: %i' % sensor)
            #msg = ('S%0.4i' % sensor)
            #print('<<< ' + msg),
            #try:
                #ret = ldev.write(0x02,msg, 150)
			
		#print(ret)
         #       if ret == len(msg):
          #          print(' - Write OK')
           # except usb.core.USBError as e:
            #    print e

            print('>>> '),
            try:
                if state == WAITING_STATE: 
                    ret = ldev.read(0x82, 8)
                    sret = ''.join([chr(x) for x in ret])
                    print sret
                    if sret == "STARTTRX":
						print "Transmission from android started"
						state = RECEIVING_STATE
						lat_i = 0
						lng_i = 0
                    else:
		                print "Wrong State : Should be STARTTRX"
                else:
                    ret = ldev.read(0x82, 8)
                    sret = ''.join([chr(x) for x in ret])
                    print sret
                    if sret == "PATHSIZE": 
                        ret = ldev.read(0x82, 8)                  
                        pathsize = struct.unpack('>i', ret[:4])[0]
                        print pathsize
                        path_Matrix = [[0 for x in range(2)] for x in range(pathsize)] 
                    if sret == "LATIDATA":
                        print lat_i                   
                        ret = ldev.read(0x82, 8)
                        value = struct.unpack('>d', ret)[0]
                        path_Matrix[lat_i][0] = value
                        print value
                        lat_i = lat_i + 1
                    elif sret == "LONGDATA":
                        print lng_i
                        ret = ldev.read(0x82, 8)
                        value = struct.unpack('>d', ret)[0]
                        path_Matrix[lng_i][1] = value
                        print value
                        lng_i = lng_i + 1
                    elif sret == "ENDTRX__":
                        state = WAITING_STATE
                        print path_Matrix
                        received_data = angleDiffMethod(path_Matrix, pathsize)
                        return received_data
                
            except usb.core.USBError as e:
                print e
            time.sleep(0.2)
        except KeyboardInterrupt:
            print "Bye!"
            break
        

#        msg='test'

    return

# Define a main() function 
def main():

    dev = start_accessory_mode()
    received_data = wait_for_command(dev)

    print("KOBUKI MOVE!!")
    rospy.init_node('test_motionforward')

    cmdvel_topic = '/mobile_base/commands/velocity'
    odom_topic = '/odom'
    cliff_topic =  '/mobile_base/events/cliff'
    length_cali = 16.470
    calibration = length_cali/received_data[0][0]
    for i in range(0,len(received_data)):
     	travel = TravelForward(cmdvel_topic,odom_topic, cliff_topic)
       
     	travel.init(0.4, received_data[i][0]*calibration,-received_data[i][1])

     	rospy.loginfo("Start to move forward")
     
     	travel.execute()
     	travel.stop()
     	rospy.loginfo("Stop")

# 'This is the standard boilerplate that calls the main() function.
if __name__ == '__main__':
    main()
