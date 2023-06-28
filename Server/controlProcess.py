"""
DSuper8 project based on Joe Herman's rpi-film-capture.

Software modified by Manuel Ángel.

User interface redesigned by Manuel Ángel.

controlProcess.py: Control of lighting and motor movement.

Latest version: 20230430.
"""

from time import sleep

import pigpio

from logging import info

from threading import Lock

from multiprocessing import Process, Event, Queue, Value

# Our configuration module.
import config

# BCM pin numbering is used.
# Illumination control: pin 0-> off 1-> on.
lightPin = config.lightPin

# Stepper motor control pins.
# Motor activation: 0-> enabled 1-> disabled.
sleepPin = config.sleepPin

# Direction: 0-> backward 1-> forward.
dirPin = config.dirPin

# Spin pulses.
pulsePin = config.pulsePin

# They are used to activate and deactivate the motor.
enabled = False
disabled = True

# Turn on, turn off:
on = 1
off = 0

# Connection with the pigpio daemon.
pi = pigpio.pi('localhost', 8889)

# We configure pins as output.
pi.set_mode(lightPin, pigpio.OUTPUT)
pi.set_mode(sleepPin, pigpio.OUTPUT)
pi.set_mode(dirPin, pigpio.OUTPUT)
pi.set_mode(pulsePin, pigpio.OUTPUT)

# Management of the GPIO port for lighting control and motor movement.
class DS8Control():

    # Image capture event.
    capEvent = Event()

    # Queue for sending orders to the motor control process MotorDriver.
    # The direction of rotation and the number of advance frames will be sent.
    motorQueue = Queue()

    def __init__(self, capEvent, motorQueue):

        self.capEvent = capEvent
        self.motorQueue = motorQueue

        # The motor starts. According to tests carried out, it is advisable not
        # to activate and deactivate the motor continuously. Operation is more
        # precise and smoother if the motor is permanently active.
        self.motorWake()

        # Engine status:
        # 0 -> stop
        # 1 -> advance
        # -1 -> recoil
        self.motorstate = 0

    # lightCheckbox
    def lightOn(self):
        pi.write(lightPin, on)

    def lightOff(self):
        pi.write(lightPin, off)

    # fRevButton
    def motorRev(self):
        if self.motorstate:
            self.motorStop()
        # cb -> continuous recoil
        self.motorQueue.put(["cb", 0])
        self.capEvent.set()
        self.motorstate = -1

    # reverseButton
    def revFrame(self, num):
        if self.motorstate:
            self.motorStop()
        while self.capEvent.is_set():
            sleep(0.5)
        # b -> recoil, num -> number of frames
        self.motorQueue.put(["b", num])
        self.capEvent.set()
        self.motorstate = -1

    # stopButton
    def motorStop(self):
        # s -> motor stop
        if self.motorstate:
            self.motorQueue.put(["s", 0])
            self.motorstate = 0
        else:
            return

    # forwardButton
    def fwdFrame(self, num):
        if self.motorstate:
            self.motorStop()
        while self.capEvent.is_set():
            sleep(0.5)
        # f -> advance, num -> number of frames
        self.motorQueue.put(["f", num])
        self.capEvent.set()
        self.motorstate = 1

    # ffdButton
    def motorFwd(self):
        if self.motorstate:
            self.motorStop()
        # cf -> continuous advance
        self.motorQueue.put(["cf", 0])
        self.capEvent.set()
        self.motorstate = 1

    def cleanup(self):
        self.lightOff()
        self.motorStop()
        self.motorSleep()
        pi.stop()
        info("GPIO cleaning done")

    def motorWake(self):
        pi.write(sleepPin, enabled)
        info("Motor on")
        sleep(0.5)

    def motorSleep(self):
        pi.write(sleepPin, disabled)
        info("Motor off")
        sleep(0.5)

