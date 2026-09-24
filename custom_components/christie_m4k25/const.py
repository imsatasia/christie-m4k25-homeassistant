"""Constants for the Christie M 4K25 integration."""

DOMAIN = "christie_m4k25"
MANUFACTURER = "Christie"
MODEL = "M 4K25 RGB"
NAME = f"{MANUFACTURER} {MODEL}"

DEFAULT_PORT = 3002
DEFAULT_SCAN_INTERVAL = 30

CONF_PORT = "port"

# Lens axes, matching the Control4 driver's naming so the two integrations
# read the same to an installer.
LENS_AXES = ("focus", "zoom", "horizontal", "vertical")
LENS_PRESET_SLOTS = ("1", "2", "3", "4")

ATTR_ENTRY_ID = "entry_id"
ATTR_PRESET = "preset"
ATTR_COMMAND = "command"

SERVICE_SAVE_LENS_PRESET = "save_lens_preset"
SERVICE_RECALL_LENS_PRESET = "recall_lens_preset"
SERVICE_SEND_RAW = "send_raw"
