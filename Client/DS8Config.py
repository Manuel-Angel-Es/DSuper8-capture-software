"""
DSuper8 project based on Joe Herman's rpi-film-capture.

Software modified by Manuel Ángel.

User interface redesigned by Manuel Ángel.

DS8Config.py: Module to save the configuration and restore it from a file.

Latest version: 20231130.
"""

from configparser import ConfigParser

from pathlib import Path

from logging import info

# Our configuration module and global variables.
import config


class DS8ConfigParser(ConfigParser):

    def updateConfigFromUI(self, ui):
        if not self.has_section("Setup"):
            self.add_section("Setup")
        if not self.has_section("Camera"):
            self.add_section("Camera")
        if not self.has_section("Capture"):
            self.add_section("Capture")
        if not self.has_section("Advanced"):
            self.add_section("Advanced")
        if not self.has_section("Post-capture"):
            self.add_section("Post-capture")
        if not self.has_section("HDR"):
            self.add_section("HDR")

        sec = "Setup"
        self.set(sec, "zoomdial", str(ui.zoomDial.value()))
        self.set(sec, "x_offset", str(ui.x_offset))
        self.set(sec, "y_offset", str(ui.y_offset))
        self.set(sec, "lightcheckbox", str(ui.lightCheckbox.isChecked()))
        self.set(sec, "startposcheckbox", str(ui.startPosCheckBox.isChecked()))

        sec = "Camera"
        self.set(sec, "analoguegain", str(round(ui.analogueGainBox.value(), 1)))
        self.set(sec, "evbox", str(round(ui.EVBox.value(), 1)))
        self.set(sec, "awbbox", str(ui.awbBox.currentIndex()))
        self.set(sec, "bluegain", str(round(ui.blueGainBox.value(), 2)))
        self.set(sec, "redgain", str(round(ui.redGainBox.value(), 2)))
        self.set(sec, "manualbluegain", str(ui.manualBlueGain))
        self.set(sec, "manualredgain", str(ui.manualRedGain))
        self.set(sec, "brightness", str(round(ui.brightnessBox.value(), 2)))
        self.set(sec, "contrast", str(round(ui.contrastBox.value(), 2)))
        self.set(sec, "saturation", str(round(ui.saturationBox.value(), 2)))

        sec = "Capture"
        self.set(sec, "endframebox", str(ui.endFrameBox.value()))
        self.set(sec, "bracketingbox", str(ui.bracketingBox.value()))
        self.set(sec, "oldbracketingbox", str(ui.oldbracketingBox))
        self.set(sec, "saveallcheckbox", str(ui.saveAllCheckBox.isChecked()))
        self.set(sec, "stopsbox", str(round(ui.stopsBox.value(), 1)))
        self.set(sec, "oldstopsbox", str(ui.oldStopsBox))
        self.set(sec, "timeexpbox", str(round(ui.manExpTime, 1)))
        self.set(sec, "autoexpcheckbox", str(ui.autoExpCheckBox.isChecked()))        
        if ui.capFolderBox.text() == "Select capture folder":
            self.set(sec, "capfolderbox", "")
        else:
            self.set(sec, "capfolderbox", ui.capFolderBox.text())
        self.set(sec, "framelcd", str(int(ui.frameLcd.value())))
        self.set(sec, "nextframebox", str(ui.nextFrameBox.value()))

        sec = "Advanced"
        self.set(sec, "vflipcheckbox", str(ui.vFlipCheckBox.isChecked()))
        self.set(sec, "hflipcheckbox", str(ui.hFlipCheckBox.isChecked()))
        self.set(sec, "bwcheckbox", str(ui.bwCheckBox.isChecked()))
        self.set(sec, "jpgcheckbox", str(ui.jpgCheckBox.isChecked()))
        self.set(sec, "rawcheckbox", str(ui.rawCheckBox.isChecked()))
        self.set(sec, "constraintmodebox", str(ui.constraintModeBox.currentIndex()))
        self.set(sec, "exposuremodebox", str(ui.exposureModeBox.currentIndex()))
        self.set(sec, "meteringmodebox", str(ui.meteringModeBox.currentIndex()))
        self.set(sec, "resolutionbox", str(ui.resolutionBox.currentIndex()))
        self.set(sec, "sharpnessbox", str(round(ui.sharpnessBox.value(), 1)))

        sec = "Post-capture"
        self.set(sec, "showhist", str(ui.showHist.isChecked()))
        self.set(sec, "oldshowhist", str(ui.oldShowHist))
        self.set(sec, "logarithmhist", str(ui.logarithmHist.isChecked()))
        self.set(sec, "sharpcheckbox", str(ui.sharpCheckBox.isChecked()))
        self.set(sec, "roundcorns", str(ui.roundCorns.isChecked()))
        self.set(sec, "rotationcheckbox", str(ui.rotationCheckBox.isChecked()))
        self.set(sec, "rotationbox", str(round(ui.rotationBox.value(), 1)))
        self.set(sec, "croppingcheckbox", str(ui.croppingCheckBox.isChecked()))
        self.set(sec, "croptopbox", str(ui.cropTopBox.value()))
        self.set(sec, "cropleftbox", str(ui.cropLeftBox.value()))
        self.set(sec, "croprightbox", str(ui.cropRightBox.value()))
        self.set(sec, "cropbottombox", str(ui.cropBottomBox.value()))

        sec = "HDR"
        self.set(sec, "mertperchigh", str(round(ui.PHighSpinBox.value(), 1)))
        self.set(sec, "mertperclow", str(round(ui.PLowSpinBox.value(), 1)))
        self.set(sec, "hdrmertens", str(ui.HDRMertensRadioButton.isChecked()))
        self.set(sec, "hdrdebevec", str(ui.HDRDebevecRadioButton.isChecked()))
        self.set(sec, "simple", str(ui.SimpleRadioButton.isChecked()))
        self.set(sec, "simplegammaspinbox", str(round(ui.SimpleGammaSpinBox.value(), 1)))
        self.set(sec, "reinhard", str(ui.ReinhardRadioButton.isChecked()))
        self.set(sec, "reinhardgammaspinbox", str(round(ui.ReinhardGammaSpinBox.value(), 1)))
        self.set(sec, "reinhardintensityspinbox", str(round(ui.ReinhardIntensitySpinBox.value(), 1)))
        self.set(sec, "reinhardlightspinbox", str(round(ui.ReinhardLightSpinBox.value(), 1)))
        self.set(sec, "reinhardcolorspinbox", str(round(ui.ReinhardColorSpinBox.value(), 1)))
        self.set(sec, "drago", str(ui.DragoRadioButton.isChecked()))
        self.set(sec, "dragogammaspinbox", str(round(ui.DragoGammaSpinBox.value(), 1)))
        self.set(sec, "dragosaturationspinbox", str(round(ui.DragoSaturationSpinBox.value(), 1)))
        self.set(sec, "dragobiasspinbox", str(round(ui.DragoBiasSpinBox.value(), 2)))
        self.set(sec, "mantiuk", str(ui.MantiukRadioButton.isChecked()))
        self.set(sec, "mantiukgammaspinbox", str(round(ui.MantiukGammaSpinBox.value(), 1)))
        self.set(sec, "mantiuksaturationspinbox", str(round(ui.MantiukSaturationSpinBox.value(), 1)))
        self.set(sec, "mantiukscalespinbox", str(round(ui.MantiukScaleSpinBox.value(), 2)))

    def updateUIfromConfig(self, ui):
        sec = "Setup"
        ui.zoomDial.setValue(self.getint(sec, "zoomdial"))
        ui.x_offset = (self.getint(sec, "x_offset"))
        ui.y_offset = (self.getint(sec, "y_offset"))
        ui.lightCheckbox.setChecked(self.getboolean(sec, "lightcheckbox"))

        sec = "Camera"
        ui.analogueGainBox.setValue(self.getfloat(sec, "analoguegain"))
        ui.EVBox.setValue(self.getfloat(sec, "evbox"))
        ui.awbBox.setCurrentIndex(self.getint(sec, "awbbox"))
        ui.blueGainBox.setValue(self.getfloat(sec, "bluegain"))
        ui.redGainBox.setValue(self.getfloat(sec, "redgain"))
        ui.manualBlueGain = (self.getfloat(sec, "manualbluegain"))
        ui.manualRedGain = (self.getfloat(sec, "manualredgain"))
        ui.brightnessBox.setValue(self.getfloat(sec, "brightness"))
        ui.contrastBox.setValue(self.getfloat(sec, "contrast"))
        ui.saturationBox.setValue(self.getfloat(sec, "saturation"))

        sec = "Capture"
        ui.endFrameBox.setValue(self.getint(sec, "endframebox"))
        ui.bracketingBox.setValue(self.getint(sec, "bracketingbox"))
        ui.oldbracketingBox = self.getint(sec, "oldbracketingbox")
        ui.saveAllCheckBox.setChecked(self.getboolean(sec, "saveallcheckbox"))
        ui.stopsBox.setValue(self.getfloat(sec, "stopsbox"))
        ui.oldStopsBox = self.getfloat(sec, "oldstopsbox")
        ui.timeExpBox.setValue(self.getfloat(sec, "timeexpbox"))
        ui.autoExpCheckBox.setChecked(self.getboolean(sec, "autoexpcheckbox"))        
        capFolder = self.get(sec, "capfolderbox").strip()
        if capFolder and Path(capFolder).is_dir():
            ui.capFolderBox.setText(capFolder)
        else:
            ui.capFolderBox.setText("")
            info(capFolder + " folder does not exist")
        config.frameNumber = self.getint(sec, "framelcd")
        config.fileNumber = config.frameNumber
        ui.frameLcd.display(config.frameNumber)
        ui.nextFrameBox.setValue(self.getint(sec, "nextframebox"))

        sec = "Advanced"
        ui.vFlipCheckBox.setChecked(self.getboolean(sec, "vflipcheckbox"))
        ui.hFlipCheckBox.setChecked(self.getboolean(sec, "hflipcheckbox"))
        ui.bwCheckBox.setChecked(self.getboolean(sec, "bwcheckbox"))
        ui.jpgCheckBox.setChecked(self.getboolean(sec, "jpgcheckbox"))
        ui.rawCheckBox.setChecked(self.getboolean(sec, "rawcheckbox"))
        ui.constraintModeBox.setCurrentIndex(self.getint(sec, "constraintmodebox"))
        ui.exposureModeBox.setCurrentIndex(self.getint(sec, "exposuremodebox"))
        ui.meteringModeBox.setCurrentIndex(self.getint(sec, "meteringmodebox"))
        ui.resolutionBox.setCurrentIndex(self.getint(sec, "resolutionbox"))
        ui.sharpnessBox.setValue(self.getfloat(sec, "sharpnessbox"))

        sec = "Post-capture"
        ui.showHist.setChecked(self.getboolean(sec, "showhist"))
        ui.oldShowHist = self.getboolean(sec, "oldshowhist")
        ui.logarithmHist.setChecked(self.getboolean(sec, "logarithmhist"))
        ui.sharpCheckBox.setChecked(self.getboolean(sec, "sharpcheckbox"))
        ui.roundCorns.setChecked(self.getboolean(sec, "roundcorns"))
        ui.rotationCheckBox.setChecked(self.getboolean(sec, "rotationcheckbox"))
        ui.rotationBox.setValue(self.getfloat(sec, "rotationbox"))
        ui.croppingCheckBox.setChecked(self.getboolean(sec, "croppingcheckbox"))
        ui.cropTopBox.setValue(self.getint(sec, "croptopbox"))
        ui.cropLeftBox.setValue(self.getint(sec, "cropleftbox"))
        ui.cropRightBox.setValue(self.getint(sec, "croprightbox"))
        ui.cropBottomBox.setValue(self.getint(sec, "cropbottombox"))

        sec = "HDR"
        ui.PHighSpinBox.setValue(self.getfloat(sec, "mertperchigh"))
        ui.PLowSpinBox.setValue(self.getfloat(sec, "mertperclow"))
        ui.HDRMertensRadioButton.setChecked(self.getboolean(sec, "hdrmertens"))
        ui.HDRDebevecRadioButton.setChecked(self.getboolean(sec, "hdrdebevec"))
        ui.SimpleRadioButton.setChecked(self.getboolean(sec, "simple"))
        ui.SimpleGammaSpinBox.setValue(self.getfloat(sec, "simplegammaspinbox"))
        ui.ReinhardRadioButton.setChecked(self.getboolean(sec, "reinhard"))
        ui.ReinhardGammaSpinBox.setValue(self.getfloat(sec,
                                                       "reinhardgammaspinbox"))
        ui.ReinhardIntensitySpinBox.setValue(self.getfloat
                                             (sec, "reinhardintensityspinbox"))
        ui.ReinhardLightSpinBox.setValue(self.getfloat
                                         (sec, "reinhardlightspinbox"))
        ui.ReinhardColorSpinBox.setValue(self.getfloat
                                         (sec, "reinhardcolorspinbox"))
        ui.DragoRadioButton.setChecked(self.getboolean(sec, "drago"))
        ui.DragoGammaSpinBox.setValue(self.getfloat(sec, "dragogammaspinbox"))
        ui.DragoSaturationSpinBox.setValue(self.getfloat
                                           (sec, "dragosaturationspinbox"))
        ui.DragoBiasSpinBox.setValue(self.getfloat(sec, "dragobiasspinbox"))
        ui.MantiukRadioButton.setChecked(self.getboolean(sec, "mantiuk"))
        ui.MantiukGammaSpinBox.setValue(self.getfloat
                                        (sec, "mantiukgammaspinbox"))
        ui.MantiukSaturationSpinBox.setValue(self.getfloat
                                             (sec, "mantiuksaturationspinbox"))
        ui.MantiukScaleSpinBox.setValue(self.getfloat
                                        (sec, "mantiukscalespinbox"))

        # It is configured last so that the rest of the settings are
        # made.
        sec = "Setup"
        ui.startPosCheckBox.setChecked(self.getboolean(sec, "startposcheckbox"))

    # This function is to check the validity of the configuration file.
    # The existence and not duplication of all the sections and options of
    # the file is checked.
    # It is also checked that there are no options without associated value.
    # The function returns False if it encounters any errors.

    def validateConfigFile(self):

        ok = True

        # There must be 6 sections.
        if len(self.sections()) != 6:
            ok = False

        # We check the existence of all sections.
        if ok:
            for section in ["Setup", "Camera", "Capture", "Advanced",
                            "Post-capture", "HDR"]:
                if section not in self.sections():
                    ok = False
                    break

        # We check the existence of all options.
        if ok and len(self.options("Setup")) != 5:
            ok = False

        if ok:
            for option in ["zoomdial", "x_offset", "y_offset", "lightcheckbox",
                           "startposcheckbox"]:
                if (option not in self.options("Setup")
                        or self.get("Setup", option).strip() == ""):
                    ok = False
                    break

        if ok and len(self.options("Camera")) != 10:
            ok = False

        if ok:
            for option in ["analoguegain", "evbox", "awbbox", "bluegain",
                           "redgain", "manualbluegain", "manualredgain",
                           "brightness", "contrast", "saturation"]:
                if (option not in self.options("Camera")
                        or self.get("Camera", option).strip() == ""):
                    ok = False
                    break

        if ok and len(self.options("Capture")) != 11:
            ok = False

        if ok:

            for option in ["endframebox", "bracketingbox", "oldbracketingbox",
                           "saveallcheckbox", "stopsbox", "oldstopsbox",
                           "autoexpcheckbox", "timeexpbox", "capfolderbox",
                           "framelcd", "nextframebox"]:
                if option not in self.options("Capture"):
                    ok = False
                    break

        # The "capfolderbox" option is allowed to be blank.
        if ok:
            for option in ["endframebox", "bracketingbox", "saveallcheckbox",
                           "stopsbox", "autoexpcheckbox", "timeexpbox",
                           "framelcd", "nextframebox"]:
                if self.get("Capture", option).strip() == "":
                    ok = False
                    break

        if ok and len(self.options("Advanced")) != 10:
            ok = False

        if ok:
            for option in ["vflipcheckbox", "hflipcheckbox", "bwcheckbox",
                           "jpgcheckbox", "rawcheckbox",
                           "constraintmodebox", "exposuremodebox",
                           "meteringmodebox", "resolutionbox", "sharpnessbox"]:
                if (option not in self.options("Advanced")
                        or self.get("Advanced", option).strip() == ""):
                    ok = False
                    break

        if ok and len(self.options("Post-capture")) != 12:
            ok = False

        if ok:
            for option in ["showhist", "oldshowhist", "logarithmhist", "sharpcheckbox",
                           "roundcorns", "rotationcheckbox", "rotationbox",
                           "croppingcheckbox", "croptopbox", "cropleftbox",
                           "croprightbox", "cropbottombox"]:
                if (option not in self.options("Post-capture")
                        or self.get("Post-capture", option).strip() == ""):
                    ok = False
                    break

        if ok and len(self.options("HDR")) != 19:
            ok = False

        if ok:
            for option in ["mertperchigh", "mertperclow", "hdrmertens",
                           "hdrdebevec", "simple", "simplegammaspinbox",
                           "reinhard", "reinhardgammaspinbox",
                           "reinhardintensityspinbox", "reinhardlightspinbox",
                           "reinhardcolorspinbox", "drago", "dragogammaspinbox",
                           "dragosaturationspinbox", "dragobiasspinbox",
                           "mantiuk", "mantiukgammaspinbox",
                           "mantiuksaturationspinbox", "mantiukscalespinbox"]:
                if (option not in self.options("HDR")
                        or self.get("HDR", option).strip == ""):
                    ok = False
                    break

        return ok
