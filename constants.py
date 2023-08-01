###############
# DISCORD BOT #
###############
DEFAULT_BOT_PREFIX = "~"
EMBED_COLOR = 0xD4E4FF


DEFAULT_COMMANDS = []
CUSTOM_COMMANDS = {}

# Command success/fail
SUCCESS = "Success"
FAILED = "Failed"

# File size restriction
BYTES_TO_MEGABYTES = 1_048_576  # 1024 squared

###########
# MODULES #
###########
MODULES_DIR = "modules"

############
# REMINDER #
############

# Used for time utils
UTC = "UTC"
DISPLAY_DATETIME_FORMAT = "%a %B %d, %H:%M %Z"
SHEET_DATETIME_FORMAT = "%m/%d/%y %H:%M %Z"

# Host Roles
HOST_ROLES: list[int | str] = [
    "Host",
    895401727954661416,
    "admin",
    1007113984077479936,
    "PermaMod",
    895401877427093514,
]
