"""
DSuper8 project based on Joe Herman's rpi-film-capture.

Software modified by Manuel Ángel.

User interface redesigned by Manuel Ángel.

DS8Dialogs.py: Module for the visualization of the captured images, calculation
               and visualization of the histogram and management of the
               graphical user interface.

Last version: 20230430.
"""

from PyQt6.QtGui import QImage, QPaintEvent, QPainter, QIcon

from PyQt6.QtCore import Qt

from PyQt6.QtWidgets import QDialog, QFileDialog, QMessageBox, QApplication

from threading import Event

from numpy import array, zeros, float32, uint8, fromstring

from cv2 import split, calcHist, cvtColor, COLOR_BGR2RGB

from matplotlib import use

use("Qt5Agg")

import matplotlib.pyplot as plt

from time import sleep

from pathlib import Path

from glob import glob

from logging import info

from configparser import Error

# Our own modules.

import config

import DS8Config

from codes import *

# Main dialog class, created with Qt Designer and translated into Python using
# pyuic6.
from ui_DSuper8 import *


# This class is used to display the images sent by the server.
class DS8ImgDialog(QDialog):
    def __init__(self, parent=None):
        super(DS8ImgDialog, self).__init__(parent)
        self.icon = QIcon(config.resourcesPath + "DSuper8Icon.png")
        self.setWindowIcon(self.icon)
        # The close button is removed from the window.
        self.setWindowFlags(Qt.WindowType.Window
                            | Qt.WindowType.WindowTitleHint
                            | Qt.WindowType.WindowMinimizeButtonHint
                            | Qt.WindowType.WindowMaximizeButtonHint)
        self.move(10, 10)
        self.setWindowTitle(config.imgWinTitle)
        self.mQImage = None
        self.displayImgEvent = Event()

        # Images reading and treatment thread.
        self.imgthread = None

    def displayImg(self, cvimg, title):
        #info("Viewing image")
        self.setWindowTitle("Image: " + title)
        self.cvImage = cvtColor(cvimg, COLOR_BGR2RGB)
        h, w, byteValue = self.cvImage.shape
        config.imgCapResH = h
        config.imgCapResW = w
        byteValue = byteValue * w
        imgwinh = config.imgWinHeight
        imgwinw = int((imgwinh / h) * w)
        if imgwinw > config.imgWinWidth:
            imgwinw = config.imgWinWidth
            imgwinh = int((imgwinw / w) * h)

        self.resize(imgwinw, imgwinh)
        self.mQImage = QImage(self.cvImage, w, h, byteValue,
                              QImage.Format.Format_RGB888)
        self.update()

    def paintEvent(self, QPaintEvent):
        #info("paintEvent called")
        painter = QPainter()
        painter.begin(self)
        if self.mQImage:
            painter.drawImage(0, 0, QImage.scaled(self.mQImage, self.width(),
                              self.height(),
                              Qt.AspectRatioMode.KeepAspectRatio))
        painter.end()
        self.displayImgEvent.set()

    def setupThreadingUpdates(self, imgthread):
        info("Setting up thread updates for the image window")
        self.imgthread = imgthread
        self.imgthread.displayImgSig.connect(self.displayImg)
        self.displayImgEvent = self.imgthread.displayImgEvent


# This class is used to display the histograms corresponding to the images
# sent by the server.
class DS8Histogram():
    def __init__(self):

        self.xnpa = array(range(256))
        self.b_ynpa = zeros(256, dtype=float32)
        self.g_ynpa = zeros(256, dtype=float32)
        self.r_ynpa = zeros(256, dtype=float32)

        plt.rcParams["toolbar"] = "None"
        plt.rcParams["axes.facecolor"] = "#EAEAEB"
        plt.rcParams["axes.edgecolor"] = "k"
        plt.rcParams["xtick.color"] = "k"
        plt.rcParams["ytick.color"] = "k"
        self.fig = plt.figure(num=None, figsize=(4.8, 3.6), dpi=100,
                              facecolor="#EAEAEB", edgecolor="#EAEAEB")
        self.icon = QIcon(config.resourcesPath + "DSuper8Icon.png")
        self.fig.canvas.parent().setWindowIcon(self.icon)
        self.fig.canvas.parent().setWindowTitle("Histograma")
        # The close button is removed from the window.
        self.fig.canvas.parent().setWindowFlags(Qt.WindowType.Window
                                    | Qt.WindowType.WindowTitleHint
                                    | Qt.WindowType.WindowMinimizeButtonHint
                                                | Qt.WindowType.WindowMaximizeButtonHint)

        self.mngr = plt.get_current_fig_manager()

        self.plot = plt.subplot(111)
        plt.ion()
        plt.show()

    def plotHistogram(self, cvimg, title):
        #info("plotHistogram called")

        self.fig.canvas.parent().setWindowTitle("Histogram: " + title)

        bgr_planes = split(cvimg)

        histSize = 256
        histRange = (0, 256)
        accumulate = False

        b_hist = calcHist(bgr_planes, [0], None, [histSize], histRange,
                          accumulate=accumulate)
        g_hist = calcHist(bgr_planes, [1], None, [histSize], histRange,
                          accumulate=accumulate)
        r_hist = calcHist(bgr_planes, [2], None, [histSize], histRange,
                          accumulate=accumulate)

        for i in range(256):
            self.b_ynpa[i] = b_hist[i][0]
            self.g_ynpa[i] = g_hist[i][0]
            self.r_ynpa[i] = r_hist[i][0]

        # Delete old chart.
        self.plot.cla()

        # Set x-axis limits.
        self.plot.set_xlim([0, 255])

        # Set logarithmic scale on y-axis.
        if config.logarithmHist:
            plt.yscale("log", nonpositive="clip")

        # Make the new chart.
        plt.plot(self.xnpa, self.b_ynpa, linewidth=1, color="blue")
        plt.plot(self.xnpa, self.g_ynpa, linewidth=1, color="green")
        plt.plot(self.xnpa, self.r_ynpa, linewidth=1, color="red")

        self.fig.canvas.draw_idle()

    # Close the histogram window.
    def closeHist(self):
        #info("Closing the histogram called")
        plt.close(self.fig)


