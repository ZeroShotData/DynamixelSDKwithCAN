# Dynamixel SDK with Waveshare WS-TTL-CAN Converter

This extension to the Dynamixel SDK enables communication with Dynamixel servos through a CAN bus using the Waveshare WS-TTL-CAN converter in transparency mode.

## Overview

The standard Dynamixel SDK communicates with servos using a direct TTL or RS485 connection. This extension allows you to use a CAN bus as an intermediate communication layer by utilizing the Waveshare WS-TTL-CAN converter, which handles the protocol conversion between TTL and CAN.

![Connection Diagram](https://i.imgur.com/placeholder.png)

## Requirements

- Standard Dynamixel SDK
- Waveshare WS-TTL-CAN converter (x2)
- USB-to-TTL converter (or equivalent to connect to your computer)
- Dynamixel servo(s)
- CAN bus cabling

## Hardware Setup

1. **Computer Side:**
   - Connect your computer to one WS-TTL-CAN converter using a USB-to-TTL converter
   - Connect the WS-TTL-CAN converter to the CAN bus

2. **Servo Side:**
   - Connect the second WS-TTL-CAN converter to the CAN bus
   - Connect the TTL side of the converter to your Dynamixel servo(s)

3. **Power:**
   - Ensure all devices are properly powered according to their specifications

## Waveshare WS-TTL-CAN Configuration

Before using the SDK, you must configure both WS-TTL-CAN converters using the WS-CAN-TOOL software:

1. Download WS-CAN-TOOL from the [Waveshare Wiki](https://www.waveshare.com/)
2. Configure each converter with these settings:
   - **Working Mode:** Transparent Conversion
   - **CAN Baudrate:** 1000000 bps (or match your CAN network speed)
   - **Serial Baudrate:** Must match your Dynamixel baudrate (typically 57600 or 1000000 bps)
   - **Serial Data Bit:** 8
   - **Serial Stop Bit:** 1
   - **Serial Parity Bit:** None
   - **CAN ID:** 0x60 (default, can be changed)
   - **Frame Type:** Standard Frame (or Extended Frame if needed)

3. Click "Save Device Parameters" and "Restart Device" to apply the settings

## Software Usage

The modified SDK adds a new port handler class specifically for CAN communication:

```python
from dynamixel_sdk import *

# Create a special port handler for the Waveshare WS-TTL-CAN converter
portHandler = PortHandlerForWaveshareCAN(
    port_name="/dev/ttyUSB0",  # Modify to match your system
    can_id=0x60,               # Default CAN ID
    extended_id=False,         # Use standard frame format
    can_baudrate=1000000,      # CAN bus baudrate
    debug=True                 # Enable debug output
)

# Initialize PacketHandler as normal
packetHandler = PacketHandler(PROTOCOL_VERSION)

# Use the SDK as you normally would
portHandler.openPort()
portHandler.setBaudRate(57600)  # Must match the serial baudrate setting in WS-TTL-CAN
```

## Example Scripts

Three example scripts are provided to demonstrate the usage:

1. **can_ping_example.py** - Basic ping example to test connectivity
2. **can_read_write_example.py** - Read and write operations on a single servo
3. **can_sync_write_example.py** - Synchronized control of multiple servos

## Troubleshooting

### Common Issues

1. **No Communication:**
   - Verify both WS-TTL-CAN converters are properly configured
   - Check physical connections and power supply
   - Ensure CAN IDs and baudrates match between converters

2. **Unreliable Communication:**
   - Check that the CAN bus has proper termination resistors (120 ohms)
   - Try reducing the baudrate
   - Enable debug mode to see what's being sent/received

3. **CAN Frame Errors:**
   - Ensure the CAN ID is within valid range for standard frames (0x000-0x7FF)
   - Check that data packets don't exceed the 8-byte limit for a single CAN frame

### Debug Mode

Enable debug mode when initializing the port handler to see detailed communication logs:

```python
portHandler = PortHandlerForWaveshareCAN(port_name, can_id=0x60, debug=True)
```

## Advanced Configuration

### Extended CAN IDs

To use extended CAN IDs (29-bit identifiers):

```python
portHandler = PortHandlerForWaveshareCAN(port_name, can_id=0x12345678, extended_id=True)
```

### Configuration Instructions

The port handler includes a helper method to print configuration instructions:

```python
portHandler.printCANConfInstructions()
```

## Performance Considerations

- CAN bus has a maximum data payload of 8 bytes per frame
- In transparency mode, the WS-TTL-CAN automatically segments larger packets
- Increased latency compared to direct TTL connection
- Limited bandwidth compared to direct TTL connection

## References

- [Dynamixel SDK Documentation](http://emanual.robotis.com/docs/en/software/dynamixel/dynamixel_sdk/overview/)
- [Waveshare WS-TTL-CAN Wiki](https://www.waveshare.com/wiki/WS-TTL-CAN) 