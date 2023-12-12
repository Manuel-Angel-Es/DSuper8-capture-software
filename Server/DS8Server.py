#!/usr/bin/python3

"""
per8 project based on Joe Herman's rpi-film-capture.

Software modified by Manuel Ángel.

User interface redesigned by Manuel Ángel.

DS8Servidor.py: Server software main program.

Latest version: 20231130.
"""

from socket import (socket, AF_INET, SOCK_STREAM, SHUT_RDWR, SOL_SOCKET,
                    SO_REUSEADDR)

from threading import Thread, Event, Lock

from struct import pack

from io import BytesIO

# Processes are used to control the stepper motor.
from multiprocessing import Queue, Event as Evento, Value

from queue import Queue as Cola, Empty

from time import sleep

from sys import stdout, exit

from logging import INFO, basicConfig, info

# Our own modules.
from controlProcess import DS8Control, MotorDriver

from camera import DS8Camera

from codes import *

import config


class DS8Server():

    def __init__(self):

        # Counter of images taken by the camera.
        self.imgcount = 0       

        # Compression quality parameter for preview.
        self.jpegQualityPr = 60

        # Compression quality parameter for capture.
        self.jpegQualityCap = 97

        # Compression quality parameter for automatic exposure calculation.
        self.jpegQualityAE = 30        

        # This variable determines if we advance after each photo.
        # It is activated and deactivated by commands from the client.
        self.autoAdvance = False

        # Main server loop event to stop preview images and image sending
        # threads.
        self.mainExitEvent = Event()
        self.mainExitEvent.clear()

        # Photo capture event.
        self.capEvent = Evento()

        # Event to stop the engine process.
        self.motExitEvent = Evento()

        # Queue for sending orders to the MotorDriver control process.
        self.motorQueue = Queue()

        # Shared variable. Determines the sending of frame forward/reverse
        # signals.
        self.svUpdateFrame = Value("I", 0)

        # Shared variable. Determines the sending of engine stop signals.
        self.svSendStop = Value("I", 1)

        # Camera instance.
        self.cam = DS8Camera()

        # Connection lock used for sending images.
        self.connectionLock = Lock()

        # Motor and lighting control.
        self.control = DS8Control(self.capEvent, self.motorQueue)

        # Motor turning process.
        self.driverprocess = MotorDriver(self.capEvent, self.motExitEvent,
                                         self.motorQueue, self.connectionLock,
                                         self.svUpdateFrame, self.svSendStop)

        # Make connections.
        self.imgSocket = socket(AF_INET, SOCK_STREAM)
        self.imgSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.imgSocket.bind(('0.0.0.0', 8000))
        self.imgSocket.listen(0)
        self.ctrlSocket = socket(AF_INET, SOCK_STREAM)
        self.ctrlSocket.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
        self.ctrlSocket.bind(('0.0.0.0', 8001))
        self.ctrlSocket.listen(0)

        # Initiation of connections with the client program.
        self.setupConns(self.imgSocket, self.ctrlSocket)

        # Connection command reading thread.
        self.ctrlReader = StreamReader(config.ctrlConn, self.mainExitEvent)
       
        # Thread for sending images.
        self.imgSendThread = ImageStreamer(self.connectionLock, self.mainExitEvent)

    # Make connections with the client program.
    def setupConns(self, imgSocket, ctrlSocket):
        info("Waiting for connection with the client...")
        config.imgConn = imgSocket.accept()[0].makefile("wb")
        config.ctrlConn = ctrlSocket.accept()[0].makefile("r")
        info("Client connection established")

    # Execution of commands from the client program.
    def processCmd(self, cmdstr):

        if not cmdstr:
            info("Empty command string")
            return 0
        cmdstr = cmdstr.replace("\n", "")
        info(cmdstr)
        cmd = cmdstr[0]
        setting = cmdstr[1:]

        # New image requested from the client program.
        if cmd == newImage:
            self.newImage()

        # Settings defined in the user interface.

        # Initial settings.

        # zoomDial            
        elif cmd == imageWidth:
            self.cam.width = int(setting)
            
        elif cmd == imageHeight:
            self.cam.height = int(setting)

        # zoomdial, roiUpButton, roiDownButton
        elif cmd == setY:
            self.cam.setY(int(setting))

        # zoomdial, roiLeftButton, roiRightButton
        elif cmd == setX:
            self.cam.setX(int(setting))

        # lightCheckbox
        elif cmd == lightOn:
            self.control.lightOn()

        elif cmd == lightOff:
            self.control.lightOff()

        # prevCheckBox
        elif cmd == previewOn:
            self.control.lightOn()
            self.sendLightOn()
            self.cam.mode = self.cam.previewing

        elif cmd == previewOff:
            self.control.lightOff()
            self.sendLightOff()
            self.cam.mode = self.cam.off            

        # fRevButton
        elif cmd == motorFrev:
            self.control.motorRev()

        # reverseButton
        elif cmd == motorRev:
            self.control.revFrame(1)

        # stopButton
        elif cmd == motorStop:
            self.control.motorStop()

        # forwardButton
        elif cmd == motorFwd:
            self.control.fwdFrame(1)

        # ffdButton
        elif cmd == motorFfd:
            self.control.motorFwd()

        # Camera settings.

        # analogueGainBox
        elif cmd == analogueGain:
            self.cam.picam2.controls.AnalogueGain = round(float(setting), 1)

        # EV
        elif cmd == expComp:            
            self.cam.picam2.controls.ExposureValue = round(float(setting), 1)

        # awbBox
        elif cmd == awbMode:
            awb = int(setting)
            self.cam.setAwbMode(awb)

        # blueGainSlider - blueGainBox
        elif cmd == gainBlue:
            self.cam.fixGains(1, round(float(setting), 2))

        # redGainSlider - redGainBox
        elif cmd == gainRed:
            self.cam.fixGains(0, round(float(setting), 2))

        # brightnessSlider - brightnessBox
        elif cmd == brightness:
            self.cam.picam2.controls.Brightness = round(float(setting), 2)

        # contrastSlider - contrastBox
        elif cmd == contrast:
            self.cam.picam2.controls.Contrast = round(float(setting), 2)

        # saturationSlider - saturationBox
        elif cmd == saturation:
            self.cam.picam2.controls.Saturation = round(float(setting), 2)

        # quitButton
        elif cmd == clientQuit:
            self.exit()

        # Capture.

        # bracketingBox
        elif cmd == bracketingShots:
            self.cam.bracketing = int(setting)

        # stopsBox
        elif cmd == bracketingStops:
            self.cam.stops = round(float(setting), 1)

        # captureTestBtn
        elif cmd == testPhoto:
            self.autoAdvance = False
            self.svSendStop.value = 0
            self.control.lightOn()
            self.sendLightOn()
            self.cam.mode = self.cam.capturing
            sleep(0.5)
            # Take and send a single photo.
            self.newImage()
            self.control.lightOff()
            self.sendLightOff()

        # autoExpCheckBox
        elif cmd == autoexpOn:            
            self.cam.autoExp = True
            # Automatic exposure is activated.
            self.cam.picam2.controls.AeEnable = True

        elif cmd == autoexpOff:
            self.cam.autoExp = False
            # Automatic exposure is disabled.
            self.cam.picam2.controls.AeEnable = False
            self.cam.picam2.controls.AnalogueGain = 1

        # timeExpBox
        elif cmd == fixExposure:
            self.cam.ManExposureTime = int(float(setting) * 1000)

        # frameLcd
        elif cmd == updateFrame:
            self.svUpdateFrame.value = 1

        elif cmd == noUpdateFrame:
            self.svUpdateFrame.value = 0

        # activateMotorCheckBox
        elif cmd == activateMotor:
            self.control.motorWake()

        elif cmd == deactivateMotor:
            self.control.motorSleep()

        # captureFrmRev10 - captureFrmRev - gotoCheckBox
        elif cmd == capFrameRev:
            # self.autoAdvance = False
            num = int(setting) if setting else 1
            self.control.revFrame(num)

        # captureFrmAdv10 - captureFrmAdv - gotoCheckBox
        elif cmd == capFrameAdv:
            # self.autoAdvance = False
            num = int(setting) if setting else 1
            self.control.fwdFrame(num)

        # captureStopBtn - capturePauseBtn pressed
        elif cmd == stopCapture:
            # self.autoAdvance = False
            self.cam.mode = self.cam.off
            self.control.lightOff()
            self.sendLightOff()

        # captureStartBtn - capturePauseBtn released
        elif cmd == startCapture:
            self.svSendStop.value = 0
            self.control.lightOn()
            self.sendLightOn()
            self.cam.startCaptureMode()
            self.autoAdvance = True
            self.newImage()

        # Advanced settings.

        # vflipCheckBox
        elif cmd == vflipOn:
            self.cam.picam2.stop()
            self.cam.picam2.still_configuration.transform.vflip = True
            self.cam.picam2.configure("still")
            self.cam.picam2.start()
        elif cmd == vflipOff:
            self.cam.picam2.stop()
            self.cam.picam2.still_configuration.transform.vflip = False
            self.cam.picam2.configure("still")
            self.cam.picam2.start()

        # hflipCheckBox
        elif cmd == hflipOn:
            self.cam.picam2.stop()
            self.cam.picam2.still_configuration.transform.hflip = True
            self.cam.picam2.configure("still")
            self.cam.picam2.start()
        elif cmd == hflipOff:
            self.cam.picam2.stop()
            self.cam.picam2.still_configuration.transform.hflip = False
            self.cam.picam2.configure("still")
            self.cam.picam2.start()

        # jpgCheckBox
        elif cmd == jpgOn:
            self.cam.captureJpg = True
        
        elif cmd == jpgOff:
            self.cam.captureJpg = False

        # rawCheckBox
        elif cmd == rawOn:            
            self.cam.captureRaw = True            
          
        elif cmd == rawOff:
            self.cam.captureRaw = False

        # constraintModeBox
        elif cmd == constraintMode:
            self.cam.setConstraintMode(int(setting))

        # exposureModeBox
        elif cmd == exposureMode:
            self.cam.setExposureMode(int(setting))

        # meteringModeBox
        elif cmd == meteringMode:
            self.cam.setMeteringMode(int(setting))

        # resolutionBox
        elif cmd == setSize:
            self.cam.setSize(int(setting))

        # sharpnessBox
        elif cmd == setSharp:
            self.cam.picam2.controls.Sharpness = round(float(setting), 1)

        # Engine stop signal sending is activated.
        elif cmd == sendStop:
            self.svSendStop.value = 1

    # Function to take and send photos at the request of the client program.
    def newImage(self):       

        if self.cam.mode == self.cam.previewing:
            
            if not self.cam.autoExp:            
                self.cam.picam2.controls.ExposureTime = self.cam.ManExposureTime
            
            imgflag = "p"
            self.takeAndQueuePhoto(imgflag)
            
            if self.cam.autoExp:
                # Automatic exposure data is sent.
                self.sendSS("e")            

            info("Taken preview image. " + self.exposureInfo())

        elif self.cam.mode == self.cam.capturing:            
            
            if self.cam.autoExp:
                # Calculation of automatic exposure.
                self.calcExpParmsAE()
                self.cam.exposureTime = self.cam.AeExposureTime
                # Automatic exposure data is sent.
                self.sendSS("e")                   
            else:
                # Manual exposure time.
                self.cam.exposureTime = self.cam.ManExposureTime

            self.cam.picam2.controls.ExposureTime = self.cam.exposureTime

            # This loop serves to ensure the stop of the motor and avoid
            # vibrations.
            while self.capEvent.is_set():
                sleep(0.1)

            if self.cam.captureRaw:
                if not self.cam.autoExp:
                    # Se envían datos de exposición.
                    self.sendSS("f")
                
                imgflag = "d"
                self.takeAndQueueDng(imgflag)
                info("Raw dng image taken. " + self.exposureInfo())

                # This additional image is taken to be displayed in the
                # client's image window.
                if not self.cam.captureJpg:
                    imgflag = "D"
                    self.takeAndQueuePhoto(imgflag)                               

            if self.cam.captureJpg:                

                for shot in range(1, self.cam.bracketing + 1):

                    bracketExposure = self.bracketSS(self.cam.stops, shot,
                                                    self.cam.bracketing,
                                                    self.cam.exposureTime)

                    self.cam.picam2.controls.ExposureTime = bracketExposure

                    # The new exposure time is stabilized.
                    self.stabExpTime(bracketExposure)                    

                    # Exposure data is sent.
                    self.sendSS("f")                    

                    imgflag = ("s" if self.cam.bracketing == 1 else "a"
                                if shot < self.cam.bracketing else "b")

                    self.takeAndQueuePhoto(imgflag)

                    if imgflag == "s":
                        info("Single image taken. " + self.exposureInfo())

                    elif imgflag == "a":
                        info("Bracketing image taken. " + self.exposureInfo())

                    elif imgflag == "b":
                        info("Last bracketing image taken. "
                              + self.exposureInfo())            
           
            if self.autoAdvance:

                # Sending the signal to advance one frame.
                self.control.fwdFrame(1)

        self.imgcount += 1
        info("Sent image " + str(self.imgcount))

    # Take and send a dng file.
    def takeAndQueueDng(self, imgflag):        
        
        # The new exposure time is stabilized.
        if not self.cam.autoExp:
            self.stabExpTime(self.cam.exposureTime)
        
        # Raw image is captured.
        request = self.cam.picam2.capture_request()
        
        request.save_dng("file.dng")       
        
        request.release()
        
        # Sending flag.
        self.imgSendThread.imgflag = imgflag.encode()
        
        # Sending dng file.
        with open("file.dng", "rb") as dngFile:
            self.imgSendThread.stream.write(dngFile.read())
        
        # Sending the exposure time.
        self.imgSendThread.exposureTime = self.cam.captureMetadata().ExposureTime
        
        # Thread start.
        self.imgSendThread.event.set()        

    # Take and send a image.
    def takeAndQueuePhoto(self, imgflag):

        if self.cam.mode == self.cam.capturing:
            jpegQuality = self.jpegQualityCap

        elif self.cam.mode == self.cam.previewing:
            jpegQuality = self.jpegQualityPr

        self.cam.picam2.options["quality"] = jpegQuality
        
        # Sending flag.
        self.imgSendThread.imgflag = imgflag.encode()
        
        # Capture the jpg image.
        self.cam.picam2.capture_file(self.imgSendThread.stream, format="jpeg")
        
        # Sending blue and red gains.
        if self.cam.awb:
            self.sendGains()
            
        # Sending the exposure time.
        self.imgSendThread.exposureTime = self.cam.captureMetadata().ExposureTime
        
        # Thread start.
        self.imgSendThread.event.set()         

    # Function for calculating automatic exposure parameters.
    def calcExpParmsAE(self):        
        
        # ScalerCrop is set for automatic exposure.
        self.cam.picam2.controls.ScalerCrop = config.AEScalerCrop
        
        # Reset exposure time.
        self.cam.picam2.controls.ExposureTime = 0
        
        # Automatic exposure is activated.
        self.cam.picam2.controls.AeEnable = True               
        
        # Waiting time to reach auto exposure convergence.        
        sleep(config.AEWaitFrames * self.cam.captureMetadata().FrameDuration * 1e-6)        
        
        oldAeExposureTime = self.cam.captureMetadata().ExposureTime
        
        retries = 0
        while True:
            convergence = True
            for i in range(10):
                retries += 1
                newAeExposureTime = self.cam.captureMetadata().ExposureTime
                if abs(oldAeExposureTime - newAeExposureTime) > config.timeExpTolerance:
                   oldAeExposureTime = newAeExposureTime
                   convergence = False
                   break
            if convergence:
                break
            
        self.cam.AeExposureTime =  newAeExposureTime
        info("Autoexposure time = " + str(self.cam.AeExposureTime) + 
             " us\n" + " "*29 +
             "Analogue gain = " + 
             str(self.cam.captureMetadata().AnalogueGain))
        
        # info("Number of retries = " + str(retries))
        
        # ScalerCrop is restored.
        self.cam.picam2.controls.ScalerCrop = self.cam.ScalerCrop       

        # Auto exposure is cancelled.
        self.cam.picam2.controls.AeEnable = False

    # This function calculates the exposure time for a certain number of
    # bracketing shots and a certain value of the step.
    def bracketSS(self, stops, shot, bkt, ss):

        if bkt == 1:
            return ss
        else:
            # Provides a range of evenly spaced values between -1 and 1.
            # So if bkt = 1, is [-1,1] if 3, is [-1,0,1],
            # if 4 is [-1,-1/3,1/3,1], and so on.
            adj = (float(shot - 1) / float(bkt - 1) * 2) - 1

            exposureTime = int(ss * 2**(adj * stops / 2))

            if exposureTime > self.cam.maxExpTime:
                exposureTime = self.cam.maxExpTime
            if exposureTime < self.cam.minExpTime:
                exposureTime = self.cam.minExpTime

            return exposureTime
        
    # This function is used to stabilize the exposure time requested from the
    # camera.
    def stabExpTime(self, time):
      # This loop has the function of ensuring that the camera uses
      # the new exposure time.

      numOfRetries = 0

      for i in range(config.numOfRetries):
          numOfRetries += 1
          metadataExposureTime = self.cam.captureMetadata().ExposureTime
          dif = abs(time - metadataExposureTime)
          # info("Theoretical exposure time = " +
          #       str(time) + " us\n" + " "*29 +
          #       "Camera real time = " +
          #       str(metadataExposureTime) + " us\n" + " "*29 +
          #       "Difference = " + str(dif) + " us")
          if  dif <= config.timeExpTolerance:
              break

      # info("Number of retries = " + str(numOfRetries))
        

    # Sending the exposure time and analog and digital gains of the camera.
    def sendSS(self, flag):

        self.cam.metadata = self.cam.captureMetadata()
        self.cam.frameRate = 1e+6 / self.cam.metadata.FrameDuration

        with self.connectionLock:
            # Flag e to point out that it is not an image, but exposure data.
            config.imgConn.write(flag.encode())
            config.imgConn.write(pack("<l", self.cam.metadata.ExposureTime))
            config.imgConn.write(pack("<f", round(self.cam.metadata.AnalogueGain, 2)))
            config.imgConn.write(pack("<f", round(self.cam.metadata.DigitalGain, 2)))
            config.imgConn.write(pack("<f", round(self.cam.frameRate, 1)))
            config.imgConn.flush()

    # Sending the gains of the blue and red.
    def sendGains(self):

        self.cam.metadata = self.cam.captureMetadata()

        gblue = self.cam.metadata.ColourGains[1]
        gred = self.cam.metadata.ColourGains[0]

        with self.connectionLock:
            # Flag g to point out that it is not an image, but color gain data.
            config.imgConn.write("g".encode())
            config.imgConn.write(pack("<f", gblue))
            config.imgConn.write(pack("<f", gred))
            config.imgConn.flush()

        gblue = round(gblue, 2)
        gred = round(gred, 2)

        info("Gains data sent to the client: " +
             "blue = " + str(gblue) + ", " + "red = " + str(gred))
    
    # Sending notice light on.
    def sendLightOn(self):
        with self.connectionLock:
            config.imgConn.write("l".encode())
            config.imgConn.flush()

    # Sending notice light off.
    def sendLightOff(self):
        with self.connectionLock:
            config.imgConn.write("L".encode())
            config.imgConn.flush()

    def exposureInfo(self):

        self.cam.metadata = self.cam.captureMetadata()

        strExpInfo = ("Exp. time = " + str(self.cam.metadata.ExposureTime) +
                      " us - Framerate = "
                      + str(round(float(self.cam.frameRate), 1))
                      + " fps - AG = "
                      + str(round(float(self.cam.metadata.AnalogueGain), 2))
                      + " - DG = "
                      + str(round(float(self.cam.metadata.DigitalGain), 2)))
                      

        return strExpInfo

    # This function serves to inform the client that he must close the
    # application either due to keyboard interruption or other type of
    # exception.
    def infExitClient(self):
        # The client is informed.
        # Flag X signal is sent -> application exit.
        with self.connectionLock:
            config.imgConn.write("X".encode())
            config.imgConn.flush()

   # Server shutdown function.
    def exit(self):
        # Signal is sent flag T -> terminate imgThread on client.
        with self.connectionLock:
            config.imgConn.write("T".encode())
            config.imgConn.flush()

        # Stop the engine, turn off the light, release the GPIO port.
        self.control.cleanup()

        info("Coming out...")

        # Event is triggered to stop the main loop and the threads reading
        # orders and sending images.
        self.mainExitEvent.set()

        # Event to stop the engine process.
        self.motExitEvent.set()

        # Finish motor turning process.
        self.driverprocess.join()

        # Close camera.
        self.cam.mode = self.cam.off
        self.cam.picam2.stop()
        self.cam.picam2.close()        

        # Close connections.
        if config.imgConn:
            config.imgConn.flush()
            config.imgConn.close()
        if config.ctrlConn:
            config.ctrlConn.flush()
            config.ctrlConn.close()

        # Time is allowed for the client to close connections.
        sleep(2)

        if self.imgSocket:
            self.imgSocket.shutdown(SHUT_RDWR)
            self.imgSocket.close()
        if self.ctrlSocket:
            self.ctrlSocket.shutdown(SHUT_RDWR)
            self.ctrlSocket.close()

        info("Released client connections")
        info("All connections closed")
        info("Finalized")

    # Main loop of the server program.

    def run(self):
        try:
            while not self.mainExitEvent.is_set():
                data = self.ctrlReader.readline(1)
                if data:
                    self.processCmd(data)

        # Keyboard interrupt.
        except KeyboardInterrupt:
            info("Keyboard interrupt")
            self.infExitClient()
            self.exit()

        except Exception as e:
            info(getattr(e, 'message', repr(e)))
            self.infExitClient()
            self.exit()


