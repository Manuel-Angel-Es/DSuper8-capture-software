"""
DSuper8 project based on Joe Herman's rpi-film-capture.

Software modified by Manuel Ángel.

User interface redesigned by Manuel Ángel.

config.py: Configuration module and global variables of the client software.

Last version: 20230430.
"""


from PyQt6.QtCore import QFile, QIODeviceBase

from numpy import float32, fromstring, uint8, ndarray

from cv2 import imdecode, IMREAD_COLOR

from logging import info

# Configuration variables.

# IP address of the server.
server_ip = "HAL9004.maodog.es"
# server_ip = "192.168.1.15"

# Examples of directories for Linux and Windows are included.
# Comment those that do not apply.

# Base directory for configuration files and capture folder.
defaultFolder = "/home/mao/Super8"
# defaultFolder = "C:/Users/mao/Super8"

# Directory where the generated image files will be saved.
capFolder = "/home/mao/Super8"
# capFolder = "C:/Users/mao/Super8"

# File to save settings.
configFile = "/home/mao/Super8/DSuper8.conf"
# configFile = "C:/Users/mao/Super8/DSuper8.conf"

# Camera custom color gains.
# They must be determined for the lamp that we are using in our device.
# customGains = (red gain, blue gain)
customGains = (2.56, 2.23)

# Name assigned to our lamp.
customLampName = "3300 K"

# Path to resource folder.
resourcesPath = ""

# Monitor H resolution. Used to position the UI.
monitorRes = 1920

# The title of the image window can be anything.
imgWinTitle = "DSuper8"

# Maximum camera exposure time.
# It has been set to 1000000 us.
camMaxExpTime = 1000000

# Image Window Geometry.
# The size of the window does not affect the size of the capture images.
imgWinWidth = 864
imgWinX = 20
imgWinHeight = 648
imgWinY = 10

# Maximum dimensions of the final image. It is applied in the scaling of the
# captured image.
imgCapFinalW = 1920
imgCapFinalH = 1080

# We await these measurements of the sharpness index before considering it valid.
valSharp = 15

# Global variables of the client software.

# Preview images indicator.
prevOn = False

# Test image indicator.
testImg = False

# Capture indicator.
captureOn = False

# Latest system state.
# It is used in the image window naming.
# P -> Preview
# T -> Test
# C -> Capture
lastMode = ""

# Socket for sending commands to the server.
ctrlConn = False

# Film position. Frame number from the first.
frameNumber = 1

# Limit number of frames to digitize.
frameLimit = 3600

# Image file naming index.
fileNumber = 1

# Image number received from server.
numImgRec = 1

# Dimensions of the image initially captured by the camera, once the cutouts
# have been applied. Obtained in the imageResize function of DS8ImgThread.
imgCapIniW = 2028
imgCapIniH = 1520

# Dimensions of the resulting image once scaled. Obtained in the displayImg
# function of DS8ImgDialog.
imgCapResW = 1920
imgCapResH = 1080

# Variable that determines whether bracketing images from HDR algorithms are
# saved individually.
saveBracketImg = False

# Percentiles to be used in the HDR Mertens algorithm.
MertPercHigh = 100
MertPercLow = 0

# Exposure time matrix used by the HDR Debevec algorithm.
exposureTimes = ndarray([], dtype=float32)

# HDR image creation algorithm.
# It can be Mertens or Debevec.
blender = "Mertens"

# Tone mapping algorithm.
# It can be Simple, Reinhard, Drago or Mantiuk.
toneMap = "Simple"

# Parameters apply in the Simple tone mapping algorithm.
SimpleGamma = 1.0

# Parameters apply in Reinhard's tone mapping algorithm.
ReinhardGamma = 1.0
ReinhardIntensity = 0.0
ReinhardLight = 0.0
ReinhardColor = 1.0

# Parameters apply in the Drago tone mapping algorithm.
DragoGamma = 1.0
DragoSaturation = 0.0
DragoBias = 0.85

# Parameters apply in the Mantiuk tone mapping algorithm.
MantiukGamma = 1.0
MantiukSaturation = 0.0
MantiukScale = 0.85

# Indicator for activating the rounding of the image angles.
roundcorns = False

# Indicator for activating the histogram window.
showHist = True

# Indicator to make the Y axis of the histogram with a logarithmic scale.
logarithmHist = False

# Indicator to show the sharpness index in preview images.
showSharp = True

# Number of sharpness index measurements made.
numMeasSharp = 0

# Maximum value reached by the sharpness index.
maxSharpness = 0

# Indicator for activating image rotation.
rotation = False

# Image rotation angle.
rotationValue = 0.0

# Indicator for activating the cropping of the image margins.
cropping = False

# Image crop (pixels).
cropT = 0
cropL = 0
cropR = 0
cropB = 0

# Denotes whether the motor is in motion or at rest.
# Repose -> True - Movement -> False
motorNotMoving = True

# Function for reading images from file.
# Used for reading images from the Resources directory.


def readImgFromFile(file):
    global resourcesPath
    imgFile = QFile(resourcesPath + file)
    if imgFile.open(QIODeviceBase.OpenModeFlag.ReadOnly):
        cvimg = imdecode(fromstring(imgFile.readAll(), dtype=uint8),
                         IMREAD_COLOR)
        imgFile.close()
        return cvimg
    else:
        info("File " + file + " not found in Resources folder")
        return None
