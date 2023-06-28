"""
DSuper8 project based on Joe Herman's rpi-film-capture.

Software modified by Manuel Ángel.

User interface redesigned by Manuel Ángel.

DS8ImgThread.py: Class and support functions for reading and processing the
                 images.

Last version: 20230430.
"""

from cv2 import (IMREAD_COLOR, resize, createMergeMertens, createMergeDebevec,
                 createCalibrateDebevec, getRotationMatrix2D, warpAffine,
                 imwrite, Laplacian, IMWRITE_JPEG_QUALITY, imdecode, imencode,
                 createTonemap, createTonemapReinhard, CV_64F,
                 createTonemapDrago, createTonemapMantiuk, cvtColor,
                 COLOR_BGR2GRAY, putText, FONT_HERSHEY_SIMPLEX)

from threading import Event

from struct import unpack, calcsize

from logging import info

from numpy import (uint8, shape, clip, array, ndarray, fromstring, bitwise_and,
                   percentile)

from io import BytesIO

from pathlib import Path

from PyQt6.QtCore import QThread, pyqtSignal

from exif import Image

from datetime import datetime

# Our own modules.

import config

from codes import newImage


# Class and support functions for the reading and treatment of images.

class imgThread(QThread):

    # Frame number indicator update signal.
    updateFrameNumSig = pyqtSignal(str)

    # Automatic exposure data update signal.
    updateAESig = pyqtSignal(int, float, float, float)

    # Exposure data update signal.
    updateSSSig = pyqtSignal(int, float, float, float)

    # A and D gains data update signal.
    updateGainsSig = pyqtSignal(float, float)

    # Image window refresh signal.
    displayImgSig = pyqtSignal(ndarray, str)

    # Histogram window refresh signal.
    plotHistogramSig = pyqtSignal(ndarray, str)

    # Engine stopped information signal.
    motorStoppedSig = pyqtSignal()

    # Application output signal reported by server.
    exitSig = pyqtSignal(bool)

    # Illumination status information signal.
    lightSig = pyqtSignal(str)

    # End of capture signal.
    endCaptureSig = pyqtSignal()

    # Enable capture widgets information signal.
    enableCaptureWidgetsSig = pyqtSignal()

    # Exception on camera information signal.
    PiCameraExcpSig = pyqtSignal()

    # Displayed image information event.
    displayImgEvent = Event()
    displayImgEvent.set()

    # Displayed histogram information event.
    plotHistogramEvent = Event()
    plotHistogramEvent.set()

    def __init__(self, connection, app):
        QThread.__init__(self, parent=app)
        self.threadID = 1
        self.name = "ImgThread"

        self.conn = connection

        # Temporary storage of the image received from the server.
        self.imageStream = BytesIO()

        # Image size received from server.
        self.imageLen = None

        # Opencv image.
        self.cvimg = ndarray

        # Group of images from multiple exposures to obtain an HDR image.
        self.imglist = []

        # Índice utilizado para la matriz de tiempos de exposición.
        self.indexETM = 0

        # Indicator of the type of information received from the server.
        self.imgflag = ""

        # Exposure time reported by camera.
        self.exposureTime = 0

        # Generate angle round masks.
        self.roundcornTLImg = config.readImgFromFile("roundcornTL.png")
        self.roundcornTRImg = config.readImgFromFile("roundcornTR.png")
        self.roundcornBRImg = config.readImgFromFile("roundcornBR.png")
        self.roundcornBLImg = config.readImgFromFile("roundcornBL.png")

        # Image name.
        self.imageName = ""

        # Image file name.
        self.filename = ""

        # Permission to save bracketing images.
        self.saveBracketPerm = False

        #  Focus index coordinates.
        self.x1 = 0
        self.y1 = self.x1
        self.x2 = 0
        self.y2 = 0

        # Final image resolution.
        self.finalh = config.imgCapFinalH
        self.finalw = config.imgCapFinalW

    # Rotating and cropping the image.
    def postProcess(self, img):

        h, w = img.shape[:2]

        # Image rotation if selected.
        if config.rotation:

            rotMtx = getRotationMatrix2D((w / 2, h / 2),
                                         config.rotationValue, 1)
            img = warpAffine(img, rotMtx, (w, h))

            #info("Rotated image")

        # Cropping the image if selected.
        if config.cropping:
            img = img[config.cropT:h - config.cropB,
                      config.cropL:w - config.cropR]

            # info("Cropped image")

        return img

    # Scaling the image to the maximum dimensions specified in the config.py
    # file.
    def imageResize(self, img):
        h, w = img.shape[:2]

        config.imgCapIniH = h
        config.imgCapIniW = w

        self.finalh = config.imgCapFinalH
        self.finalw = int((self.finalh / h) * w)
        if self.finalw > config.imgCapFinalW:
            self.finalw = config.imgCapFinalW
            self.finalh = int((self.finalw / w) * h)
        img = resize(img, (self.finalw, self.finalh))

        # info("Resized image")

        return img

    # Draw the sharpness index on the image.
    def drawImageSharpness(self, img):
        self.x1 = int(config.imgCapIniH / 10.8)
        self.y1 = self.x1
        self.x2 = int(config.imgCapIniH / 3.4)
        self.y2 = int(config.imgCapIniH / 7)
        self.fontScale = round(config.imgCapIniH / 540, 1)
        self.tickness = int(self.fontScale * 2)

        imgSharp = self.imageSharpness(img)

        config.numMeasSharp += 1

        putText(img, "Focus: ", (self.x1, self.y1),
                FONT_HERSHEY_SIMPLEX, self.fontScale, (0, 0, 255),
                self.tickness)

        putText(img, str(imgSharp), (self.x2, self.y1),
                FONT_HERSHEY_SIMPLEX, self.fontScale, (0, 0, 255),
                self.tickness)

        if config.numMeasSharp > config.valSharp:

            if (imgSharp > config.maxSharpness):
                config.maxSharpness = imgSharp

            putText(img, "Max: ", (self.x1, self.y2),
                    FONT_HERSHEY_SIMPLEX, self.fontScale, (0, 0, 255),
                    self.tickness)

            putText(img, str(config.maxSharpness), (self.x2, self.y2),
                    FONT_HERSHEY_SIMPLEX, self.fontScale, (0, 0, 255),
                    self.tickness)

        return img

    # Calculation of the image sharpness index.
    def imageSharpness(self, img):
        imgSharp = 0
        imgSharp = Laplacian(cvtColor(img, COLOR_BGR2GRAY), CV_64F).var()
        imgSharp = round(imgSharp, 2)

        return imgSharp

    # Rounding the angles of the image.
    def roundCorners(self, img):
        h, w = img.shape[:2]

        img[0:50, 0:50] = bitwise_and(img[0:50, 0:50], self.roundcornTLImg)
        img[0:50, w - 50:w] = bitwise_and(img[0:50, w - 50:w],
                                          self.roundcornTRImg)
        img[h - 50:h, w - 50:w] = bitwise_and(img[h - 50:h, w - 50:w],
                                              self.roundcornBRImg)
        img[h - 50:h, 0:50] = bitwise_and(img[h - 50:h, 0:50],
                                          self.roundcornBLImg)
        return img

    # Merging bracketing images to obtain an HDR image.
    def blendImgList(self):

        if config.blender == "Mertens":
            blender = createMergeMertens()
            img = blender.process(self.imglist)

            # Function proposed by Rolf Henkel (cpixip) to carry out the
            # normalization.
            # Percentiles are applied to discard the brightest and darkest
            # pixels in the image.
            minimum = percentile(img, config.MertPercLow)
            maximum = percentile(img, config.MertPercHigh)
            scaler = 1.0 / (maximum - minimum + 1e-6)

            img = scaler * (img - minimum)

        else:
            # In tests carried out, it has been found that, to obtain good
            # results with the Debevec algorithm, it is required to take enough
            # images. Minimum 6 images.

            # Get the response function of the camera (CRF).
            calibrateDebevec = createCalibrateDebevec()
            responseDebevec = calibrateDebevec.process(self.imglist,
                                                       config.exposureTimes)

            # Merge the images into a linear HDR image.
            blender = createMergeDebevec()
            hdrDebevec = blender.process(self.imglist, config.exposureTimes,
                                         responseDebevec)

            # Apply tone mapping.
            match config.toneMap:
                case "Simple":
                    img = self.toneMapSimple(hdrDebevec)
                case "Reinhard":
                    img = self.toneMapReinhard(hdrDebevec)
                case "Drago":
                    img = self.toneMapDrago(hdrDebevec)
                case "Mantiuk":
                    img = self.toneMapMantiuk(hdrDebevec)

        # We convert to BGR matrix.
        img = clip(img * 255, 0, 255).astype('uint8')

        info("Images fusion done")

        return img

    # Apply simple tone mapping.
    def toneMapSimple(self, hdrDebevec):

        toneMap = createTonemap(gamma=config.SimpleGamma)
        img = toneMap.process(hdrDebevec)
        return img

    # Apply Reinhard method tone mapping.
    def toneMapReinhard(self, hdrDebevec):

        toneMap = createTonemapReinhard(config.ReinhardGamma,
                                        config.ReinhardIntensity,
                                        config.ReinhardLight,
                                        config.ReinhardColor)

        img = toneMap.process(hdrDebevec)
        return img

    # Apply Drago method tone mapping.
    def toneMapDrago(self, hdrDebevec):

        toneMap = createTonemapDrago(config.DragoGamma,
                                     config.DragoSaturation,
                                     config.DragoBias)
        img = toneMap.process(hdrDebevec)
        img *= 3
        return img

    # Apply Mantiuk method tone mapping.
    def toneMapMantiuk(self, hdrDebevec):

        toneMap = createTonemapMantiuk(config.MantiukGamma,
                                       config.MantiukScale,
                                       config.MantiukSaturation)
        img = toneMap.process(hdrDebevec)
        img *= 3
        return img

    # Show captured image.
    def showImage(self, img, title=""):
        self.displayImgEvent.wait(10)
        self.displayImgSig.emit(img, title)
        self.displayImgEvent.clear()

    # Show histogram of captured image.
    def showHist(self, img, title=""):
        self.plotHistogramEvent.wait(10)
        self.plotHistogramSig.emit(img, title)
        self.plotHistogramEvent.clear()

    # This function is used to name the test files.
    def testFileName(self):

        i = 1
        while True:
            self.imageName = "Test{:05d}.jpg".format(i)

            self.filename = config.capFolder.strip() + "/" + self.imageName
            if Path(self.filename).exists():
                i += 1
                continue
            else:
                break

    def finalizeImage(self, img):

        match config.lastMode:

            case "P":
                self.imageName = "Previous " + str(config.numImgRec - 1)

            case "T":
                self.testFileName()

            case "C":
                self.imageName = "img{:05d}.jpg".format(config.fileNumber)

        # Sharpness index calculation and display.
        # Only for preview images.
        if (config.lastMode == "P" and config.showSharp and
                config.motorNotMoving):

            img = self.drawImageSharpness(img)

        # Image resize.
        img = self.imageResize(img)

        # The image histogram is displayed.
        if config.showHist:
            self.showHist(img, self.imageName)

        # Rounding the image angles.
        if config.roundcorns:
            img = self.roundCorners(img)

        # The image is shown.
        self.showImage(img, self.imageName)

        return img

    # Function to save bracketing image files.
    def writeBracketImgFile(self, img):

        if config.lastMode == "T":
            self.testFileName()

            filename = (self.filename[:-4] +
                        "-{:02d}.jpg".format(self.indexETM + 1))

            filename = Path(filename)

        else:
            filename = (Path(config.capFolder.strip()
                        + "/img{:05d}-{:02d}.jpg".format(config.fileNumber,
                                                       self.indexETM + 1)))

        # We encode img in jpg.
        (ret, imgJpg) = imencode(".jpg", img, (int(IMWRITE_JPEG_QUALITY), 97))

        imgJpg = imgJpg.tobytes()

        # We add exif information.
        imgExif = Image(imgJpg)

        imgExif.datetime = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
        imgExif.make = "Raspberry Pi"
        imgExif.model = "HQ Camera"
        imgExif.exposure_time = self.exposureTime

        # Save the image.
        with (open(filename, "wb")) as imfile:
            imfile.write(imgExif.get_file())

    def writeImgFile(self, img):

        self.filename = config.capFolder.strip() + "/" + self.imageName

        with open(Path(self.filename), "wb"):

            # Write JPG file.
            imwrite(self.filename, img,
                    [int(IMWRITE_JPEG_QUALITY), 97])

        if config.testImg:
            info("Test image saved in: " + str(self.filename))
            config.testImg = False

        else:
            info("Captured image saved in: " + str(self.filename))

   # With this function the server is requested to capture and send a new
   # image.
    def newImage(self):
        config.ctrlConn.write(newImage + "\n")
        config.ctrlConn.flush()
        info("Image " + str(config.numImgRec) + " requested")

    # Processing functions of the information received from the server.

    # Flag e -> automatic exposure time.
    def imgflag_e(self):
        ssAE = unpack("<l", self.conn.read(calcsize("<l")))[0]
        again = unpack("<f", self.conn.read(calcsize("<f")))[0]
        dgain = unpack("<f", self.conn.read(calcsize("<f")))[0]
        framerate = unpack("<f", self.conn.read(calcsize("<f")))[0]
        self.updateAESig.emit(ssAE, again, dgain, framerate)

    # Flag f -> exposure time and analog and digital gains.
    def imgFlag_f(self):
        ss = unpack("<l", self.conn.read(calcsize("<l")))[0]
        again = unpack("<f", self.conn.read(calcsize("<f")))[0]
        dgain = unpack("<f", self.conn.read(calcsize("<f")))[0]
        framerate = unpack("<f", self.conn.read(calcsize("<f")))[0]
        self.updateSSSig.emit(ss, again, dgain, framerate)

    # Flag g -> blue and red gains.
    def imgFlag_g(self):
        gblue = round(unpack("<f", self.conn.read(calcsize("<f")))[0], 2)
        gred = round(unpack("<f", self.conn.read(calcsize("<f")))[0], 2)

        self.updateGainsSig.emit(gblue, gred)

    def imgFlag_spab(self):
        self.exposureTime = unpack("<i", self.conn.read(calcsize("<i")))[0]
        self.imageLen = unpack("<L", self.conn.read(calcsize("<L")))[0]

        # Save image data to temporary storage.
        self.imageStream.write(self.conn.read(self.imageLen))
        self.imageStream.seek(0)

        # File to opencv image.
        self.cvimg = imdecode(fromstring(self.imageStream.read(self.imageLen),
                                         dtype=uint8), IMREAD_COLOR)

    # Preview Image.
    def imgFlag_p(self):

        if type(self.cvimg) != ndarray:
            return

        info("Preview image " + str(config.numImgRec) + " received" +
             " - " + str(self.imageLen) + " bytes - Exp. time " +
             str(self.exposureTime) + " us")

        # The received image number is increased.
        config.numImgRec += 1

        # New image is requested from the server.
        if config.prevOn:
            self.newImage()

        self.cvimg = self.postProcess(self.cvimg)
        self.cvimg = self.finalizeImage(self.cvimg)

    # Digitized frame with a single image.
    def imgFlag_s(self):

        info("Single image " + str(config.numImgRec) + " received" +
             " - " + str(self.imageLen) + " bytes - Exp. time " +
             str(self.exposureTime) + " us")

        # The received image number is increased.
        config.numImgRec += 1

        # New image is requested from the server.
        if (config.captureOn and config.fileNumber < config.frameLimit):
            self.newImage()

        else:
            self.enableCaptureWidgetsSig.emit()

        self.cvimg = self.postProcess(self.cvimg)
        self.cvimg = self.finalizeImage(self.cvimg)
        self.writeImgFile(self.cvimg)

        if config.lastMode == "C":

            if config.fileNumber >= config.frameLimit:
                # We finished capture.
                self.endCaptureSig.emit()
                # We enable disabled widgets during capture.
                self.enableCaptureWidgetsSig.emit()

            # We increase file number.
            config.fileNumber += 1

    # Digitized frame with multiple images merged.
    # One of several bracketing images.
    def imgFlag_a(self):

        # Permission to save bracketing images.
        if not config.saveBracketImg and not self.indexETM:
            self.saveBracketPerm = False

        elif config.saveBracketImg and not self.indexETM:
            self.saveBracketPerm = True

        info("Bracketing image " + str(config.numImgRec) + " received"
             + " - " + str(self.imageLen) + " bytes - Exp. time "
             + str(self.exposureTime) + " us")

        self.cvimg = self.postProcess(self.cvimg)

        # The image is saved in a list to later perform the fusion of the
        # images.

        self.imglist.append(self.cvimg)

        # The HDR Debevec algorithm uses time in s.
        self.exposureTime = float(self.exposureTime * 1e-6)
        config.exposureTimes[self.indexETM] = self.exposureTime

        # The bracketing image is saved if this option is selected.

        if self.saveBracketPerm:
            self.writeBracketImgFile(self.cvimg)

        # The index is increased.

        self.indexETM += 1

    # The last of several bracketing images.
    def imgFlag_b(self):

        info("Last bracketing image " + str(config.numImgRec) + " received" +
             " - " + str(self.imageLen) + " bytes - Exp. time " +
             str(self.exposureTime) + " us")

        # The received image number is increased.
        config.numImgRec += 1

        # New image is requested from the server.
        if (config.captureOn and config.fileNumber < config.frameLimit):
            self.newImage()

        else:
            self.enableCaptureWidgetsSig.emit()

        self.cvimg = self.postProcess(self.cvimg)

        # The image is saved in a list to later perform the fusion of the
        # images.
        self.imglist.append(self.cvimg)

        # The HDR Debevec algorithm uses time in s.
        self.exposureTime = float(self.exposureTime * 1e-6)
        config.exposureTimes[self.indexETM] = self.exposureTime

        # The bracketing image is saved if this option is selected.

        if self.saveBracketPerm:
            self.writeBracketImgFile(self.cvimg)

        self.cvimg = self.blendImgList()
        self.cvimg = self.finalizeImage(self.cvimg)
        self.writeImgFile(self.cvimg)

        # Cleaning the list of images and exposure times.
        self.imglist = []
        self.indexETM = 0

        if config.lastMode == "C":

            if config.fileNumber >= config.frameLimit:
                # We finished capture.
                self.endCaptureSig.emit()
                # We enable disabled widgets during capture.
                self.enableCaptureWidgetsSig.emit()

            # We increase file number.
            config.fileNumber += 1

    # Imaging thread main loop.

    def run(self):
        info("Executing main function of image thread")

        while True:

            # The flag of the information sent by the server is obtained.
            self.imgflag = self.conn.read(1)
            try:
                self.imgflag = self.imgflag.decode()
            except:
                continue

            # Treatment of data sent by the server.
            match self.imgflag:

                # Flag f -> exposure time and analog and digital gains.
                case "f":
                    self.imgFlag_f()

                # Flag c -> frame advance.
                case "c":
                    self.updateFrameNumSig.emit("c")

                # Flag C -> reverse of a frame.
                case "C":
                    self.updateFrameNumSig.emit("C")

                # Digitized frame with bracketing merged images.
                # Flag a -> image from a series of images to merge.
                # One of several bracketing images.
                case "a":
                    self.imgFlag_spab()
                    self.imgFlag_a()
                    # Clearing the temporary storage of the image received from
                    # the server.
                    self.imageStream.seek(0)
                    self.imageStream.truncate()

                # Flag b -> last image of the serie.
                case "b":
                    self.imgFlag_spab()
                    self.imgFlag_b()
                    # Clearing the temporary storage of the image received from
                    # the server.
                    self.imageStream.seek(0)
                    self.imageStream.truncate()

                # Flag p -> preview image.
                case "p":
                    self.imgFlag_spab()
                    self.imgFlag_p()
                    # Clearing the temporary storage of the image received from
                    # the server.
                    self.imageStream.seek(0)
                    self.imageStream.truncate()

                # Flag s -> single capture image.
                case "s":
                    self.imgFlag_spab()
                    self.imgFlag_s()
                    # Clearing the temporary storage of the image received from
                    # the server.
                    self.imageStream.seek(0)
                    self.imageStream.truncate()

                # Flag m -> motor stopped.
                case "m":
                    self.motorStoppedSig.emit()

                # Flags l -> light on and L -> light off.
                case "l" | "L":
                    self.lightSig.emit(self.imgflag)

                # Flag g -> red and blue gains.
                case "g":
                    self.imgFlag_g()

                # Flag e -> automatic exposure time.
                case "e":
                    self.imgflag_e()

                # Flag T -> terminate thread execution.
                case "T":
                    break

                # Flag X -> application output reported by server.
                case "X":
                    self.exitSig.emit(True)
                    break

        self.conn.close()