# Main dialog class for displaying and managing the user interface, created
# with Qt Designer.
class DS8Dialog(QDialog, Ui_DSuper8):
    def __init__(self, parent=None):
        super(DS8Dialog, self).__init__(parent)
        self.setupUi(self)
        self.icon = QIcon(config.resourcesPath + "DSuper8Icon.png")
        self.setWindowIcon(self.icon)
        self.move(config.monitorRes - 10 - self.width(), 10)
        self.config = DS8Config.DS8ConfigParser()
        self.configFile = Path(config.configFile)
        self.histograma = DS8Histogram()
        self.plotHistogramEvent = Event()
        self.plotHistogramEvent.set()

        # The name assigned to the lamp of our device is personalized.
        self.awbBox.setItemText(7, config.customLampName)

        # Reading thread and treatment of images.
        self.imgthread = None

        # Geometry of the area of interest to be captured by the camera.

        # Image size captured by the camera.
        self.imgCapW = 2028
        self.imgCapH = 1520

        # Full HQ camera sensor resolution.
        self.fullResW = 4056
        self.fullResH = 3040

        # Image size after zooming, measured in pixels with respect to the
        # maximum resolution of the sensor.
        self.imgZoomW = 4056
        self.imgZoomH = 3040

        # Coordinates of the upper left corner measured in pixels with respect
        # to the maximum resolution of the sensor.
        self.x_offset = 0
        self.y_offset = 0

        # Zoom value. Determines the width and height of the area of interest.
        # Values between 400 and 1000. They are given by the zoom control.
        self.roiZ = 1000

        # Scrolling the region of interest each time a button is pressed.
        self.deltaRoi = 10

        # Blue and red gain for manual white balance adjustment HQ camera.
        self.manualBlueGain = 2.23
        self.manualRedGain = 2.56

        # Manual exposure time.
        self.manExpTime = 0.0

        # Auto exposure time.
        self.autoExpTime = 0.0

        # Indicates that the file naming index is out of sync with the position
        # of the movie.
        self.dirty = True

        # Last image viewed.
        # Initializes with Splash image.
        self.lastShowImg = config.readImgFromFile("DSuper8Splash.jpg")

        # Title of the last image viewed.
        self.lastShowTitle = "Splash"

        # Capture folder is determined.
        self.capFolderBox.setText(config.capFolder.strip())

        # This variable indicates whether the exitApp() function has been
        # executed.
        self.exitAppCalled = False

    # This function is used to send control sequences to the server.
    def sendCtrl(self, cmd):
        info("CTRL: " + cmd)
        config.ctrlConn.write(cmd + "\n")
        config.ctrlConn.flush()

    # Configuring connections to UI update from imgthread.
    def setupThreadingUpdates(self, imgthread):

        self.imgthread = imgthread

        # Frame number indicator update signal.
        self.imgthread.updateFrameNumSig.connect(self.updateFrameNum)

        # Automatic exposure data update signal.
        self.imgthread.updateAESig.connect(self.updateSSAE)

        # Exposure data update signal.
        self.imgthread.updateSSSig.connect(self.updateSS)

        # Red and blue gains data update signal.
        self.imgthread.updateGainsSig.connect(self.updateGains)

        # Image window refresh signal.
        self.imgthread.displayImgSig.connect(self.takenImg)

        # Histogram window refresh signal.
        self.imgthread.plotHistogramSig.connect(self.updateHistogram)

        # Engine stopped information signal.
        self.imgthread.motorStoppedSig.connect(self.motorStopped)

        # Illumination status information signal.
        self.imgthread.lightSig.connect(self.updateLightCheckbox)

        # Last frame reached information signal.
        self.imgthread.endCaptureSig.connect(self.captureEnd)

        # Enable capture widgets information signal.
        self.imgthread.enableCaptureWidgetsSig.connect(self.enableCaptureWidgets)

        # Output signal reported by server.
        self.imgthread.exitSig.connect(self.exitApp)

        # Displayed histogram information event.
        self.plotHistogramEvent = self.imgthread.plotHistogramEvent

    # This function is used to send the UI settings to the server.
    # Sent at startup.
    def sendInitConfig(self):

        # Zoom dial setting.
        self.sendCtrl(setZ + str(self.zoomDial.value()))

        # Setting the region of interest.
        self.sendCtrl(setX + str(self.x_offset))
        self.sendCtrl(setY + str(self.y_offset))

        # Lighting control.
        if self.lightCheckbox.isChecked():
            self.sendCtrl(lightOn)
        else:
            self.sendCtrl(lightOff)

        # White balance.
        self.setAWBmode(self.awbBox.currentIndex())

        # Brightness adjustment.
        self.sendCtrl(brightness + str(self.brightnessBox.value()))

        # Contrast adjustment.
        self.sendCtrl(contrast + str(self.contrastBox.value()))

        # Saturation adjustment.
        self.sendCtrl(saturation + str(self.saturationBox.value()))

        # Adjustment bracketing exposures.
        self.setBlend(self.bracketingBox.value())
        self.setBlendStops(self.stopsBox.value())

        # Manual exposure time adjustment.
        self.sendCtrl(fixExposure + str(self.timeExpBox.value()))

        # Auto exposure control.
        if self.autoExpCheckBox.isChecked():
            self.setAutoExp(True)

        else:
            self.setAutoExp(False)
            # Analog gain adjustment.
            self.setAnalogueGain(self.analogueGainBox.value())

        # Vertical and horizontal flip.
        self.setVFlip(self.vFlipCheckBox.isChecked())
        self.setHFlip(self.hFlipCheckBox.isChecked())

        # Black and white image.
        if self.bwCheckBox.isChecked():
            self.saturationBox.setValue(0.0)
        else:
            self.saturationBox.setValue(1.0)

        # Capture resolution.
        self.setCapRes(self.resolutionBox.currentIndex())

        # Sharpness adjustment.
        self.setSharpness(self.sharpnessBox.value())

    # Post-capture settings.
    def initPostCapture(self):

        # Show histogram.
        if self.showHist.isChecked():
            self.initHistogram(True)
            # Y axis of the histogram logarithmic.
            if self.logarithmHist.isChecked():
                self.mklogHist(True)
            else:
                self.mklogHist(False)

        # Round corners.
        if self.roundCorns.isChecked():
            self.setRoundCorns(True)
        else:
            self.setRoundCorns(False)

        # Rotate image.
        if self.rotationCheckBox.isChecked():
            self.setRotation(True)
        else:
            self.setRotation(False)

        # Crop image edges.
        if self.croppingCheckBox.isChecked():
            self.setCrop(True)
        else:
            self.setCrop(False)

        self.setHDRAlgorithm(False)
        self.setToneMapAlgorithm(False)

    # Slots connected to the signals generated by the UI.

    # Setup.

    # zoomDial
    def setZoom(self, zoomval):

        self.roiZ = zoomval

        self.imgZoomW = int(self.fullResW * self.roiZ / 1000)
        self.imgZoomH = int(self.fullResH * self.roiZ / 1000)

        self.x_offset = int((self.fullResW - self.imgZoomW) / 2)
        self.y_offset = int((self.fullResH - self.imgZoomH) / 2)

        if self.roiZ == 1000:
            self.roiUpButton.setEnabled(False)
            self.roiLeftButton.setEnabled(False)
            self.roiRightButton.setEnabled(False)
            self.roiDownButton.setEnabled(False)
        elif self.roiZ != 1000 and config.prevOn:
            self.roiUpButton.setEnabled(True)
            self.roiLeftButton.setEnabled(True)
            self.roiRightButton.setEnabled(True)
            self.roiDownButton.setEnabled(True)

        self.sendCtrl(setZ + str(self.roiZ))

        # Sharpness measurement reset.
        config.numMeasSharp = 0
        config.maxSharpness = 0

        self.updateStatus("Zoom level set")

    # roiUpButton
    def setRoiYUp(self):
        # Vertical image offset measured in pixels.
        shift = 0
        if self.y_offset > self.deltaRoi:
            shift = self.deltaRoi

        else:
            shift = self.y_offset
            self.roiUpButton.setEnabled(False)

        self.y_offset -= shift

        if self.y_offset + self.imgZoomH < self.fullResH:
            self.roiDownButton.setEnabled(True)

        self.sendCtrl(setY + str(self.y_offset))

        # Sharpness measurement reset.
        config.numMeasSharp = 0
        config.maxSharpness = 0

        self.updateStatus("ROI shifted up")

    # roiLeftButton
    def setRoiXLeft(self):
        # Horizontal image offset measured in pixels.
        shift = 0
        if self.x_offset > self.deltaRoi:
            shift = self.deltaRoi

        else:
            shift = self.x_offset
            self.roiLeftButton.setEnabled(False)

        self.x_offset -= shift

        if self.x_offset + self.imgZoomW < self.fullResW:
            self.roiRightButton.setEnabled(True)

        self.sendCtrl(setX + str(self.x_offset))

        # Sharpness measurement reset.
        config.numMeasSharp = 0
        config.maxSharpness = 0

        self.updateStatus("ROI shifted to the left")

    # roiRightButton
    def setRoiXRight(self):
        # Horizontal image offset measured in pixels.
        shift = 0
        remaind = self.fullResW - self.x_offset - self.imgZoomW
        if remaind > self.deltaRoi:
            shift = self.deltaRoi

        else:
            shift = remaind
            self.roiRightButton.setEnabled(False)

        self.x_offset += shift

        if self.x_offset > 0:
            self.roiLeftButton.setEnabled(True)

        self.sendCtrl(setX + str(self.x_offset))

        # Sharpness measurement reset.
        config.numMeasSharp = 0
        config.maxSharpness = 0

        self.updateStatus("ROI shifted to the right")

    # roiDownButton
    def setRoiYDown(self):
        # Vertical image offset measured in pixels.
        shift = 0
        remaind = self.fullResH - self.y_offset - self.imgZoomH
        if remaind > self.deltaRoi:
            shift = self.deltaRoi

        else:
            shift = remaind
            self.roiDownButton.setEnabled(False)

        self.y_offset += shift

        if self.y_offset > 0:
            self.roiUpButton.setEnabled(True)

        self.sendCtrl(setY + str(self.y_offset))

        # Reinicio de las medidas de nitidez.
        config.numMeasSharp = 0
        config.maxSharpness = 0

        self.updateStatus("ROI shifted down")

    # lightCheckbox
    def lightSet(self, isOn):
        if isOn:
            self.sendCtrl(lightOn)
            self.updateStatus("Light on")
        else:
            self.sendCtrl(lightOff)
            self.updateStatus("Light off")

    # prevCheckBox
    def previewSet(self, isOn):
        if isOn:
            config.lastMode = "P"
            config.prevOn = True
            config.testImg = False
            config.captureOn = False

            # Sharpness measurement reset.
            config.numMeasSharp = 0
            config.maxSharpness = 0

            self.sendCtrl(previewOn)

            # Enable preview controls.
            self.zoomDial.setEnabled(True)
            if self.zoomDial.value() != 1000:
                self.roiUpButton.setEnabled(True)
                self.roiLeftButton.setEnabled(True)
                self.roiRightButton.setEnabled(True)
                self.roiDownButton.setEnabled(True)
            self.vFlipCheckBox.setEnabled(True)
            self.hFlipCheckBox.setEnabled(True)
            self.bwCheckBox.setEnabled(True)
            if self.autoExpCheckBox.isChecked():
                self.constraintModeLabel.setEnabled(True)
                self.constraintModeBox.setEnabled(True)
                self.exposureModeLabel.setEnabled(True)
                self.exposureModeBox.setEnabled(True)
                self.meteringModeLabel.setEnabled(True)
                self.meteringModeBox.setEnabled(True)
            self.resolutionLabel.setEnabled(True)
            self.resolutionBox.setEnabled(True)
            self.sharpnessLabel.setEnabled(True)
            self.sharpnessBox.setEnabled(True)
            self.sharpCheckBox.setEnabled(True)
            self.roundCorns.setEnabled(True)
            self.rotationCheckBox.setEnabled(True)
            if self.rotationCheckBox.isChecked():
                self.rotationBox.setEnabled(True)
            self.croppingCheckBox.setEnabled(True)
            if self.croppingCheckBox.isChecked():
                self.cropTopLabel.setEnabled(True)
                self.cropTopBox.setEnabled(True)
                self.cropLeftLabel.setEnabled(True)
                self.cropLeftBox.setEnabled(True)
                self.cropRightLabel.setEnabled(True)
                self.cropRightBox.setEnabled(True)
                self.cropBottomLabel.setEnabled(True)
                self.cropBottomBox.setEnabled(True)

            # Disable controls.
            self.captureTestBtn.setEnabled(False)
            self.captureStartBtn.setEnabled(False)
            self.capturePauseBtn.setEnabled(False)
            self.loadConfigButton.setEnabled(False)

            # Disable exit button.
            self.quitButton.setEnabled(False)

            # Request image from server avoiding imgThread blocking.
            self.sendCtrl(newImage)

            info("Waiting for image " + str(config.numImgRec))
            self.updateStatus("Preview images")

        else:
            config.prevOn = False
            self.sendCtrl(previewOff)
            self.loadConfigButton.setEnabled(True)

            # Disable preview controls.
            self.zoomDial.setEnabled(False)
            self.roiUpButton.setEnabled(False)
            self.roiLeftButton.setEnabled(False)
            self.roiRightButton.setEnabled(False)
            self.roiDownButton.setEnabled(False)
            self.vFlipCheckBox.setEnabled(False)
            self.hFlipCheckBox.setEnabled(False)
            self.bwCheckBox.setEnabled(False)
            self.constraintModeLabel.setEnabled(False)
            self.constraintModeBox.setEnabled(False)
            self.exposureModeLabel.setEnabled(False)
            self.exposureModeBox.setEnabled(False)
            self.meteringModeLabel.setEnabled(False)
            self.meteringModeBox.setEnabled(False)
            self.resolutionLabel.setEnabled(False)
            self.resolutionBox.setEnabled(False)
            self.sharpnessLabel.setEnabled(False)
            self.sharpnessBox.setEnabled(False)
            self.sharpCheckBox.setEnabled(False)
            self.roundCorns.setEnabled(False)
            self.rotationCheckBox.setEnabled(False)
            self.rotationBox.setEnabled(False)
            self.croppingCheckBox.setEnabled(False)
            self.cropTopLabel.setEnabled(False)
            self.cropTopBox.setEnabled(False)
            self.cropLeftLabel.setEnabled(False)
            self.cropLeftBox.setEnabled(False)
            self.cropRightLabel.setEnabled(False)
            self.cropRightBox.setEnabled(False)
            self.cropBottomLabel.setEnabled(False)
            self.cropBottomBox.setEnabled(False)

            # Activate Test and Start buttons.
            self.checkCaptureOK()

            if config.motorNotMoving:
                # Activate Exit button.
                self.quitButton.setEnabled(True)

    # startPosCheckBox
    def synchronizePositionIndicator(self, checked):

        filmPosition = int(self.frameLcd.value())

        if self.startPosCheckBox.isChecked():

            # We tell the server to send position update signals.
            self.sendCtrl(updateFrame)

            if filmPosition:
                config.fileNumber = filmPosition
                config.frameNumber = filmPosition
            else:
                config.fileNumber = 1
                config.frameNumber = 1
                self.frameLcd.display(1)

            self.dirty = False
            self.frameLcd.setStyleSheet("""QLCDNumber {background-color:
                                        rgb(245, 255, 172)}""")
            self.frameLcd.setEnabled(True)
            self.gotoCheckBox.setEnabled(True)
            self.passToCheckbox.setEnabled(True)
            self.nextFrameBox.setEnabled(True)
            self.frameLCDCountUpBtn.setEnabled(True)
            self.frameLCDCountDownBtn.setEnabled(True)
            self.captureFrmRev10.setEnabled(True)
            self.captureFrmRev.setEnabled(True)
            self.captureFrmAdv.setEnabled(True)
            self.captureFrmAdv10.setEnabled(True)

            # Activate Test and Start buttons.
            self.checkCaptureOK()

            filmPosition = int(self.frameLcd.value())

            if filmPosition == 1:
                self.updateStatus("Film in initial position")

            elif filmPosition > 1:
                self.updateStatus("Set position of the film")
        else:

            # We tell the server not to send position update signals.
            self.sendCtrl(noUpdateFrame)

            config.fileNumber = 0
            config.frameNumber = 0
            self.dirty = True
            self.captureTestBtn.setEnabled(False)
            self.frameLcd.setStyleSheet("""QLCDNumber {background-color:
                                        rgb(241, 241, 236)}""")
            self.frameLcd.setEnabled(False)
            self.frameLcd.display(0)
            self.gotoCheckBox.setEnabled(False)
            self.passToCheckbox.setEnabled(False)
            self.nextFrameBox.setEnabled(False)
            self.frameLCDCountUpBtn.setEnabled(False)
            self.frameLCDCountDownBtn.setEnabled(False)
            self.captureFrmRev10.setEnabled(False)
            self.captureFrmRev.setEnabled(False)
            self.captureFrmAdv.setEnabled(False)
            self.captureFrmAdv10.setEnabled(False)
            self.captureStartBtn.setEnabled(False)
            self.updateStatus("Film is not in initial position")

    # fRevButton
    def motorfrev(self):
        # Motor is activated.
        self.activateMotorCheckBox.setChecked(True)
        self.sendCtrl(motorFrev)
        if self.startPosCheckBox.isChecked():
            self.dirty = True
        config.motorNotMoving = False

        # Sharpness measurement reset.
        config.numMeasSharp = 0
        config.maxSharpness = 0

        self.updateStatus("Continuous reverse motor")
        self.stopButton.setEnabled(True)
        self.disableButtons()

    # reverseButton
    def motorRev(self):
        # Motor is activated.
        self.activateMotorCheckBox.setChecked(True)
        self.sendCtrl(motorRev)
        if self.startPosCheckBox.isChecked():
            self.dirty = True
        config.motorNotMoving = False

        # Sharpness measurement reset.
        config.numMeasSharp = 0
        config.maxSharpness = 0

        self.updateStatus("1 frame reverse")
        self.stopButton.setEnabled(False)
        self.disableButtons()

    # stopButton
    def motorStop(self):
        self.sendCtrl(motorStop)
        self.updateStatus("Engine stop")
        # The self.enableButtons() function is called when the motorStoppedSig
        # signal is received.

    # forwardButton
    def motorFwd(self):
        # Motor is activated.
        self.activateMotorCheckBox.setChecked(True)
        self.sendCtrl(motorFwd)
        if self.startPosCheckBox.isChecked():
            self.dirty = True
        config.motorNotMoving = False

        # Sharpness measurement reset.
        config.numMeasSharp = 0
        config.maxSharpness = 0

        self.updateStatus("1 frame advance")
        self.stopButton.setEnabled(False)
        self.disableButtons()

    # ffdButton
    def motorffd(self):
        # Motor is activated.
        self.activateMotorCheckBox.setChecked(True)
        self.sendCtrl(motorFfd)
        if self.startPosCheckBox.isChecked():
            self.dirty = True
        config.motorNotMoving = False

        # Sharpness measurement reset.
        config.numMeasSharp = 0
        config.maxSharpness = 0

        self.updateStatus("Continuous advance motor")
        self.stopButton.setEnabled(True)
        self.disableButtons()

    # configFileBox
    def checkconfigFileBox(self, text):
        # Text is checked.
        if not self.configFileBox.text():
            self.saveConfigButton.setEnabled(False)
        else:
            self.saveConfigButton.setEnabled(True)

    # loadConfigButton
    def loadConfig(self):
        # Self.config is restarted.
        for section in self.config.sections():
            self.config.remove_section(section)

        # Configuration file selection dialog.
        fileDialog = QFileDialog()
        fileDialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        fileDialog.setWindowTitle("Select configuration file")
        fileDialog.setDirectory(config.defaultFolder)
        filtros = ["*.conf"]
        fileDialog.setNameFilters(filtros)

        if fileDialog.exec():
            self.configFile = Path(fileDialog.selectedFiles()[0])

        else:
            return

        if self.configFile.is_file():
            configError = False
            info("Reading " + str(self.configFile) + " configuration file")

            try:
                self.config.read([self.configFile])
                if not self.config.validateConfigFile():
                    raise Error

            except Error:
                # Pop-up message if there are errors loading the configuration
                # file.
                msgBox = QMessageBox()
                msgBox.setWindowTitle("Invalid configuration file")
                msgBox.setIcon(QMessageBox.Icon.Warning)
                msgBox.setText(str(self.configFile) +
                               " is not a valid configuration file")
                msgBox.addButton("Accept", QMessageBox.ButtonRole.AcceptRole)

                msgBox.exec()

                configError = True
                info(str(self.configFile) + " is not a valid configuration file")

        else:
            configError = True
            info("Configuration file " + str(self.configFile) +
                 " does not exist")

        if not configError:
            self.config.updateUIfromConfig(self)
            self.configFileBox.setText(str(self.configFile))
            info(str(self.configFile) + " configuration file loaded")

            self.updateStatus("Configuration file loaded")

        # Setting the region of interest.
        # You have to send the configuration because it does not have a slot.
        self.sendCtrl(setX + str(self.x_offset))
        self.sendCtrl(setY + str(self.y_offset))

        # Maximum allowed clipping is updated.
        self.setMaxCrop()

    # saveConfigButton
    def saveCurrentConfig(self):
        if self.configFile.is_file():
            self.config.updateConfigFromUI(self)
            with open(self.configFile, "w") as savefile:
                self.config.write(savefile)
            self.updateStatus("Configuration file saved")

        else:
            self.saveConfig()

    # saveAsButton
    def saveConfig(self):
        fileDialog = QFileDialog()
        fileDialog.setFileMode(QFileDialog.FileMode.AnyFile)
        fileDialog.setWindowTitle("Configuration file - Save as")
        fileDialog.setDirectory(config.defaultFolder)
        filtros = ["*.conf"]
        fileDialog.setNameFilters(filtros)

        if fileDialog.exec():
            self.configFile = fileDialog.selectedFiles()[0]

            if not self.configFile.endswith(".conf"):
                self.configFile += ".conf"

            self.configFile = Path(self.configFile)

        else:
            return

        self.config.updateConfigFromUI(self)
        with open(self.configFile, "w") as savefile:
            self.config.write(savefile)
        self.configFileBox.setText(str(self.configFile))
        self.saveConfigButton.setEnabled(True)
        self.updateStatus("Configuration file saved")

    # Camera settings.

    # analogueGainBox
    def setAnalogueGain(self, value):
        value = round(value, 1)
        self.sendCtrl(analogueGain + str(value))
        self.gainBoxA.setValue(value)

        # Sharpness measurement reset.
        config.numMeasSharp = 0
        config.maxSharpness = 0

        self.updateStatus("Set analog gain")

    # EVBox
    def setEV(self, value):
        value = round(value, 1)
        self.sendCtrl(expComp + str(value))

        # Sharpness measurement reset.
        config.numMeasSharp = 0
        config.maxSharpness = 0

        self.updateStatus("Set exposure value")

    # awbBox
    # White balance for HQ camera.
    def setAWBmode(self, idx):
        self.sendCtrl(awbMode + str(idx))

        self.setColorsEnabled(False)
        self.blueGainSlider.blockSignals(True)
        self.blueGainBox.blockSignals(True)
        self.redGainSlider.blockSignals(True)
        self.redGainBox.blockSignals(True)

        match idx:
            case 0:
                pass
            case 1:
                self.blueGainBox.setValue(2.37)
                self.blueGainSlider.setValue(237)
                self.redGainBox.setValue(2.35)
                self.redGainSlider.setValue(235)
            case 2:
                self.blueGainBox.setValue(2.30)
                self.blueGainSlider.setValue(230)
                self.redGainBox.setValue(2.39)
                self.redGainSlider.setValue(239)
            case 3:
                self.blueGainBox.setValue(1.75)
                self.blueGainSlider.setValue(175)
                self.redGainBox.setValue(2.95)
                self.redGainSlider.setValue(295)
            case 4:
                self.blueGainBox.setValue(2.30)
                self.blueGainSlider.setValue(230)
                self.redGainBox.setValue(2.39)
                self.redGainSlider.setValue(239)
            case 5:
                self.blueGainBox.setValue(1.26)
                self.blueGainSlider.setValue(126)
                self.redGainBox.setValue(3.80)
                self.redGainSlider.setValue(380)
            case 6:
                self.blueGainBox.setValue(1.21)
                self.blueGainSlider.setValue(121)
                self.redGainBox.setValue(3.66)
                self.redGainSlider.setValue(366)
            case 7:
                self.blueGainBox.blockSignals(False)
                self.redGainBox.blockSignals(False)
                self.blueGainBox.setValue(config.customGains[1])
                self.redGainBox.setValue(config.customGains[0])
                self.setColorsEnabled(False)
                self.blueGainBox.blockSignals(True)
                self.redGainBox.blockSignals(True)
            case 8:
                self.setColorsEnabled(True)
                self.blueGainSlider.blockSignals(False)
                self.blueGainBox.blockSignals(False)
                self.redGainSlider.blockSignals(False)
                self.redGainBox.blockSignals(False)
                self.blueGainBox.setValue(self.manualBlueGain)
                self.redGainBox.setValue(self.manualRedGain)

        # Sharpness measurement reset.
        config.numMeasSharp = 0
        config.maxSharpness = 0

        self.updateStatus("Set white balance")

    def setColorsEnabled(self, enable):
        self.blueLabel.setEnabled(enable)
        self.blueGainSlider.setEnabled(enable)
        self.blueGainBox.setEnabled(enable)
        self.blueResetBtn.setEnabled(enable)
        self.redLabel.setEnabled(enable)
        self.redGainSlider.setEnabled(enable)
        self.redGainBox.setEnabled(enable)
        self.redResetBtn.setEnabled(enable)

    # awbManualBtn
    def awbManual(self):
        self.awbBox.setCurrentIndex(8)
        self.updateStatus("Manual white balance")

    # blueGainSlider
    def setGainBlueSlider(self, value):
        value = float(value)
        value /= 100
        value = round(value, 2)
        self.sendCtrl(gainBlue + str(value))
        self.blueGainBox.blockSignals(True)
        self.blueGainBox.setValue(value)
        self.blueGainBox.blockSignals(False)

        # Sharpness measurement reset.
        config.numMeasSharp = 0
        config.maxSharpness = 0

        self.updateStatus("Blue gain manual adjustment")

    # blueGainBox
    def setGainBlueBox(self, value):
        self.manualBlueGain = value
        self.sendCtrl(gainBlue + str(value))

        value *= 100
        value = int(value)
        self.blueGainSlider.blockSignals(True)
        self.blueGainSlider.setSliderPosition(value)
        self.blueGainSlider.blockSignals(False)

        # Sharpness measurement reset.
        config.numMeasSharp = 0
        config.maxSharpness = 0

        self.updateStatus("Blue gain manual adjustment")

    # blueResetBtn
    def resetGainBlue(self):
        self.blueGainBox.setValue(2.50)

        # Sharpness measurement reset.
        config.numMeasSharp = 0
        config.maxSharpness = 0

        self.updateStatus("Blue gain setting reset")

    # redGainSlider
    def setGainRedSlider(self, value):
        value = float(value)
        value /= 100
        value = round(value, 2)
        self.sendCtrl(gainRed + str(value))
        self.redGainBox.blockSignals(True)
        self.redGainBox.setValue(value)
        self.redGainBox.blockSignals(False)

        # Sharpness measurement reset.
        config.numMeasSharp = 0
        config.maxSharpness = 0

        self.updateStatus("Red gain manual adjustment")

    # redGainBox
    def setGainRedBox(self, value):
        self.manualRedGain = value
        self.sendCtrl(gainRed + str(value))
        value *= 100
        value = int(value)
        self.redGainSlider.blockSignals(True)
        self.redGainSlider.setSliderPosition(value)
        self.redGainSlider.blockSignals(False)

        # Sharpness measurement reset.
        config.numMeasSharp = 0
        config.maxSharpness = 0

        self.updateStatus("Red gain manual adjustment")

    # redResetBtn
    def resetGainRed(self):
        self.redGainBox.setValue(2.50)

        # Sharpness measurement reset.
        config.numMeasSharp = 0
        config.maxSharpness = 0

        self.updateStatus("Red gain setting reset")

    # brightnessSlider
    def setBrightnessSlider(self, value):
        value = float(value)
        value /= 100
        value = round(value, 2)
        self.sendCtrl(brightness + str(value))
        self.brightnessBox.blockSignals(True)
        self.brightnessBox.setValue(value)
        self.brightnessBox.blockSignals(False)

        # Sharpness measurement reset.
        config.numMeasSharp = 0
        config.maxSharpness = 0

        self.updateStatus("Brightness level set")

    # brightnessBox
    def setBrightnessBox(self, value):
        self.sendCtrl(brightness + str(value))

        value *= 100
        value = int(value)
        self.brightnessSlider.blockSignals(True)
        self.brightnessSlider.setSliderPosition(value)
        self.brightnessSlider.blockSignals(False)

        # Sharpness measurement reset.
        config.numMeasSharp = 0
        config.maxSharpness = 0

        self.updateStatus("Brightness level set")

    # resetBrightnessBtn
    def resetBrightness(self):
        self.brightnessBox.setValue(0.00)

        # Sharpness measurement reset.
        config.numMeasSharp = 0
        config.maxSharpness = 0

        self.updateStatus("Brightness level reset")

    # contrastSlider
    def setContrastSlider(self, value):
        value = float(value)
        value /= 100
        value = round(value, 2)
        self.sendCtrl(contrast + str(value))
        self.contrastBox.blockSignals(True)
        self.contrastBox.setValue(value)
        self.contrastBox.blockSignals(False)

        # Sharpness measurement reset.
        config.numMeasSharp = 0
        config.maxSharpness = 0

        self.updateStatus("Contrast level set")

    # contrastBox
    def setContrastBox(self, value):
        self.sendCtrl(contrast + str(value))

        value *= 100
        value = int(value)
        self.contrastSlider.blockSignals(True)
        self.contrastSlider.setSliderPosition(value)
        self.contrastSlider.blockSignals(False)

        # Sharpness measurement reset.
        config.numMeasSharp = 0
        config.maxSharpness = 0

        self.updateStatus("Contrast level set")

    # resetContrastBtn
    def resetContrast(self):
        self.contrastBox.setValue(1.00)

        # Sharpness measurement reset.
        config.numMeasSharp = 0
        config.maxSharpness = 0

        self.updateStatus("Contrast level reset")

    # saturationSlider
    def setSaturationSlider(self, value):
        value = float(value)
        value /= 100
        value = round(value, 2)
        self.sendCtrl(saturation + str(value))
        self.saturationBox.blockSignals(True)
        self.saturationBox.setValue(value)
        self.saturationBox.blockSignals(False)

        # Sharpness measurement reset.
        config.numMeasSharp = 0
        config.maxSharpness = 0

        self.updateStatus("Saturation level set")

    # saturationBox
    def setSaturationBox(self, value):
        self.sendCtrl(saturation + str(value))

        value *= 100
        value = int(value)
        self.saturationSlider.blockSignals(True)
        self.saturationSlider.setSliderPosition(value)
        self.saturationSlider.blockSignals(False)

        # Sharpness measurement reset.
        config.numMeasSharp = 0
        config.maxSharpness = 0

        self.updateStatus("Saturation level set")

    # resetSaturationBtn
    def resetSaturation(self):
        self.saturationBox.setValue(1.00)

        # Sharpness measurement reset.
        config.numMeasSharp = 0
        config.maxSharpness = 0

        self.updateStatus("Saturation level reset")

    # quitButton
    def quitApp(self):
        msgBox = QMessageBox()
        msgBox.setWindowTitle("Application exit")
        msgBox.setIcon(QMessageBox.Icon.Question)
        msgBox.setText(" " * 5 + "Exit application?" + " " * 25)
        acceptButton = msgBox.addButton("Accept",
                                        QMessageBox.ButtonRole.AcceptRole)
        rejectButton = msgBox.addButton("Cancel",
                                        QMessageBox.ButtonRole.RejectRole)

        msgBox.exec()
        if msgBox.clickedButton() == acceptButton:
            # We close the application.
            self.exitApp(False)

        else:
            return

    # Capture.

    # endFrameBox
    def setEndFrame(self, frame):
        config.frameLimit = frame
        self.updateStatus("Last frame to digitize: " +
                          str(config.frameLimit))

    # bracketingBox
    def setBlend(self, value):
        self.sendCtrl(bracketingShots + str(value))
        config.bracketing = value

        if value == 1:
            self.stopsBox.setEnabled(False)
            self.stopsBox.setValue(0.0)
            self.DS8tabWidget.setTabEnabled(4, False)
            self.setHDRAlgorithm(False)
            self.setToneMapAlgorithm(False)
            self.saveAllCheckBox.setChecked(False)
            self.saveAllCheckBox.setEnabled(False)

        else:
            config.exposureTimes.resize(value, refcheck=False)
            self.stopsBox.setEnabled(True)
            if self.stopsBox.value():
                self.DS8tabWidget.setTabEnabled(4, True)
                self.setHDRAlgorithm(False)
                self.setToneMapAlgorithm(False)
                self.saveAllCheckBox.setEnabled(True)

        # Activate Test and Start buttons.
        self.checkCaptureOK()

        self.updateStatus("Set number of photos per frame")

    # captureTestBtn
    def takeTestPhoto(self):
        config.lastMode = "T"
        config.prevOn = False
        config.testImg = True
        config.captureOn = False
        self.disableCaptureWidgets()
        self.sendCtrl(testPhoto)
        self.updateStatus("Taken test image")

    # saveAllCheckBox
    def saveBracketImg(self, checked):
        if checked:
            config.saveBracketImg = True
        else:
            config.saveBracketImg = False

    # stopsBox
    def setBlendStops(self, stops):
        self.sendCtrl(bracketingStops + str(stops))
        minExp = self.minExp(self.exposureBox.value())
        self.exposureBoxMin.setValue(minExp)
        maxExp = self.maxExp(self.exposureBox.value())
        self.exposureBoxMax.setValue(maxExp)

        if (stops and self.bracketingBox.value() > 1):
            self.DS8tabWidget.setTabEnabled(4, True)
            self.setHDRAlgorithm(False)
            self.setToneMapAlgorithm(False)
            self.saveAllCheckBox.setEnabled(True)

        else:
            self.DS8tabWidget.setTabEnabled(4, False)
            self.setHDRAlgorithm(False)
            self.setToneMapAlgorithm(False)
            self.saveAllCheckBox.setChecked(False)
            self.saveAllCheckBox.setEnabled(False)

        # Activate Test and Start buttons.
        self.checkCaptureOK()

        self.updateStatus("Set number of stop points")

    # autoExpCheckBox
    def setAutoExp(self, isOn):
        if isOn:
            self.sendCtrl(autoexpOn)

            # Manually set exposure time is saved for later use.
            self.manExpTime = self.timeExpBox.value()

            # Exposure compensation.
            self.sendCtrl(expComp + str(self.EVBox.value()))
            # Auto exposure restriction.
            self.setConstraintMode(self.constraintModeBox.currentIndex())
            # Auto exposure mode.
            self.setExposureMode(self.exposureModeBox.currentIndex())
            # Measurement mode.
            self.setMeteringMode(self.meteringModeBox.currentIndex())

            # Auto exposure controls are activated.
            self.enableAEWidgets()

            self.updateStatus("Set auto exposure")

        else:
            self.sendCtrl(autoexpOff)
            self.sendCtrl(fixExposure + str(self.manExpTime))

            # Auto exposure controls are disabled.
            self.disableAEWidgets()

            # We recover the manual exposure time.
            self.timeExpBox.setValue(self.manExpTime)

            self.timeExpLabel.setEnabled(True)
            self.timeExpBox.blockSignals(False)
            self.timeExpBox.setEnabled(True)

            if self.timeExpBox.value():
                self.exposureDownBtn.setEnabled(True)

            if (self.timeExpBox.value() < 1000.0):
                self.exposureUpBtn.setEnabled(True)

            # Multiple exposure data is updated.
            minExp = self.minExp(self.manExpTime)
            self.exposureBoxMin.setValue(minExp)
            self.exposureBox.setValue(self.manExpTime)
            maxExp = self.maxExp(self.manExpTime)
            self.exposureBoxMax.setValue(maxExp)

            self.updateStatus("Set manual exposure")

    # timeExpBox
    def setExposure(self, texp, updStat=True):

        texp = round(texp, 1)
        # Manually set exposure time is saved for later use.
        self.manExpTime = texp

        self.sendCtrl(fixExposure + str(texp))

        # Multiple exposure data is updated.
        minExp = self.minExp(texp)
        self.exposureBoxMin.setValue(minExp)
        self.exposureBox.setValue(texp)
        maxExp = self.maxExp(texp)
        self.exposureBoxMax.setValue(maxExp)

        if self.timeExpBox.value():
            self.exposureDownBtn.setEnabled(True)
        else:
            self.exposureDownBtn.setEnabled(False)

        if self.timeExpBox.value() < 1000.0:
            self.exposureUpBtn.setEnabled(True)
        else:
            self.exposureUpBtn.setEnabled(False)

        # Sharpness measurement reset.
        config.numMeasSharp = 0
        config.maxSharpness = 0

        if updStat:

            self.updateStatus("Set manual exposure")

    # exposureDownBtn
    def setExposureDown(self):
        texp = self.timeExpBox.value()
        texp *= 0.8
        texp = round(texp, 1)
        self.sendCtrl(fixExposure + str(texp))
        self.timeExpBox.setValue(texp)
        if self.timeExpBox.value():
            self.exposureDownBtn.setEnabled(True)
        if self.timeExpBox.value() < 1000.0:
            self.exposureUpBtn.setEnabled(True)

        # Sharpness measurement reset.
        config.numMeasSharp = 0
        config.maxSharpness = 0

        self.updateStatus("Decreased exposure time 20%")

    # exposureUpBtn
    def setExposureUp(self):
        texp = self.timeExpBox.value()
        texp *= 1.2
        texp = round(texp, 1)
        if texp > 1000.0:
            texp = 1000.0
        self.sendCtrl(fixExposure + str(texp))
        self.timeExpBox.setValue(texp)
        if self.timeExpBox.value():
            self.exposureDownBtn.setEnabled(True)
        if self.timeExpBox.value() >= 1000.0:
            self.exposureUpBtn.setEnabled(False)

        # Sharpness measurement reset.
        config.numMeasSharp = 0
        config.maxSharpness = 0

        self.updateStatus("Increased exposure time 20%")

    # capFolderBox
    def checkCaptureFolder(self, capFolder):
        # If the folder is valid, it is selected.
        capFolder = capFolder.strip()

        if capFolder and Path(capFolder).is_dir():
            config.capFolder = capFolder

            # Activate Test and Start buttons.
            self.checkCaptureOK()

            return

        # If it is not valid, it is tried with the folder indicated in the
        # global variables file config.py.

        elif (config.capFolder.strip() and
              Path(config.capFolder.strip()).is_dir()):
            self.capFolderBox.blockSignals(True)
            self.capFolderBox.setText(config.capFolder.strip())
            self.capFolderBox.blockSignals(False)

            # Activate Test and Start buttons.
            self.checkCaptureOK()

        # Finally, if it is not valid either, it is left blank and the user
        # must manually select the folder before starting to digitize.

        else:
            self.capFolderBox.blockSignals(True)
            self.capFolderBox.setText("Select capture folder")
            self.capFolderBox.blockSignals(False)
            config.capFolder = ""
            self.captureTestBtn.setEnabled(False)
            self.captureStartBtn.setEnabled(False)

    # chooseFolderBtn
    def chooseFolder(self):
        fileDialog = QFileDialog()
        fileDialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        fileDialog.setFileMode(QFileDialog.FileMode.Directory)
        fileDialog.setWindowTitle("Select capture folder")
        fileDialog.setDirectory(str(config.defaultFolder))
        filtros = ["Folders"]
        fileDialog.setNameFilters(filtros)

        if fileDialog.exec():

            self.capFolderBox.setText(fileDialog.selectedFiles()[0])

        else:
            return

    # activateMotorCheckBox
    def activateMotor(self, checked):
        if checked:
            self.sendCtrl(activateMotor)
            self.updateStatus("Motor on")

        else:
            self.sendCtrl(deactivateMotor)
            self.updateStatus("Motor off")

    # frameLCDCountUpBtn
    def positionIndicatorUp(self):
        if self.startPosCheckBox.isChecked():
            config.frameNumber += 1
            config.fileNumber = config.frameNumber
            self.dirty = False
            self.frameLcd.display(config.frameNumber)

    # frameLCDCountDownBtn
    def positionIndicatorDown(self):
        if self.startPosCheckBox.isChecked():
            config.frameNumber -= 1
            config.fileNumber = config.frameNumber
            self.dirty = False
            self.frameLcd.display(config.frameNumber)

    # gotoCheckBox
    def gotoFrameNumber(self, checked):
        if checked:
            numFrames = self.nextFrameBox.value() - config.frameNumber
            if numFrames > 0:
                # Motor is activated.
                self.activateMotorCheckBox.setChecked(True)
                self.sendCtrl(capFrameAdv + str(numFrames))
                self.dirty = True
                config.motorNotMoving = False

                # Sharpness measurement reset.
                config.numMeasSharp = 0
                config.maxSharpness = 0

                self.updateStatus("Forward to the frame " +
                                  str(self.nextFrameBox.value()))
                self.disableButtons()
                self.gotoCheckBox.setEnabled(True)

            elif numFrames < 0:
                numFrames *= -1
                # Motor is activated.
                self.activateMotorCheckBox.setChecked(True)
                self.sendCtrl(capFrameRev + str(numFrames))
                self.dirty = True
                config.motorNotMoving = False

                # Sharpness measurement reset.
                config.numMeasSharp = 0
                config.maxSharpness = 0

                self.updateStatus("Backward to the frame " +
                                  str(self.nextFrameBox.value()))
                self.disableButtons()
                self.gotoCheckBox.setEnabled(True)

            elif numFrames == 0:
                self.gotoCheckBox.setChecked(False)
                return

        else:

            if config.motorNotMoving:
                return
            else:
                self.sendCtrl(motorStop)
                self.updateStatus("Forward/Backward to the frame " +
                                  str(self.nextFrameBox.value()) +
                                  " cancelled")

    # passToCheckbox
    def passToLCDIndicator(self):
        frame = self.nextFrameBox.value()
        self.frameLcd.display(frame)
        config.frameNumber = frame
        config.fileNumber = frame
        self.passToCheckbox.setChecked(False)

    # nextFrameBox does not require slot.

    # captureFrmRev10
    def capFrameRev10(self):
        # Motor is activated.
        self.activateMotorCheckBox.setChecked(True)
        self.sendCtrl(capFrameRev + "10")
        self.dirty = True
        config.motorNotMoving = False

        # Sharpness measurement reset.
        config.numMeasSharp = 0
        config.maxSharpness = 0

        self.updateStatus("10 frame reverse")
        self.disableButtons()

    # captureFrmRev
    def capFrameRev(self):
        # Motor is activated.
        self.activateMotorCheckBox.setChecked(True)
        self.sendCtrl(capFrameRev)
        self.dirty = True
        config.motorNotMoving = False

        # Sharpness measurement reset.
        config.numMeasSharp = 0
        config.maxSharpness = 0

        self.updateStatus("1 frame reverse")
        self.disableButtons()

    # captureFrmAdv
    def capFrameAdv(self):
        # Motor is activated.
        self.activateMotorCheckBox.setChecked(True)
        self.sendCtrl(capFrameAdv)
        self.dirty = True
        config.motorNotMoving = False

        # Sharpness measurement reset.
        config.numMeasSharp = 0
        config.maxSharpness = 0

        self.updateStatus("1 frame advance")
        self.disableButtons()

    # captureFrmAdv10
    def capFrameAdv10(self):
        # Motor is activated.
        self.activateMotorCheckBox.setChecked(True)
        self.sendCtrl(capFrameAdv + "10")
        self.dirty = True
        config.motorNotMoving = False

        # Sharpness measurement reset.
        config.numMeasSharp = 0
        config.maxSharpness = 0

        self.updateStatus("10 frame advance")
        self.disableButtons()

    # captureStopBtn
    def captureEnd(self):
        config.captureOn = False
        self.captureStopBtn.setEnabled(False)
        self.capturePauseBtn.setEnabled(False)
        self.sendCtrl(stopCapture)
        self.updateStatus("Capture stopped")

    # captureStartBtn
    def captureStart(self):
        numImgFiles = len(glob(str(config.capFolder) + "/img*.jpg"))
        if numImgFiles:
            msgBox = QMessageBox()
            msgBox.setWindowTitle("Existing image files")
            msgBox.setIcon(QMessageBox.Icon.Question)
            msgBox.setText("The selected folder contains " +
                           str(numImgFiles) + " image files.")
            msgBox.setInformativeText("Overwrite existing files?")
            acceptButton = msgBox.addButton("Accept",
                                            QMessageBox.ButtonRole.AcceptRole)
            rejectButton = msgBox.addButton("Cancel",
                                            QMessageBox.ButtonRole.RejectRole)

            msgBox.exec()
            if msgBox.clickedButton() == rejectButton:
                return
        if (config.imgCapResW % 2):
            msgBox = QMessageBox()
            msgBox.setWindowTitle("Image dimensions error")
            msgBox.setIcon(QMessageBox.Icon.Warning)
            msgBox.setText("The width of the resulting image (" +
                           str(config.imgCapResW) +
                           " px) is not divisible by 2.")
            msgBox.setInformativeText("Width modification required.")
            acceptButton = msgBox.addButton("Accept",
                                            QMessageBox.ButtonRole.AcceptRole)

            msgBox.exec()
            if msgBox.clickedButton() == acceptButton:
                return

        # Motor is activated.
        self.activateMotorCheckBox.setChecked(True)

        # Start capture mode.
        config.lastMode = "C"
        config.prevOn = False
        config.testImg = False
        config.captureOn = True
        self.sendCtrl(startCapture)

        # Disable controls that affect capture.
        self.disableCaptureWidgets()

        info("Waiting for image " + str(config.numImgRec))
        self.updateStatus("Capture mode started")

    # capturePauseBtn
    def capturePause(self, pressed):
        if pressed:

            self.sendCtrl(stopCapture)
            self.captureStopBtn.setEnabled(False)
            self.updateStatus("Capture paused")

        else:

            # Restart capture mode.
            self.sendCtrl(startCapture)
            info("Waiting for image " + str(config.numImgRec))
            self.captureStopBtn.setEnabled(True)
            self.updateStatus("Capture mode restarted")

    # Advanced settings.

    # vFlipCheckBox
    def setVFlip(self, isOn):
        self.sendCtrl(vflipOn if isOn else vflipOff)
        self.updateStatus("Set vertical flip")

    # hFlipCheckBox
    def setHFlip(self, isOn):
        self.sendCtrl(hflipOn if isOn else hflipOff)
        self.updateStatus("Set horizontal flip")

    # bwCheckBox
    def setBW(self, isOn):
        if isOn:
            self.saturationBox.setValue(0)
            self.updateStatus("B/W image")
        else:
            self.saturationBox.setValue(1)
            self.updateStatus("Color image")

    # constraintModeBox
    def setConstraintMode(self, idx):

        self.sendCtrl(constraintMode + str(idx))

        # Sharpness measurement reset.
        config.numMeasSharp = 0
        config.maxSharpness = 0

        self.updateStatus("Auto exposure restriction set")

    # exposureModeBox
    def setExposureMode(self, idx):
        self.sendCtrl(exposureMode + str(idx))

        # Sharpness measurement reset.
        config.numMeasSharp = 0
        config.maxSharpness = 0

        self.updateStatus("Set auto exposure mode")

    # meteringModeBox
    def setMeteringMode(self, idx):
        self.sendCtrl(meteringMode + str(idx))

        # Sharpness measurement reset.
        config.numMeasSharp = 0
        config.maxSharpness = 0

        self.updateStatus("Set measurement mode")

    # resolutionBox
    def setCapRes(self, idx):
        self.sendCtrl(setSize + str(idx))

        match idx:

            case 0:
                self.imgCapW = 2028
                self.imgCapH = 1520
            case 1:
                self.imgCapW = 4056
                self.imgCapH = 3040

        # Capture size and maximum allowed cropping are updated.
        self.setMaxCrop()

        # Sharpness measurement reset.
        config.numMeasSharp = 0
        config.maxSharpness = 0

        self.updateStatus("Set capture resolution")

    # sharpnessBox
    def setSharpness(self, value):
        value = round(value, 1)
        self.sendCtrl(setSharp + str(value))

        # Sharpness measurement reset.
        config.numMeasSharp = 0
        config.maxSharpness = 0

        self.updateStatus("Set capture sharpness")

    # Post-capture settings.
    # They are made on the client. No need to inform the server.

    # showHist
    def initHistogram(self, isOn):
        config.showHist = isOn
        if isOn:
            if not self.histograma:
                self.histograma = DS8Histogram()
            self.histograma.mngr.window.setGeometry(1000, 200, 480, 360)
            self.logarithmHist.setEnabled(True)
            self.plotHistogramEvent.wait(10)
            self.updateHistogram(self.lastShowImg, self.lastShowTitle)
            self.updateStatus("Show histogram")
        else:
            self.histograma.closeHist()
            self.histograma = None
            self.logarithmHist.setEnabled(False)
            self.updateStatus("Don't show histogram")

    # logarithmHist
    def mklogHist(self, isOn):
        config.logarithmHist = isOn
        if config.showHist:
            self.plotHistogramEvent.wait(10)
            self.updateHistogram(self.lastShowImg, self.lastShowTitle)
            if isOn:
                self.updateStatus("Histogram with logarithmic scale")
            else:
                self.updateStatus("Histogram with linear scale")

    # sharpCheckBox
    def showSharpness(self, isOn):
        config.numMeasSharp = 0
        config.maxSharpness = 0
        config.showSharp = isOn
        if isOn:
            self.updateStatus("Show sharpness index")
        else:
            self.updateStatus("Don't show sharpness index")

    # roundCorns
    def setRoundCorns(self, isOn):
        config.roundcorns = isOn
        if isOn:
            self.updateStatus("Round angles")
        else:
            self.updateStatus("Don't round angles")

    # rotationCheckBox
    def setRotation(self, isOn):
        config.rotation = isOn
        if isOn:
            self.rotationBox.setEnabled(True)
            config.rotationValue = round(self.rotationBox.value(), 2)
            self.updateStatus("Rotate image")
        else:
            self.rotationBox.setEnabled(False)
            self.updateStatus("Do not rotate image")

        if isOn and config.prevOn:
            self.rotationBox.setEnabled(True)
        else:
            self.rotationBox.setEnabled(False)

        # Sharpness measurement reset.
        config.numMeasSharp = 0
        config.maxSharpness = 0

    # rotationBox
    def setRotationValue(self, value):
        config.rotationValue = round(value, 2)

        # Sharpness measurement reset.
        config.numMeasSharp = 0
        config.maxSharpness = 0

        if value:
            self.updateStatus("Rotation angle set")
        else:
            self.updateStatus("Angle of rotation at 0º")

    # croppingCheckBox
    def setCrop(self, isOn):
        config.cropping = isOn
        if isOn:
            config.CropT = self.cropTopBox.value()
            config.cropL = self.cropLeftBox.value()
            config.cropR = self.cropRightBox.value()
            config.cropB = self.cropBottomBox.value()
            self.updateStatus("Crop image")

        else:
            self.updateStatus("Do not crop image")

        if isOn and config.prevOn:
            self.cropTopBox.setEnabled(True)
            self.cropLeftBox.setEnabled(True)
            self.cropRightBox.setEnabled(True)
            self.cropBottomBox.setEnabled(True)
        else:
            self.cropTopBox.setEnabled(False)
            self.cropLeftBox.setEnabled(False)
            self.cropRightBox.setEnabled(False)
            self.cropBottomBox.setEnabled(False)

        # Sharpness measurement reset.
        config.numMeasSharp = 0
        config.maxSharpness = 0

    # cropTopBox
    def setCropT(self, value):
        config.cropT = value

        # Sharpness measurement reset.
        config.numMeasSharp = 0
        config.maxSharpness = 0

        self.updateStatus("Set top cutout")

    # cropLeftBox
    def setCropL(self, value):
        config.cropL = value

        # Sharpness measurement reset.
        config.numMeasSharp = 0
        config.maxSharpness = 0

        self.updateStatus("Set left clipping")

    # cropRightBox
    def setCropR(self, value):
        config.cropR = value

        # Sharpness measurement reset.
        config.numMeasSharp = 0
        config.maxSharpness = 0

        self.updateStatus("Set right clipping")

    # cropBottomBox
    def setCropB(self, value):
        config.cropB = value

        # Sharpness measurement reset.
        config.numMeasSharp = 0
        config.maxSharpness = 0

        self.updateStatus("Set bottom cutout")

    # HDR settings

    # PHighSpinBox
    def setPercentHigh(self, percent):
        config.MertPercHigh = percent
        self.updateStatus("Set high percentile to {:.1f} %".format(percent))

    # PLowSpinBox
    def setPercentLow(self, percent):
        config.MertPercLow = percent
        self.updateStatus("Set low percentile to {:.1f} %".format(percent))

    # HDRMertensRadioButton, HDRDebevecRadioButton
    def setHDRAlgorithm(self, updStat=True):
        if self.bracketingBox.value() == 1 or not self.stopsBox.value():
            self.HDRMertensRadioButton.setEnabled(False)
            self.HDRDebevecRadioButton.setEnabled(False)
        else:
            self.HDRMertensRadioButton.setEnabled(True)
            self.HDRDebevecRadioButton.setEnabled(True)

        if self.HDRMertensRadioButton.isChecked():
            config.blender = "Mertens"
            self.PHighLabel.setEnabled(True)
            self.PHighSpinBox.setEnabled(True)
            self.PLowLabel.setEnabled(True)
            self.PLowSpinBox.setEnabled(True)
            self.SimpleRadioButton.setEnabled(False)
            self.SimpleGammaLabel.setEnabled(False)
            self.SimpleGammaSpinBox.setEnabled(False)
            self.ReinhardRadioButton.setEnabled(False)
            self.ReinhardGammaLabel.setEnabled(False)
            self.ReinhardGammaSpinBox.setEnabled(False)
            self.ReinhardIntensityLabel.setEnabled(False)
            self.ReinhardIntensitySpinBox.setEnabled(False)
            self.ReinhardLightLabel.setEnabled(False)
            self.ReinhardLightSpinBox.setEnabled(False)
            self.ReinhardColorLabel.setEnabled(False)
            self.ReinhardColorSpinBox.setEnabled(False)
            self.DragoRadioButton.setEnabled(False)
            self.DragoGammaLabel.setEnabled(False)
            self.DragoGammaSpinBox.setEnabled(False)
            self.DragoSaturationLabel.setEnabled(False)
            self.DragoSaturationSpinBox.setEnabled(False)
            self.DragoBiasLabel.setEnabled(False)
            self.DragoBiasSpinBox.setEnabled(False)
            self.MantiukRadioButton.setEnabled(False)
            self.MantiukGammaLabel.setEnabled(False)
            self.MantiukGammaSpinBox.setEnabled(False)
            self.MantiukSaturationLabel.setEnabled(False)
            self.MantiukSaturationSpinBox.setEnabled(False)
            self.MantiukScaleLabel.setEnabled(False)
            self.MantiukScaleSpinBox.setEnabled(False)
            if updStat:
                self.updateStatus("Set HDR Mertens")

        elif (self.HDRDebevecRadioButton.isEnabled()
              and self.HDRDebevecRadioButton.isChecked()):
            config.blender = "Debevec"
            self.PHighLabel.setEnabled(False)
            self.PHighSpinBox.setEnabled(False)
            self.PLowLabel.setEnabled(False)
            self.PLowSpinBox.setEnabled(False)
            self.SimpleRadioButton.setEnabled(True)
            self.ReinhardRadioButton.setEnabled(True)
            self.DragoRadioButton.setEnabled(True)
            self.MantiukRadioButton.setEnabled(True)
            self.setToneMapAlgorithm(False)
            if updStat:
                self.updateStatus("Set HDR Debevec")

    # Tone mapping algorithm controls.
    # SimpleRadioButton, ReinhardRadioButton, DragoRadioButton,
    # MantiukRadioButton
    def setToneMapAlgorithm(self, updStat=True):
        if (self.SimpleRadioButton.isEnabled()
                and self.SimpleRadioButton.isChecked()):
            config.toneMap = "Simple"
            self.SimpleGammaLabel.setEnabled(True)
            self.SimpleGammaSpinBox.setEnabled(True)
            self.ReinhardGammaLabel.setEnabled(False)
            self.ReinhardGammaSpinBox.setEnabled(False)
            self.ReinhardIntensityLabel.setEnabled(False)
            self.ReinhardIntensitySpinBox.setEnabled(False)
            self.ReinhardLightLabel.setEnabled(False)
            self.ReinhardLightSpinBox.setEnabled(False)
            self.ReinhardColorLabel.setEnabled(False)
            self.ReinhardColorSpinBox.setEnabled(False)
            self.DragoGammaLabel.setEnabled(False)
            self.DragoGammaSpinBox.setEnabled(False)
            self.DragoSaturationLabel.setEnabled(False)
            self.DragoSaturationSpinBox.setEnabled(False)
            self.DragoBiasLabel.setEnabled(False)
            self.DragoBiasSpinBox.setEnabled(False)
            self.MantiukGammaLabel.setEnabled(False)
            self.MantiukGammaSpinBox.setEnabled(False)
            self.MantiukSaturationLabel.setEnabled(False)
            self.MantiukSaturationSpinBox.setEnabled(False)
            self.MantiukScaleLabel.setEnabled(False)
            self.MantiukScaleSpinBox.setEnabled(False)
            if updStat:
                self.updateStatus("Established simple tone mapping algorithm")

        elif (self.ReinhardRadioButton.isEnabled() and
              self.ReinhardRadioButton.isChecked()):
            config.toneMap = "Reinhard"
            self.SimpleGammaLabel.setEnabled(False)
            self.SimpleGammaSpinBox.setEnabled(False)
            self.ReinhardGammaLabel.setEnabled(True)
            self.ReinhardGammaSpinBox.setEnabled(True)
            self.ReinhardIntensityLabel.setEnabled(True)
            self.ReinhardIntensitySpinBox.setEnabled(True)
            self.ReinhardLightLabel.setEnabled(True)
            self.ReinhardLightSpinBox.setEnabled(True)
            self.ReinhardColorLabel.setEnabled(True)
            self.ReinhardColorSpinBox.setEnabled(True)
            self.DragoGammaLabel.setEnabled(False)
            self.DragoGammaSpinBox.setEnabled(False)
            self.DragoSaturationLabel.setEnabled(False)
            self.DragoSaturationSpinBox.setEnabled(False)
            self.DragoBiasLabel.setEnabled(False)
            self.DragoBiasSpinBox.setEnabled(False)
            self.MantiukGammaLabel.setEnabled(False)
            self.MantiukGammaSpinBox.setEnabled(False)
            self.MantiukSaturationLabel.setEnabled(False)
            self.MantiukSaturationSpinBox.setEnabled(False)
            self.MantiukScaleLabel.setEnabled(False)
            self.MantiukScaleSpinBox.setEnabled(False)
            if updStat:
                self.updateStatus("Established Reinhard tone mapping algorithm")

        elif (self.DragoRadioButton.isEnabled() and
              self.DragoRadioButton.isChecked()):
            config.toneMap = "Drago"
            self.SimpleGammaLabel.setEnabled(False)
            self.SimpleGammaSpinBox.setEnabled(False)
            self.ReinhardGammaLabel.setEnabled(False)
            self.ReinhardGammaSpinBox.setEnabled(False)
            self.ReinhardIntensityLabel.setEnabled(False)
            self.ReinhardIntensitySpinBox.setEnabled(False)
            self.ReinhardLightLabel.setEnabled(False)
            self.ReinhardLightSpinBox.setEnabled(False)
            self.ReinhardColorLabel.setEnabled(False)
            self.ReinhardColorSpinBox.setEnabled(False)
            self.DragoGammaLabel.setEnabled(True)
            self.DragoGammaSpinBox.setEnabled(True)
            self.DragoSaturationLabel.setEnabled(True)
            self.DragoSaturationSpinBox.setEnabled(True)
            self.DragoBiasLabel.setEnabled(True)
            self.DragoBiasSpinBox.setEnabled(True)
            self.MantiukGammaLabel.setEnabled(False)
            self.MantiukGammaSpinBox.setEnabled(False)
            self.MantiukSaturationLabel.setEnabled(False)
            self.MantiukSaturationSpinBox.setEnabled(False)
            self.MantiukScaleLabel.setEnabled(False)
            self.MantiukScaleSpinBox.setEnabled(False)
            if updStat:
                self.updateStatus("Established Drago tone mapping algorithm")

        elif (self.MantiukRadioButton.isEnabled() and
              self.MantiukRadioButton.isChecked()):
            config.toneMap = "Mantiuk"
            self.SimpleGammaLabel.setEnabled(False)
            self.SimpleGammaSpinBox.setEnabled(False)
            self.ReinhardGammaLabel.setEnabled(False)
            self.ReinhardGammaSpinBox.setEnabled(False)
            self.ReinhardIntensityLabel.setEnabled(False)
            self.ReinhardIntensitySpinBox.setEnabled(False)
            self.ReinhardLightLabel.setEnabled(False)
            self.ReinhardLightSpinBox.setEnabled(False)
            self.ReinhardColorLabel.setEnabled(False)
            self.ReinhardColorSpinBox.setEnabled(False)
            self.DragoGammaLabel.setEnabled(False)
            self.DragoGammaSpinBox.setEnabled(False)
            self.DragoSaturationLabel.setEnabled(False)
            self.DragoSaturationSpinBox.setEnabled(False)
            self.DragoBiasLabel.setEnabled(False)
            self.DragoBiasSpinBox.setEnabled(False)
            self.MantiukGammaLabel.setEnabled(True)
            self.MantiukGammaSpinBox.setEnabled(True)
            self.MantiukSaturationLabel.setEnabled(True)
            self.MantiukSaturationSpinBox.setEnabled(True)
            self.MantiukScaleLabel.setEnabled(True)
            self.MantiukScaleSpinBox.setEnabled(True)
            if updStat:
                self.updateStatus("Established Mantiuk tone mapping algorithm")

    # SimpleGammaSpinBox
    def simpleGamma(self, gamma):
        gamma = round(gamma, 1)
        config.SimpleGamma = gamma
        self.updateStatus("Set gamma parameter to " + str(gamma))

    # ReinhardGammaSpinBox
    def reinhardGamma(self, gamma):
        gamma = round(gamma, 1)
        config.ReinhardGamma = gamma
        self.updateStatus("Set gamma parameter to " + str(gamma))

    # ReinhardIntensitySpinBox
    def reinhardIntensity(self, intensity):
        intensity = round(intensity, 1)
        config.ReinhardIntensity = intensity
        self.updateStatus("Intensity parameter set to " + str(intensity))

    # ReinhardLightSpinBox
    def reinhardLight(self, light):
        light = round(light, 1)
        config.ReinhardLight = light
        self.updateStatus("Set light parameter to " + str(light))

    # ReinhardColorSpinBox
    def reinhardColor(self, color):
        color = round(color, 1)
        config.ReinhardColor = color
        self.updateStatus("Set color parameter to " + str(color))

    # DragoGammaSpinBox
    def dragoGamma(self, gamma):
        gamma = round(gamma, 1)
        config.DragoGamma = gamma
        self.updateStatus("Set gamma parameter to " + str(gamma))

    # DragoSaturationSpinBox
    def dragoSaturation(self, saturation):
        saturation = round(saturation, 1)
        config.DragoSaturation = saturation
        self.updateStatus("Set saturation parameter to " + str(saturation))

    # DragoBiasSpinBox
    def dragoBias(self, bias):
        bias = round(bias, 2)
        config.DragoBias = bias
        self.updateStatus("Set bias parameter to " + str(bias))

    # MantiukGammaSpinBox
    def mantiukGamma(self, gamma):
        gamma = round(gamma, 1)
        config.MantiukGamma = gamma
        self.updateStatus("Set gamma parameter to " + str(gamma))

    # MantiukSaturationSpinBox
    def mantiukSaturation(self, saturation):
        saturation = round(saturation, 1)
        config.MantiukSaturation = saturation
        self.updateStatus("Set saturation parameter to " + str(saturation))

    # MantiukScaleSpinBox
    def mantiukScale(self, scale):
        scale = round(scale, 2)
        config.MantiukScale = scale
        self.updateStatus("Set scale parameter to " + str(scale))

    # This function is used to check that all the conditions to start the
    # capture are met.
    # Used to activate the Test and Start buttons.
    # Necessary conditions:
    # - Motor idle.
    # - Inactive preview.
    # - Film placed in position.
    # - Capture folder determined.
    # - Configured a single photo per frame or
    # - Configured more than one photo per frame and more than 0 stop points.
    def checkCaptureOK(self):
        if (config.motorNotMoving and
            (not config.prevOn) and
            self.startPosCheckBox.isChecked() and
            config.capFolder.strip() and
            Path(config.capFolder.strip()).is_dir() and
            (self.bracketingBox.value() == 1 or
                 (self.bracketingBox.value() > 1 and self.stopsBox.value()))):

            self.captureTestBtn.setEnabled(True)
            self.captureStartBtn.setEnabled(True)

        else:
            self.captureTestBtn.setEnabled(False)
            self.captureStartBtn.setEnabled(False)

    def disableButtons(self):
        self.fRevButton.setEnabled(False)
        self.reverseButton.setEnabled(False)
        self.forwardButton.setEnabled(False)
        self.ffdButton.setEnabled(False)
        self.captureTestBtn.setEnabled(False)
        self.activateMotorCheckBox.setEnabled(False)
        self.gotoCheckBox.setEnabled(False)
        self.passToCheckbox.setEnabled(False)
        self.nextFrameBox.setEnabled(False)
        self.captureFrmRev10.setEnabled(False)
        self.captureFrmRev.setEnabled(False)
        self.captureFrmAdv.setEnabled(False)
        self.captureFrmAdv10.setEnabled(False)
        self.captureStartBtn.setEnabled(False)
        self.quitButton.setEnabled(False)

    def enableButtons(self):
        self.fRevButton.setEnabled(True)
        self.reverseButton.setEnabled(True)
        self.stopButton.setEnabled(False)
        self.forwardButton.setEnabled(True)
        self.ffdButton.setEnabled(True)
        self.quitButton.setEnabled(True)
        self.activateMotorCheckBox.setEnabled(True)
        if self.startPosCheckBox.isChecked():
            self.passToCheckbox.setEnabled(True)
            self.gotoCheckBox.setEnabled(True)
            self.nextFrameBox.setEnabled(True)
            self.captureFrmRev10.setEnabled(True)
            self.captureFrmRev.setEnabled(True)
            self.captureFrmAdv.setEnabled(True)
            self.captureFrmAdv10.setEnabled(True)

            # Activate Test and Start buttons.
            self.checkCaptureOK()

    def disableAEWidgets(self):
        self.analogueGainLabel.setEnabled(True)
        self.analogueGainBox.blockSignals(False)
        self.analogueGainBox.setEnabled(True)
        self.EVLabel.setEnabled(False)
        self.EVBox.setEnabled(False)
        if config.prevOn:
            self.constraintModeLabel.setEnabled(False)
            self.constraintModeBox.setEnabled(False)
            self.exposureModeLabel.setEnabled(False)
            self.exposureModeBox.setEnabled(False)
            self.meteringModeLabel.setEnabled(False)
            self.meteringModeBox.setEnabled(False)

    def enableAEWidgets(self):
        self.analogueGainLabel.setEnabled(False)
        self.analogueGainBox.blockSignals(True)
        self.analogueGainBox.setEnabled(False)
        self.EVLabel.setEnabled(True)
        self.EVBox.setEnabled(True)
        self.setEV(self.EVBox.value())
        self.timeExpLabel.setEnabled(False)
        self.timeExpBox.blockSignals(True)
        self.timeExpBox.setEnabled(False)
        self.exposureDownBtn.setEnabled(False)
        self.exposureUpBtn.setEnabled(False)
        if config.prevOn:
            self.constraintModeLabel.setEnabled(True)
            self.constraintModeBox.setEnabled(True)
            self.exposureModeLabel.setEnabled(True)
            self.exposureModeBox.setEnabled(True)
            self.meteringModeLabel.setEnabled(True)
            self.meteringModeBox.setEnabled(True)

    def disableCaptureWidgets(self):
        # Disable lighting control.
        self.lightCheckbox.setEnabled(False)

        # Disable preview images.
        self.prevCheckBox.setChecked(False)
        self.prevCheckBox.setEnabled(False)
        config.prevOn = False

        # Disable home position indicator.
        self.startPosCheckBox.setEnabled(False)

        # Disable analog gain control.
        self.analogueGainLabel.setEnabled(False)
        self.analogueGainBox.setEnabled(False)

        # Disable EV control.
        self.EVLabel.setEnabled(False)
        self.EVBox.setEnabled(False)

        # Disable white balance adjustment.
        self.awbLabel.setEnabled(False)
        self.awbBox.setEnabled(False)
        self.awbManualBtn.setEnabled(False)

        # Disable blue and red sliders and controls.
        self.blueLabel.setEnabled(False)
        self.blueGainSlider.setEnabled(False)
        self.blueGainBox.setEnabled(False)
        self.blueResetBtn.setEnabled(False)
        self.redLabel.setEnabled(False)
        self.redGainSlider.setEnabled(False)
        self.redGainBox.setEnabled(False)
        self.redResetBtn.setEnabled(False)

        # Disable slider and brightness control.
        self.brightnessLabel.setEnabled(False)
        self.brightnessSlider.setEnabled(False)
        self.brightnessBox.setEnabled(False)
        self.resetBrightnessBtn.setEnabled(False)

        # Disable slider and contrast control.
        self.contrastLabel.setEnabled(False)
        self.contrastSlider.setEnabled(False)
        self.contrastBox.setEnabled(False)
        self.resetContrastBtn.setEnabled(False)

        # Disable slider and saturation control.
        self.saturationLabel.setEnabled(False)
        self.saturationSlider.setEnabled(False)
        self.saturationBox.setEnabled(False)
        self.resetSaturationBtn.setEnabled(False)

        # Disable exit button.
        self.quitButton.setEnabled(False)

        # Disable auto exposure control.
        self.autoExpCheckBox.setEnabled(False)

        # Disable motor activation control.
        self.activateMotorCheckBox.setEnabled(False)

        # Disable manual position adjustment controls.
        self.frameLCDCountUpBtn.setEnabled(False)
        self.frameLCDCountDownBtn.setEnabled(False)
        self.passToCheckbox.setEnabled(False)

        # Disable motion and capture controls.
        self.fRevButton.setEnabled(False)
        self.reverseButton.setEnabled(False)
        self.stopButton.setEnabled(False)
        self.forwardButton.setEnabled(False)
        self.ffdButton.setEnabled(False)
        self.bracketingBox.setEnabled(False)
        self.bracketingLabel.setEnabled(False)
        self.captureTestBtn.setEnabled(False)
        self.stopsBox.setEnabled(False)
        self.stopsLabel.setEnabled(False)
        self.timeExpLabel.setEnabled(False)
        self.timeExpBox.setEnabled(False)
        self.timeExpBox.blockSignals(True)
        self.exposureDownBtn.setEnabled(False)
        self.exposureUpBtn.setEnabled(False)
        self.gotoCheckBox.setEnabled(False)
        self.nextFrameBox.setEnabled(False)
        self.captureFrmRev10.setEnabled(False)
        self.captureFrmRev.setEnabled(False)
        self.captureFrmAdv.setEnabled(False)
        self.captureFrmAdv10.setEnabled(False)
        self.captureStartBtn.setEnabled(False)
        if config.lastMode == "C":
            self.captureStopBtn.setEnabled(True)
            self.capturePauseBtn.setEnabled(True)

        # Disable folder selection.
        self.configFileBox.setEnabled(False)
        self.loadConfigButton.setEnabled(False)
        self.capFolderBox.setEnabled(False)
        self.chooseFolderBtn.setEnabled(False)

        # Disable post-capture settings.
        self.roundCorns.setEnabled(False)

        # Disable HDR settings.
        self.PHighLabel.setEnabled(False)
        self.PHighSpinBox.setEnabled(False)
        self.PLowLabel.setEnabled(False)
        self.PLowSpinBox.setEnabled(False)
        self.HDRMertensRadioButton.setEnabled(False)
        self.HDRDebevecRadioButton.setEnabled(False)

        self.SimpleRadioButton.setEnabled(False)
        if self.SimpleRadioButton.isChecked():
            self.SimpleGammaLabel.setEnabled(False)
            self.SimpleGammaSpinBox.setEnabled(False)

        self.ReinhardRadioButton.setEnabled(False)
        if self.ReinhardRadioButton.isChecked():
            self.ReinhardGammaLabel.setEnabled(False)
            self.ReinhardGammaSpinBox.setEnabled(False)
            self.ReinhardIntensityLabel.setEnabled(False)
            self.ReinhardIntensitySpinBox.setEnabled(False)
            self.ReinhardLightLabel.setEnabled(False)
            self.ReinhardLightSpinBox.setEnabled(False)
            self.ReinhardColorLabel.setEnabled(False)
            self.ReinhardColorSpinBox.setEnabled(False)

        self.DragoRadioButton.setEnabled(False)
        if self.DragoRadioButton.isChecked():
            self.DragoGammaLabel.setEnabled(False)
            self.DragoGammaSpinBox.setEnabled(False)
            self.DragoSaturationLabel.setEnabled(False)
            self.DragoSaturationSpinBox.setEnabled(False)
            self.DragoBiasLabel.setEnabled(False)
            self.DragoBiasSpinBox.setEnabled(False)

        self.MantiukRadioButton.setEnabled(False)
        if self.MantiukRadioButton.isChecked():
            self.MantiukGammaSpinBox.setEnabled(False)
            self.MantiukGammaLabel.setEnabled(False)
            self.MantiukSaturationLabel.setEnabled(False)
            self.MantiukSaturationSpinBox.setEnabled(False)
            self.MantiukScaleLabel.setEnabled(False)
            self.MantiukScaleSpinBox.setEnabled(False)

    def enableCaptureWidgets(self):

        if not config.captureOn:
            # Enable lighting control.
            self.lightCheckbox.setEnabled(True)

            # Allow preview images.
            self.prevCheckBox.setEnabled(True)

            # Enable home position indicator.
            self.startPosCheckBox.setEnabled(True)

            # Activate analog gain and EV controls.
            if self.autoExpCheckBox.isChecked():
                self.EVLabel.setEnabled(True)
                self.EVBox.setEnabled(True)
            else:
                self.analogueGainLabel.setEnabled(True)
                self.analogueGainBox.setEnabled(True)

            # Allow white balance adjustment.
            self.awbLabel.setEnabled(True)
            self.awbBox.setEnabled(True)
            self.awbManualBtn.setEnabled(True)

            # Enable blue and red sliders and controls.
            if self.awbBox.currentIndex() == 8:
                self.blueLabel.setEnabled(True)
                self.blueGainSlider.setEnabled(True)
                self.blueGainBox.setEnabled(True)
                self.blueResetBtn.setEnabled(True)
                self.redLabel.setEnabled(True)
                self.redGainSlider.setEnabled(True)
                self.redGainBox.setEnabled(True)
                self.redResetBtn.setEnabled(True)

            # Enable slider and brightness control.
            self.brightnessLabel.setEnabled(True)
            self.brightnessSlider.setEnabled(True)
            self.brightnessBox.setEnabled(True)
            self.resetBrightnessBtn.setEnabled(True)

            # Enable slider and contrast control.
            self.contrastLabel.setEnabled(True)
            self.contrastSlider.setEnabled(True)
            self.contrastBox.setEnabled(True)
            self.resetContrastBtn.setEnabled(True)

            # Enable slider and saturation control.
            self.saturationLabel.setEnabled(True)
            self.saturationSlider.setEnabled(True)
            self.saturationBox.setEnabled(True)
            self.resetSaturationBtn.setEnabled(True)

            # Enable exit button.
            self.quitButton.setEnabled(True)

            # Enable auto exposure control.
            self.autoExpCheckBox.setEnabled(True)

            # Enable manual exposure adjustment controls.
            if not self.autoExpCheckBox.isChecked():
                self.timeExpLabel.setEnabled(True)
                self.timeExpBox.setEnabled(True)
                self.timeExpBox.blockSignals(False)
                self.timeExpBox.setValue(self.manExpTime)
                if self.timeExpBox.value():
                    self.exposureDownBtn.setEnabled(True)
                if self.timeExpBox.value() < 1000:
                    self.exposureUpBtn.setEnabled(True)
            else:
                self.timeExpBox.setValue(self.autoExpTime)

            # Enable motor activation control.
            self.activateMotorCheckBox.setEnabled(True)

            # Enable manual position adjustment controls.
            self.frameLCDCountUpBtn.setEnabled(True)
            self.frameLCDCountDownBtn.setEnabled(True)
            self.passToCheckbox.setEnabled(True)

            # Enable motion and capture controls.
            self.fRevButton.setEnabled(True)
            self.reverseButton.setEnabled(True)
            self.stopButton.setEnabled(False)
            self.forwardButton.setEnabled(True)
            self.ffdButton.setEnabled(True)
            self.bracketingBox.setEnabled(True)
            self.bracketingLabel.setEnabled(True)
            if self.startPosCheckBox.isChecked():
                self.captureTestBtn.setEnabled(True)
                self.captureStartBtn.setEnabled(True)
            if self.bracketingBox.value() > 1:
                self.stopsBox.setEnabled(True)
                self.stopsLabel.setEnabled(True)

            self.gotoCheckBox.setEnabled(True)
            self.nextFrameBox.setEnabled(True)
            self.captureFrmRev10.setEnabled(True)
            self.captureFrmRev.setEnabled(True)
            self.captureFrmAdv.setEnabled(True)
            self.captureFrmAdv10.setEnabled(True)
            self.captureStopBtn.setEnabled(False)
            self.capturePauseBtn.setEnabled(False)
            self.nextFrameBox.setEnabled(True)
            self.endFrameBox.setEnabled(True)

            # Engine stop signal sending is activated.
            self.sendCtrl(sendStop)

            # Allow folder selection.
            self.configFileBox.setEnabled(True)
            self.loadConfigButton.setEnabled(True)
            self.capFolderBox.setEnabled(True)
            self.chooseFolderBtn.setEnabled(True)

            # Enable HDR settings.
            if self.bracketingBox.value() > 1:
                self.HDRMertensRadioButton.setEnabled(True)
                self.HDRDebevecRadioButton.setEnabled(True)

                if self.HDRMertensRadioButton.isChecked():
                    self.PHighLabel.setEnabled(True)
                    self.PHighSpinBox.setEnabled(True)
                    self.PLowLabel.setEnabled(True)
                    self.PLowSpinBox.setEnabled(True)

                elif self.HDRDebevecRadioButton.isChecked():
                    self.SimpleRadioButton.setEnabled(True)
                    if self.SimpleRadioButton.isChecked():
                        self.SimpleGammaLabel.setEnabled(True)
                        self.SimpleGammaSpinBox.setEnabled(True)
                    self.ReinhardRadioButton.setEnabled(True)
                    if self.ReinhardRadioButton.isChecked():
                        self.ReinhardGammaLabel.setEnabled(True)
                        self.ReinhardGammaSpinBox.setEnabled(True)
                        self.ReinhardIntensityLabel.setEnabled(True)
                        self.ReinhardIntensitySpinBox.setEnabled(True)
                        self.ReinhardLightLabel.setEnabled(True)
                        self.ReinhardLightSpinBox.setEnabled(True)
                        self.ReinhardColorLabel.setEnabled(True)
                        self.ReinhardColorSpinBox.setEnabled(True)
                    self.DragoRadioButton.setEnabled(True)
                    if self.DragoRadioButton.isChecked():
                        self.DragoGammaLabel.setEnabled(True)
                        self.DragoGammaSpinBox.setEnabled(True)
                        self.DragoSaturationLabel.setEnabled(True)
                        self.DragoSaturationSpinBox.setEnabled(True)
                        self.DragoBiasLabel.setEnabled(True)
                        self.DragoBiasSpinBox.setEnabled(True)
                    self.MantiukRadioButton.setEnabled(True)
                    if self.MantiukRadioButton.isChecked():
                        self.MantiukGammaSpinBox.setEnabled(True)
                        self.MantiukGammaLabel.setEnabled(True)
                        self.MantiukSaturationLabel.setEnabled(True)
                        self.MantiukSaturationSpinBox.setEnabled(True)
                        self.MantiukScaleLabel.setEnabled(True)
                        self.MantiukScaleSpinBox.setEnabled(True)

                    self.setToneMapAlgorithm(False)

    # It is used in histogram activation operations.
    def takenImg(self, img, title):
        self.lastShowImg = img
        self.lastShowTitle = title
        self.showImgSizes()

    # Maximum allowed clipping.
    def setMaxCrop(self):
        # Minimum image size 100x100 pixels.
        maxCropW = int((self.imgCapW - 100) / 2)
        maxCropH = int((self.imgCapH - 100) / 2)
        self.cropTopBox.setMaximum(maxCropH)
        self.cropLeftBox.setMaximum(maxCropW)
        self.cropRightBox.setMaximum(maxCropW)
        self.cropBottomBox.setMaximum(maxCropH)

    def showImgSizes(self):
        self.sizeImgCapLabel.setText("Capturada: " + str(config.imgCapIniW) +
                                     "x" + str(config.imgCapIniH))
        self.sizeImgFinalLabel.setText("Final: " + str(config.imgCapResW) +
                                       "x" + str(config.imgCapResH))

    # This function runs when the server reports engine stopped.
    def motorStopped(self):
        info("Engine stopped signal received")
        if self.dirty and self.startPosCheckBox.isChecked():
            config.fileNumber = config.frameNumber
            self.dirty = False
        config.motorNotMoving = True
        if not self.capturePauseBtn.isChecked() and not config.captureOn:
            self.enableButtons()

    # This function is executed when the server reports light on or off. It is
    # used to update the status of the lighting control.
    def updateLightCheckbox(self, flag):
        # Light on.
        if flag == "l":
            info("Received light on signal")
            self.lightCheckbox.blockSignals(True)
            self.lightCheckbox.setEnabled(False)
            self.lightCheckbox.setChecked(True)

        # Light off.
        elif flag == "L":
            info("Received light off signal")
            self.lightCheckbox.setChecked(False)
            if not self.capturePauseBtn.isChecked():
                self.lightCheckbox.setEnabled(True)
                self.lightCheckbox.blockSignals(False)

        else:
            return

    def updateGains(self, gblue, gred):
        if self.awbBox.currentIndex() < 7:
            info("Camera reported color gains. Blue = " + str(gblue) +
                 ", Red = " + str(gred))
            self.blueGainSlider.blockSignals(True)
            self.blueGainBox.blockSignals(True)
            self.redGainSlider.blockSignals(True)
            self.redGainBox.blockSignals(True)

            self.blueGainSlider.setSliderPosition(int(gblue * 100))
            self.blueGainBox.setValue(gblue)
            self.redGainSlider.setSliderPosition(int(gred * 100))
            self.redGainBox.setValue(gred)

    # Automatic exposure data update.
    def updateSSAE(self, ssAE, again, dgain, framerate):
        if self.autoExpCheckBox.isChecked():
            #info("updateSSAE called")
            ssAE = round(ssAE / 1000, 1)
            self.autoExpTime = ssAE
            minExp = self.minExp(ssAE)
            self.exposureBoxMin.setValue(minExp)
            self.exposureBox.setValue(ssAE)
            maxExp = self.maxExp(ssAE)
            self.exposureBoxMax.setValue(maxExp)
            self.timeExpBox.setValue(ssAE)
            self.FPSdoubleSpinBox.setValue(framerate)
            self.gainBoxA.setValue(again)
            self.gainBoxD.setValue(dgain)
            self.analogueGainBox.setValue(again)

    # Exposure data update.
    def updateSS(self, ss, again, dgain, framerate):
        #info("updateSS called")
        ss = round((ss / 1000), 1)
        self.timeExpBox.setValue(ss)
        self.FPSdoubleSpinBox.setValue(framerate)
        self.gainBoxA.setValue(again)
        self.gainBoxD.setValue(dgain)
        self.analogueGainBox.setValue(again)

    def minExp(self, ss):
        if self.bracketingBox.value() == 1:
            minExp = round(ss, 1)
        else:
            minExp = round(ss / (2**(self.stopsBox.value() / 2)), 1)

        return minExp

    def maxExp(self, ss):
        if self.bracketingBox.value() == 1:
            maxExp = round(ss, 1)
        else:
            maxExp = round(ss * (2**(self.stopsBox.value() / 2)), 1)

        camMaxExpTime = round(config.camMaxExpTime / 1000, 1)

        if maxExp > camMaxExpTime:
            maxExp = camMaxExpTime

        return maxExp

    def updateFrameNum(self, flag):
        if self.startPosCheckBox.isChecked():
            # Advance of a frame.
            if flag == "c":
                info("Frame advance signal received")
                config.frameNumber += 1
            # Back one frame.
            elif flag == "C":
                info("Frame reverse signal received")
                config.frameNumber -= 1
            # The position indicator is updated.
            self.frameLcd.display(config.frameNumber)

            # The command go to is deactivated.
            if config.frameNumber == self.nextFrameBox.value():
                self.gotoCheckBox.setChecked(False)

    def updateStatus(self, status):
        self.statusBar.setText(status)

    def updateHistogram(self, cvimg, title):
        if config.showHist and self.histograma:
            self.histograma.plotHistogram(cvimg, title)
            self.plotHistogramEvent.set()

    # This function is to activate the default GUI settings.

    def setDefaultConfiguration(self):

        # Setup.
        self.zoomDial.setValue(1000)
        self.x_offset = 0
        self.y_offset = 0
        self.lightCheckbox.setChecked(False)
        self.startPosCheckBox.setChecked(False)

        # Camera.
        self.analogueGainBox.setValue(1.0)
        self.EVBox.setValue(0.0)
        self.awbBox.setCurrentIndex(0)
        self.blueGainBox.setValue(1.5)
        self.redGainBox.setValue(2.7)
        self.manualBlueGain = 1.5
        self.manualRedGain = 2.7
        self.brightnessBox.setValue(0.0)
        self.contrastBox.setValue(1.0)
        self.saturationBox.setValue(1.0)

        # Capture.
        self.endFrameBox.setValue(3580)
        self.bracketingBox.setValue(1)
        self.saveAllCheckBox.setChecked(False)
        self.stopsBox.setValue(0.0)
        self.autoExpCheckBox.setChecked(False)
        self.timeExpBox.setValue(4.0)
        self.capFolderBox.setText("Select capture folder")
        self.frameLcd.display(0)
        self.nextFrameBox.setValue(1)

        # Advanced.
        self.vFlipCheckBox.setChecked(True)
        self.hFlipCheckBox.setChecked(False)
        self.bwCheckBox.setChecked(False)
        self.constraintModeBox.setCurrentIndex(0)
        self.exposureModeBox.setCurrentIndex(0)
        self.meteringModeBox.setCurrentIndex(0)
        self.resolutionBox.setCurrentIndex(0)
        self.sharpnessBox.setValue(1.0)

        # Post-capture.
        self.showHist.setChecked(True)
        self.logarithmHist.setChecked(False)
        self.sharpCheckBox.setChecked(True)
        self.roundCorns.setChecked(False)
        self.rotationCheckBox.setChecked(False)
        self.rotationBox.setValue(0.0)
        self.croppingCheckBox.setChecked(False)
        self.cropTopBox.setValue(0)
        self.cropLeftBox.setValue(0)
        self.cropRightBox.setValue(0)
        self.cropBottomBox.setValue(0)

        # HDR.
        self.PHighSpinBox.setValue(100.0)
        self.PLowSpinBox.setValue(0.0)
        self.HDRMertensRadioButton.setChecked(True)
        self.HDRDebevecRadioButton.setChecked(False)
        self.SimpleRadioButton.setChecked(True)
        self.SimpleGammaSpinBox.setValue(1.0)
        self.ReinhardRadioButton.setChecked(False)
        self.ReinhardGammaSpinBox.setValue(1.0)
        self.ReinhardIntensitySpinBox.setValue(0.0)
        self.ReinhardLightSpinBox.setValue(0.0)
        self.ReinhardColorSpinBox.setValue(0.0)
        self.DragoRadioButton.setChecked(False)
        self.DragoGammaSpinBox.setValue(1.0)
        self.DragoSaturationSpinBox.setValue(0.0)
        self.DragoBiasSpinBox.setValue(0.85)
        self.MantiukRadioButton.setChecked(False)
        self.MantiukGammaSpinBox.setValue(1.0)
        self.MantiukSaturationSpinBox.setValue(0.0)
        self.MantiukScaleSpinBox.setValue(0.85)

    # Application exit function.
    def exitApp(self, serverExit):

        self.exitAppCalled = True

        # The current configuration is saved.
        self.saveCurrentConfig()

        # serverExit = True -> Exit due to server shutdown.
        if not serverExit:
            self.sendCtrl(clientQuit)
            info("Program exit")
        else:
            info("Program exit due to server shutdown")

        self.imgthread.quit()
        self.imgthread.wait()
        while self.imgthread.isRunning():
            sleep(0.5)
        info("Image thread finalized")

        app = QApplication.instance()
        app.closeAllWindows()

    # This function runs automatically when you close the GUI.
    def closeEvent(self, *args, **kwargs):
        if self.exitAppCalled:
            pass
        else:
            self.exitApp(False)
