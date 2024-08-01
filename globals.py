# GLOBALS.py

"""
LENGTH OF MESSAGE
"""
HEADER_BYTES = 3
PAYLOAD_BYTES = 8
MSG_BYTES = HEADER_BYTES + PAYLOAD_BYTES

"""
VOLTAGE GLOBAL VARIABLES
"""
# Voltage sample bias valid range
VBIAS_MIN   = -10.0
VBIAS_MAX   = 10.0

# Voltage piezo valid range
VPIEZO_MIN  = 0.0
VPIEZO_MAX  = 10.0

# Volts per step for voltage piezo
IZ_VOLTS_PER_STEP_MIN = 0.0002
IV_VOLTS_PER_STEP_MIN = 0.0004

# Voltage piezo delta
VPIEZO_DELTA_MIN = 0.0002

"""
NUMBER OF SETPOINTS AND SAMPLE SIZE GLOBAL VARIABLES
"""
SAMPLE_SIZE_MIN = 1
SAMPLE_SIZE_MAX = 1024

NUM_SETPOINTS_MIN = 1


"""
MESSAGE COMMAND GLOBAL VARIABLES
"""
# The message representation of different message types
MSG_A = 0X0A
MSG_B = 0X0B
MSG_C = 0X0C
MSG_D = 0X0D
MSG_E = 0X0E
MSG_F = 0X0F
MSG_X = 0x58

# The message representation of different step sizes
FULL_STEP       = 0x00
HALF_STEP       = 0x01
QUARTER_STEP    = 0x02
EIGHTH_STEP     = 0x03

# The distance in nanometers of the step sizes (rough estimate)
FULL_STEP_DISTANCE = 400
HALF_STEP_DISTANCE = 200
QUARTER_STEP_DISTANCE = 100
EIGHTH_STEP_DISTANCE = 50

# Direction the stepper motor is moving
DIR_UP          = 0x00
DIR_DOWN        = 0x01

# Number of steps to move the stepper motor by with user adjustment
NUM_STEPS = 1

"""
TIMING AND MESSAGE CHECKING
"""
# Time
TIMEOUT = 10.0
ONE_SECOND = 1.0
HALF_SECOND = 0.5
TENTH_SECOND = 0.1

# Attempts
MAX_ATTEMPTS = 10
SWEEP_MAX_ATTEMPTS = 1

"""
BAUD RATE
"""
BAUDRATE = 460800

"""
GRAPHICAL DISPLAY PARAMETERS
"""
# these parameters will make the graphical displays readable (to avoid cluttered graphs)

# homepage graph will display this interval (in seconds) 
# i.e. the graph will display the most recent (X) second interval
HOMEPAGE_GRAPH_DISPLAY_TIME_INTERVAL = 10

# sweep windows will display this number of points at a time, may change as desired
SWEEP_GRAPH_DISPLAY_NUMBER_OF_POINTS = 200