# This class is used to send images to the client program.
class ImageStreamer(Thread):

    def __init__(self, connLock, exitEvent):
        super(ImageStreamer, self).__init__()
        self.daemon = True
        self.connLock = connLock        
        self.stream = BytesIO()
        self.event = Event()
        self.exitEvent = exitEvent
        self.imgflag = "s".encode()
        self.exposureTime = 1000
        self.start()

    # Main loop. Runs in a separate thread.
    def run(self):
        while not self.exitEvent.is_set():
            # Waiting for an image to be written to the stream.
            if self.event.wait():
                try:
                    with self.connLock:
                        self.sendFile(self.imgflag, self.exposureTime,
                                      self.stream)
                finally:
                    self.event.clear()                    

    def sendFile(self, flag, exposureTime, stream):
        config.imgConn.write(flag)
        config.imgConn.write(pack("<i", exposureTime))
        size = stream.tell()        
        config.imgConn.write(pack("<L", size))
        config.imgConn.flush()
        stream.seek(0)
        config.imgConn.write(stream.read())
        stream.seek(0)
        stream.truncate()


# This class is used for the continuous reading of the orders coming from the
# client program.
class StreamReader(Thread):

    def __init__(self, stream, exitEvent):
        super(StreamReader, self).__init__()
        self.daemon = True
        self.stream = stream
        self.que = Cola()
        self.exitEvent = exitEvent
        self.start()

    # Main reading loop.
    def run(self):
        info("Executing command reading thread")
        try:
            while not self.exitEvent.is_set():
                    line = self.stream.readline()
                    if line:
                        self.que.put(line)

        except Exception as e:
            info(getattr(e, 'message', repr(e)))

        finally:
            info("End of command reading thread")

    def readline(self, time=None):
        try:
            return self.que.get(block=True, timeout=time)

        except Empty:
            return None


# Starting the server program.

if __name__ == "__main__":

    # Severity level of the log set to INFO.
    basicConfig(stream=stdout, level=INFO, format="%(asctime)s - %(levelname)s"
                " - %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    info("DSuper8 server software ver. 20231130")

    info("Starting")

    # DSuper8 server.
    server = DS8Server()

    # Starting the motor control process.
    server.driverprocess.start()

    # Server startup.
    server.run()

    # Program exit.
    exit()
