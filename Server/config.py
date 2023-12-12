"""
DSuper8 project based on Joe Herman's rpi-film-capture.

Software modified by Manuel Ángel.

User interface redesigned by Manuel Ángel.

config.py: Global server variables.

Latest version: 20231130.
"""

# Global server variables are defined here.
# pool = []
imgConn = None
ctrlConn = None
ctrlReader = None
nullFile = "/dev/null"

# In auto exposure it is used to determine the exposure metering area.
# AEScalerCrop = (x_offset, y_offset, width, height)
AEScalerCrop = (310, 330, 3310, 2520)

# This variable is used to set the exposure time in bracketed exposures.
# If the exposure time of the camera differs from the theoretical one by a
# value lower than that set in the variable, it is accepted as valid.
# Initially it is fixed at 50 us.
timeExpTolerance = 50

# Number of holding frames required to achieve auto exposure convergence.
AEWaitFrames = 25

# Number of retries to reach the defined exposure time.
numOfRetries = 100

# GPIO pin assignment.
# BCM pin numbering is used.

# Illumination control pin: 0-> off 1-> on.
lightPin = 6

# Stepper motor control pins.
# Motor activation: 0-> enabled 1-> disabled.
sleepPin = 13

# Direction: 0-> backward 1-> forward.
dirPin = 19

# Spin pulses.
pulsePin = 26

# Number of steps required to move forward/backward one frame.
# The stepper motor used is 200 steps per revolution.
# For smooth operation we use 32 microsteps per step, it has the drawback of
# slowness.
# Due to the wheel-pinion mesh, it only takes half a full revolution of the
# engine to advance one frame.
# Therefore we have: number of microsteps = 200 * 32 / 2 = 3200
stepsPerFrame = 3200

# Frequency in Hz of the pulses to be sent to the motor driver.
# It should be chosen so that it is as high as possible but without the motor
# losing steps.
freq = 8000

# They are used to determine the direction of rotation of the motor.
backward = False
forward = True
