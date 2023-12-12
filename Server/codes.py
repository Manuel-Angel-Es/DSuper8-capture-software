"""
DSuper8 project based on Joe Herman's rpi-film-capture.

Software modified by Manuel Ángel.

User interface redesigned by Manuel Ángel.

codes.py: Codes used for client-server communication.

Latest version: 20231130.
"""

# Initial settings

# zoomDial
imageWidth = "1"
imageHeight = "2"

# roiUpButton - roiDownButton
setY = "7"

# roiLeftButton - roiRightButton
setX = "8"

# lightCheckbox
lightOn = "l"
lightOff = "L"

# prevCheckBox
previewOn = "p"
previewOff = "P"

# startPosCheckBox
updateFrame = "u"
noUpdateFrame = "U"

# fRevButton
motorFrev = ","

# reverseButton
motorRev = "<"

# stopButton
motorStop = "~"

# forwardButton
motorFwd = ">"

# ffdButton
motorFfd = "."

# Camera settings

# analogueGainBox
analogueGain = "I"

# EVBox
expComp = "e"

# awbBox
awbMode = "w"

# awbManualBtn
fixGains = "W"

# blueGainBox
gainBlue = "b"

# redGainBox
gainRed = "r"

# brightnessBox
brightness = "y"

# saturationBox
saturation = "s"

# contrastBox
contrast = "k"

# quitButton
clientQuit = "0"

# Capture

# bracketingBox
bracketingShots = "f"

# captureTestBtn
testPhoto = "t"

# stopsBox
bracketingStops = "F"

# autoExpCheckBox
autoexpOn = "4"
autoexpOff = "$"

# timeExpBox
fixExposure = "x"

# activateMotorCheckBox
activateMotor = "a"
deactivateMotor = "A"

# captureFrmRev10 - captureFrmRev
capFrameRev = ":"

# captureFrmAdv - captureFrmAdv10
capFrameAdv = ";"

# captureStopBtn - capturePauseBtn pressed
stopCapture = "O"

# captureStartBtn - capturePauseBtn released
startCapture = "o"
newImage = "n"

# activate engine stop signal
sendStop = "q"

# Advanced settings

# vFlipCheckBox
vflipOn = "v"
vflipOff = "V"

# hFlipCheckBox
hflipOn = "h"
hflipOff = "H"

# jpgCheckBox
jpgOn = "j"
jpgOff = "J"

# rawCheckBox
rawOn = "d"
rawOff = "D"

# constraintModeBox
constraintMode = "T"

# exposureModeBox
exposureMode = "E"

# meteringModeBox
meteringMode = "M"

# resolutionBox
setSize = "Z"

# sharpnessBox
setSharp = "S"
