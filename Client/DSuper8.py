#!/usr/bin/python3

"""
DSuper8 project based on Joe Herman's rpi-film-capture.

Software modified by Manuel Ángel.

User interface redesigned by Manuel Ángel.

DSuper8.py: Main client software program.

Last version: 20230430.
"""

from socket import socket, AF_INET, SOCK_STREAM

from pathlib import Path

from sys import argv, stdout, exit

from logging import INFO, basicConfig, info

from configparser import Error

from PyQt6.QtWidgets import QApplication, QStyleFactory

from PyQt6.QtCore import QCoreApplication, QDir


# Our own modules.

# The global variables of the modules are defined here.
import config

# Classes for the definition of our UI and for the image window.
from DS8Dialogs import DS8Dialog, DS8ImgDialog

# Class and support functions for the reading and treatment of images.
from DS8ImgThread import imgThread

# Creation of 2 connections: one for sending control sequences and another for
# receiving image data.


def setupConns(image_socket, control_socket):
    try:
        imageSocket.connect((config.server_ip, 8000))
        controlSocket.connect((config.server_ip, 8001))
        imgConn = imageSocket.makefile("rb")
        ctrlConn = controlSocket.makefile("w")
        info("Connections with the server established")
        return (imgConn, ctrlConn)

    except Exception as e:
        info(getattr(e, 'message', repr(e)))
        info("It seems that the server is not working")
        info("The server must be running before the client program starts")
        imageSocket.close()
        controlSocket.close()
        exit()


if __name__ == "__main__":
    # Severity level of the log set to INFO.
    basicConfig(stream=stdout, level=INFO, format="%(asctime)s - %(levelname)s " +
                "- %(message)s", datefmt="%Y-%m-%d %H:%M:%S")

    info("DSuper8 client software ver. 20230430")

    app = QApplication(argv)
    app.setStyle(QStyleFactory.create("Fusion"))

    # Path to the resources folder is configured.
    config.resourcesPath = QDir.currentPath() + "/Resources/"

    configError = False
    config.testImg = True

    # Establishing connections with the server.
    imageSocket = socket(AF_INET, SOCK_STREAM)
    controlSocket = socket(AF_INET, SOCK_STREAM)
    (imgConn, ctrlConn) = setupConns(imageSocket, controlSocket)
    config.ctrlConn = ctrlConn

    # Thread for receiving and processing the images sent by the server.
    imgthread = imgThread(imgConn, app)

    # Graphical user interface.
    winUI = DS8Dialog()

    # Loading the initial configuration.

    if Path(config.configFile.strip()).is_file():
        try:
            winUI.config.read([Path(config.configFile.strip())])
            if not winUI.config.validateConfigFile():
                raise Error
            winUI.config.updateUIfromConfig(winUI)
            winUI.configFileBox.setText(config.configFile)
            winUI.saveConfigButton.setEnabled(True)
            info(config.configFile + " configuration file loaded")

        except Error:
            configError = True
            info(config.configFile + " not a valid configuration file")

    else:
        configError = True
        info("Configuration file " + config.configFile + " does not exist")
        info("Modify path to the configuration file in config.py of the client"
             " program")

    if configError:
        winUI.configFileBox.setText("")
        winUI.saveConfigButton.setEnabled(False)
        info("Default configuration is loaded")

        # Load default settings.
        winUI.setDefaultConfiguration()

    # Image window.
    winImg = DS8ImgDialog(winUI)
    splash = winUI.lastShowImg
    winImg.displayImg(splash, "Splash")
    winImg.resize(config.imgWinWidth, config.imgWinHeight)

    # Slot configuration to allow the image sequence to update the image window
    # and user interface.
    winImg.setupThreadingUpdates(imgthread)
    winUI.setupThreadingUpdates(imgthread)

    # Image thread start.
    imgthread.start()
    info("Images thread started")

    # Initial server configuration to match the settings defined in the user
    # interface.
    winUI.sendInitConfig()

    # Enable/Disable controls to match settings loaded in initial setup.
    winUI.initPostCapture()

    # Show windows.
    winUI.show()
    winImg.show()
    info("Windows displayed")    

    winUI.updateStatus("Program started")

    rtnVal = app.exec()
    info("Windows closed")
    imageSocket.close()
    controlSocket.close()
    info("Server connections closed")
    info("Finalized")
    exit(rtnVal)
