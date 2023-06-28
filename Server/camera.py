"""
DSuper8 project based on Joe Herman's rpi-film-capture.

Software modified by Manuel Ángel.

User interface redesigned by Manuel Ángel.

camera.py: Camera configuration.

Latest version: 20230430.
"""

from picamera2 import Picamera2, Metadata

from time import sleep

from logging import info

class DS8Camera():
    off = 0
    previewing = 1
    capturing = 2

    # Resolutions supported by the camera.
    resolutions = [(2028, 1520), (4056, 3040)]

    def __init__(self):

        tuningfile = Picamera2.load_tuning_file("imx477_scientific.json")
        self.picam2 = Picamera2(tuning=tuningfile)

        # Configured resolution.
        self.resolution = self.resolutions[0]

        # Geometry of the zone of interest to be captured by the camera.

        # Coordinates of the upper left corner.
        self.x_offset = 0
        self.y_offset = 0

        # Zoom value. Determines the width and height of the zone of interest.
        # Values between 0.4 and 1. They are given by the zoom control.
        self.roiZ = 1

        # Width of the image.
        self.width = self.resolution[0] * self.roiZ

        # Height of the image.
        self.height = self.resolution[1] * self.roiZ

        # Automatic exposure.
        self.autoExp = False

        # Automatic white balance.
        self.awb = False

        # Number of bracketed exposures.
        self.bracketing = 1

        # Stop points.
        self.stops = 0

        # Manual exposure time.
        self.ManExposureTime = 2500

        # Automatic exposure time.
        self.AeExposureTime = 2500

        # Actual exposure time requested from the camera.
        self.exposureTime = 2500
        
        # Minimum exposure time. It is fixed at 10 us.
        self.minExpTime = 10

        # Maximum camera exposure time.
        # According to technical specifications of the camera, it can reach a
        # maximum of 670.74 s.
        # For our application we will set it to 1 s.
        self.maxExpTime = 1000000        

        # Metadata of the captured images.
        self.metadata = None

        # Camera capture speed in fps.
        self.frameRate = 10

        # Camera settings.
        # These settings are applied with the camera disabled.
        # It's not possible modify them with the camera active.

        # Allocate a single buffer.
        self.picam2.still_configuration.buffer_count = 1

        # Flip the image vertically
        self.picam2.still_configuration.transform.vflip = True
        self.picam2.still_configuration.transform.hflip = False

        # No images in preview.
        self.picam2.still_configuration.display = None

       # No streams are encoded.
        self.picam2.still_configuration.encode = None

        # Color space.
        # This feature is automatically configured by Picamera2.

        # Noise reduction:
        # This feature is automatically configured by Picamera2.

        # Duration time of the frames.
        self.picam2.still_configuration.controls.FrameDurationLimits = (self.minExpTime, self.maxExpTime)

        # Dimensions of the captured image.
        self.picam2.still_configuration.main.size = self.resolutions[0]

        # Image format 24 bits per pixel, ordered [R, G, B].
        self.picam2.still_configuration.main.format = ("RGB888")

        # Unknown parameters.
        # Default configuration.
        self.picam2.still_configuration.main.stride = None
        # self.picam2.still_configuration.framesize = None
        self.picam2.still_configuration.lores = None
        self.picam2.still_configuration.raw = None

        # Do not allow queuing images.
        # The captured image corresponds to the moment of the capture order.
        # To queue images the buffer_count parameter must be greater than 1.
        self.picam2.still_configuration.queue = False

        # Loading still image settings.
        self.picam2.configure("still")

        # Camera controls. These parameters can be changed with the
        # camera working.

        # AeEnable:
        # AEC: Automatic Exposure Control.
        # AGC: Automatic Gain Control.
        # False: Algoritm AEC/AGC disabled.
        # True: Algoritm AEC/AGC enabled.
        self.picam2.controls.AeEnable = False
        
        # This variable gives error "Control AEConstraintMode is not advertised by libcamera".
        # However, with the camera started it can be referenced normally. 
        # AEConstraintMode:
        # 0: Normal. Normal metering.
        # 1: Highlight. Meter for highlights.
        # 2: Shadows. Meter for shadows.
        # 3: Custom. User-defined metering.
        # self.picam2.controls.AEConstraintMode = 0

        # AeExposureMode:
        # 0: Normal. Normal exposures.
        # 1: Short. Use shorter exposures.
        # 2: Long. Use longer exposures.
        # 3: Custom. Use custom exposures.
        self.picam2.controls.AeExposureMode = 0

        # AeMeteringMode:
        # 0: CentreWeighted. Centre weighted metering.
        # 1: Spot. Spot metering.
        # 2: Matrix. Matrix metering.
        # 3: Custom. Custom metering.
        self.picam2.controls.AeMeteringMode = 0

        # ExposureTime: value between 0 and 1000000 us
        self.picam2.controls.ExposureTime = 4000

        # NoiseReductionMode: configuration parameter.

        # FrameDurationLimits: configuration parameter.

        # ColourCorrectionMatrix

        # Saturation: value between 0.0 and 32.0. Default 1.0.
        self.picam2.controls.Saturation = 1.0

        # Brightness: value between -1 and 1. Default 0.0.
        self.picam2.controls.Brightness = 0.0

        # Contrast: value between 0.0 and 32.0. Default 1.0.
        self.picam2.controls.Contrast = 1.0

        # ExposureValue: value between -8.0 and 8.0. Default 0.0.
        self.picam2.controls.ExposureValue = 0

        # AwbEnable:
        # AWB: Auto white balance.
        # False: Algoritm AWB disabled.
        # True: Algoritm AWB enabled.
        self.picam2.controls.AwbEnable = True

        # AwbMode:
        # 0: Auto. Any illumant.
        # 1: Incandescent. Incandescent lighting.
        # 2: Tungsten. Tungsten lighting.
        # 3: Fluorescent. Fluorescent lighting.
        # 4: Indoor. Indoor illumination.
        # 5: Daylight. Daylight illumination.
        # 6: Cloudy. Cloudy illumination.
        # 7: Custom. Custom setting.
        self.picam2.controls.AwbMode = 0

        # ScalerCrop:
        self.picam2.controls.ScalerCrop = (0, 0, 4056, 3040)

        # AnalogueGain: value between 1.0 and 16.0.
        self.picam2.controls.AnalogueGain = 1.0

        # ColourGains: value between 0.0 and 32.0
        self.customGains = (2.56, 2.23)
        self.picam2.controls.ColourGains = self.customGains

        # Sharpness: value between 0.0 and 16.0. Default 1.0.
        self.picam2.controls.Sharpness = 1.0

        self.mode = self.off

        # Starting up the camera.
        self.picam2.start()

        sleep(1)

    # Initial settings.

    # zoomDial

    def setZ(self, value):
        self.roiZ = float(value) / 1000

        self.x_offset = int(self.resolutions[1][0] * (1 - self.roiZ) / 2)
        self.y_offset = int(self.resolutions[1][1] * (1 - self.roiZ) / 2)

        self.width = int(self.resolutions[1][0] * self.roiZ)
        self.height = int(self.resolutions[1][1] * self.roiZ)

        self.picam2.controls.ScalerCrop = (self.x_offset, self.y_offset,
                                           self.width, self.height)

    # roiUpButton - roiDownButton
    def setY(self, value):
        self.y_offset = value
        self.picam2.controls.ScalerCrop = (self.x_offset, self.y_offset,
                                           self.width, self.height)

    # roiLeftButton - roiRightButton
    def setX(self, value):
        self.x_offset = value
        self.picam2.controls.ScalerCrop = (self.x_offset, self.y_offset,
                                           self.width, self.height)

    # Camera settings.

    # awbBox
    def setAwbMode(self, idx):

        if idx < 7:
            self.awb = True
            self.picam2.controls.AwbEnable = self.awb
            self.picam2.controls.AwbMode = idx
        else:
            self.awb = False
            self.picam2.controls.AwbEnable = self.awb

        if idx == 0:
            mode = "auto"
        elif idx == 1:
            mode = "incandescent lighting"
        elif idx == 2:
            mode = "tungsten lighting"
        elif idx == 3:
            mode = "fluorescent lighting"
        elif idx == 4:
            mode = "indoor lighting"
        elif idx == 5:
            mode = "daylight"
        elif idx == 6:
            mode = "cloudy"
        elif idx == 7:
            mode = "custom lighting"
        elif idx == 8:
            mode = "manual"
        else:
            return

        info("Adjusted white balance " + mode)

    # blueGainBox, redGainBox
    def fixGains(self, idx, value):

        self.metadata = self.captureMetadata()

        if (idx == 0):
            gred = value
            gblue = round(self.metadata.ColourGains[1], 2)

        elif (idx == 1):
            gred = round(self.metadata.ColourGains[0], 2)
            gblue = value

        self.picam2.controls.ColourGains = (gred, gblue)

        sleep(0.2)

        info("Camera color gains: blue = " + str(gblue) + ", red = " + str(gred))
             
    # Capture.

    # captureStartBtn
    def startCaptureMode(self):
        sleep(1)
        self.mode = self.capturing
        info("Camera in capture mode")

    # Advanced settings.

    # constraintModeBox
    def setConstraintMode(self, idx):
        self.picam2.controls.AeConstraintMode = idx        

        if idx == 0:
            mode = "normal"
        elif idx == 1:
            mode = "highlight"
        elif idx == 2:
            mode = "shadows"
        else:
            return

        info("Adjusted auto exposure restriction " + mode)

    # exposureModeBox
    def setExposureMode(self, idx):
        self.picam2.controls.AeExposureMode = idx
        
        if idx == 0:
            mode = "normal"
        elif idx == 1:
            mode = "sort exposures"
        elif idx == 2:
            mode = "long exposures"
        else:
            return

        info("Adjusted auto exposure mode " + mode)

    # meteringModeBox
    def setMeteringMode(self, idx):
        self.picam2.controls.AeMeteringMode = idx
        
        if idx == 0:
            mode = "centre weighted"
        elif idx == 1:
            mode = "spot"
        elif idx == 2:
            mode = "matrix"
        else:
            return

        info("Adjusted auto exposure metering mode " + mode)

    # resolutionBox
    def setSize(self, idx):
        self.picam2.stop()
        self.picam2.still_configuration.main.size = self.resolutions[idx]
        self.picam2.configure("still")
        self.picam2.start()
        if idx == 0:
            resol = "2028x1520 px"
        elif idx == 1:
            resol = "4056x3040 px"

        info("Camera resolution " + resol)

    # This function is used to capture the metadata of the images.
    def captureMetadata(self):
        metadata = Metadata(self.picam2.capture_metadata())

        return metadata
