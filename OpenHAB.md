



# Channel Type "rollershutter"
on: An optional string (like "Open") that is recognized as UP state.
off: An optional string (like "Close") that is recognized as DOWN state.
stop: An optional string (like "Stop") that is recognized as STOP state.
Internally UP is converted to 0%, DOWN to 100%. If strings are defined for these values, they are used for sending commands to the broker, too.

You can connect this channel to a Rollershutter or Dimmer item.

# Channel Type "dimmer"
on: An optional string (like "ON"/"Open") that is recognized as minimum.
off: An optional string (like "OFF"/"Close") that is recognized as maximum.
min: A required minimum value.
max: A required maximum value.
step: For decrease, increase commands the step needs to be known
The value is internally stored as a percentage for a value between min and max.

The channel will publish a value between min and max.

You can connect this channel to a Rollershutter or Dimmer item.




