DOMAIN = "victron_vebus_mk3"

KEY_CONTEXT = "context"

CONF_SERIAL_NUMBER = "serial_number"
CONF_CURRENT_LIMIT = "current_limit"
CONF_UPDATE_INTERVAL = "update_interval"

DEFAULT_UPDATE_INTERVAL = 2
MIN_UPDATE_INTERVAL = 1

# The MK3 protocol supports up to 4 phases. Additional phase entities are disabled
# by default, so polling still depends on whether the user enables those entities.
AC_PHASES_POLLED = 4
