# Game Window Settings
WIDTH = 1024
HEIGHT = 768
FPS = 60
BG_COLOR = (20, 20, 30)

# Player (Ric) Settings
PLAYER_SPEED = 300
PLAYER_SIZE = 40
PLAYER_COLOR = (0, 150, 255)
PLAYER_MAX_HEALTH = 3
PLAYER_ACCELERATION = 12.0  # Acceleration rate
PLAYER_DECELERATION = 6.0   # Deceleration rate
PLAYER_MAX_VELOCITY = 300   # Maximum velocity
PLAYER_INVULNERABILITY_DURATION = 2.0  # Seconds player is invulnerable after being hit
LASER_COOLDOWN = 0.5

# Shay (Robot) Settings
SHAY_SIZE = 35
SHAY_COLOR = (100, 255, 100)
SHAY_FOLLOW_SPEED = 2.0  # Higher value = more responsive following
SHAY_DIRECT_FOLLOW_THRESHOLD = 25  # Distance threshold for direct teleport
RICOCHET_ANGLE_INCREMENT = 2  # In degrees

# Laser Settings
LASER_COLOR = (255, 50, 50)
LASER_INDICATOR_COLOR = (50, 200, 255)
LASER_WIDTH = 3
LASER_INDICATOR_WIDTH = 2
LASER_DISPLAY_DURATION = 0.5  # Seconds that the laser visual effect is displayed

# Laser Impact Effect Settings
IMPACT_BASE_RADIUS = 20      # Base size of the impact circle
IMPACT_PULSE_RANGE = 12      # How much the impact size varies during pulsing
IMPACT_GLOW_MULTIPLIER = 1.5  # Size multiplier for outer glow effect (relative to base)
IMPACT_GLOW_ALPHA = 100      # Transparency of the glow effect (0-255)
IMPACT_PULSE_SPEED = 20      # Speed of the pulsing animation

# Reflection Effect Settings
REFLECTION_LINE_COUNT = 3    # Number of reflection lines
REFLECTION_MIN_LENGTH = 1.5  # Minimum length multiplier relative to SHAY_SIZE
REFLECTION_MAX_LENGTH = 2.5  # Maximum length multiplier relative to SHAY_SIZE
REFLECTION_LINE_WIDTH_DIVISOR = 2  # Divides main laser width to get reflection line width

# Enemy Settings
ENEMY_SIZE = 35
ENEMY_BASE_SPEED = 50
ENEMY_COLORS = [(255, 100, 100), (255, 150, 50), (255, 200, 0), (200, 100, 200), (255, 50, 200)]
VULNERABLE_ARC_SIZE = 90  # Size of the vulnerable arc in degrees

# Game State
GAME_STATE_MENU = 0
GAME_STATE_PLAYING = 1
GAME_STATE_WAVE_TRANSITION = 2
GAME_STATE_GAME_OVER = 3
GAME_STATE_VICTORY = 4

# Wave Settings
TOTAL_WAVES = 5
WAVE_TRANSITION_TIME = 3  # seconds
ENEMY_SPEED_INCREASE = 1.2  # Multiplier per wave
ENEMY_COUNT_BASE = 5
ENEMY_COUNT_INCREASE = 3  # Additional enemies per wave
SPAWN_DELAY_BASE = 1.5  # seconds
SPAWN_DELAY_DECREASE = 0.2  # seconds decrease per wave

# Debug Settings
DEBUG_MODE = False
DEBUG_COLOR = (200, 200, 50)

# Paths
ASSET_DIR = "assets/"
SOUND_DIR = ASSET_DIR + "sounds/" 