# Very simple class designed to advance frames in another process during
# captures, so a different kernel can handle it and will not delay the
# photograph, or vice versa.
class MotorDriver(Process):

    # Photo capture event.
    capEvent = Event()

    # Application exit event.
    appExitEvent = Event()

    # Queue for receiving orders to the motor control process.
    # The direction of rotation and the number of advance frames will be
    # received.
    motorQueue = Queue()

    # Blocking the connection used for sending images.
    connectionLock = Lock()

    # Shared variable.This variable determines the sending of forward and
    # backward signals of frames, for updating the client's position indicator.
    # 0 -> no update frame
    # 1 -> update frame
    svUpdateFrame = Value("I", 0)

   # Shared variable. Determines the sending of engine stop signals.
    # 0 -> no send stop signals
    # 1 -> send stop signals
    svSendStop = Value("I", 1)

    def __init__(self, capEvent, motExitEvent, motorQueue, connectionLock,
                  svUpdateFrame, svSendStop):
        super(MotorDriver, self).__init__()
        info("Starting MotorDriver")

        self.capEvent = capEvent
        self.motExitEvent = motExitEvent
        self.motorQueue = motorQueue
        self.connectionLock = connectionLock
        self.svUpdateFrame = svUpdateFrame
        self.svSendStop = svSendStop

        # Pulse wave identifier.
        self.wid = 0

        # Pulse chain.
        self.chain = []

        # Number of steps required to move forward/backward one frame.
        # For smooth operation we use 32 microsteps per step, has the
        # disadvantage of slowness.
        # Due to the wheel-pinion mesh, only half a revolution of the motor is
        # needed to advance one frame.
        self.stepsPerFrame = config.stepsPerFrame

        # Parameters used to create the pulse chain.
        self.x = self.stepsPerFrame % 256
        self.y = int(self.stepsPerFrame / 256)

        # They are used to determine the direction of rotation of the motor.
        self.backward = config.backward
        self.forward = config.forward

        # Variable that contains the order.
        self.order = ""

        # Variable that indicates continuous rotation of the motor if True.
        self.turn = False

        # Variable that determines the number of frames that the motor must
        # advance/reverse.
        self.numframes = 0

        # Engine advance pulse chain.
        self.createChain()

        # Frame advance time in s.
        self.tFrameAdv = config.stepsPerFrame * pi.wave_get_micros() * 1e-6

    # Definition of the motor advance pulse chain.
    def createChain(self):

        # We create the pulses that make up the wave.
        pul = []

        # Time in us of a half-period of the wave.
        tus = int(500000 / config.freq)

        # pin ON
        pul.append(pigpio.pulse(1 << pulsePin, 0, tus))

        # pin OFF
        pul.append(pigpio.pulse(0, 1 << pulsePin, tus))

        # We clean pre-existing waves.
        pi.wave_clear()

        # We add the previously created pulses.
        pi.wave_add_generic(pul)

        # We create the wave.
        self.wid = pi.wave_create()

        # Chain of pulses required to advance one frame.
        self.chain += [255, 0, self.wid, 255, 1, self.x, self.y]

    # Main control loop of motor rotation.
    def run(self):
        info("Running motor turn process")
        try:
            while not self.motExitEvent.is_set():

                if not self.motorQueue.empty():
                    msg = self.motorQueue.get()
                    self.order = msg[0]
                    self.numframes = msg[1]
                else:
                    continue

                if self.order == "f":
                    pi.write(dirPin, self.forward)
                    self.turnFrames(self.numframes, "f")
                    # Motor stopped.
                    info("Motor stop")
                    self.capEvent.clear()
                    if self.svSendStop.value:
                        self.sendFrameMove("m")

                elif self.order == "cf":
                    pi.write(dirPin, self.forward)
                    self.turn = True
                    self.continuousTurn("f")
                    # Motor stopped.
                    info("Motor stop")
                    self.capEvent.clear()
                    if self.svSendStop.value:
                        self.sendFrameMove("m")

                # In order to eliminate the small error that originates from
                # vertical scrolling when moving back frames, go back one
                # additional frame and then advance one frame.
                elif self.order == "cb":
                    pi.write(dirPin, self.backward)
                    self.turn = True
                    self.continuousTurn("b")
                    sleep(0.5)
                    pi.write(dirPin, self.forward)
                    self.turnFrames(1, "f")
                    # Motor stopped.
                    info("Motor stop")
                    self.capEvent.clear()
                    if self.svSendStop.value:
                        self.sendFrameMove("m")

                elif self.order == "b":
                    pi.write(dirPin, self.backward)
                    self.turnFrames(self.numframes + 1, "b")
                    sleep(0.5)
                    pi.write(dirPin, self.forward)
                    self.turnFrames(1, "f")
                    # Motor stopped.
                    info("Motor stop")
                    self.capEvent.clear()
                    if self.svSendStop.value:
                        self.sendFrameMove("m")

                elif self.order == "s":
                    self.turn = False

        except Exception as e:
            info(getattr(e, 'message', repr(e)))

        finally:
            info("End of the motor turning process")

    def turnFrames(self, numframes, direction):
        if direction == "f":
            if numframes == 1:
                info("1 frame advance")
            else:
                info(str(numframes) + " frames advance")

        if self.order == "b":
            if numframes == 1:
                info("1 frame reverse")
            else:
                info(str(numframes) + " frames reverse")

        for i in range(numframes):
            self.motorTurn()
            if direction == "f" and self.svUpdateFrame.value:
                self.sendFrameMove("c")
            elif direction == "b" and self.svUpdateFrame.value:
                self.sendFrameMove("C")

            # We check stop order.
            if not self.motorQueue.empty():
                msg = self.motorQueue.get()
                self.order = msg[0]
                if self.order == "s":
                    break

    def continuousTurn(self, direction):
        if direction == "f":
            info("Continuous advance motor")
        elif direction == "b":
            info("Continuous reverse motor")

        # Continuous turning is done by full frames.
        while self.turn:
            self.motorTurn()
            if direction == "f" and self.svUpdateFrame.value:
                self.sendFrameMove("c")
            elif direction == "b" and self.svUpdateFrame.value:
                self.sendFrameMove("C")

            # We check stop order.
            if not self.motorQueue.empty():
                msg = self.motorQueue.get()
                self.order = msg[0]
                if self.order == "s":
                    self.turn = False
                else:
                    continue

    def motorTurn(self):
        # We send the chain for the advance of a frame.
        pi.wave_chain(self.chain)
        sleep(self.tFrameAdv)

    # Sending forward or backward frame movement signal.
    def sendFrameMove(self, flag):

        with self.connectionLock:

            config.imgConn.write(flag.encode())
            config.imgConn.flush()

        if flag == "c":
            info("Frame advance signal sent")
        elif flag == "C":
            info("Frame reverse signal sent")
        elif flag == "m":
            info("Motor stopped signal sent")
