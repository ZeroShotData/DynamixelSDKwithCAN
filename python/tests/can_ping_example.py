#!/usr/bin/env python
# -*- coding: utf-8 -*-

################################################################################
# Copyright 2024
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
################################################################################

# *********     Ping Example with Waveshare WS-TTL-CAN     *********
#
# This example shows how to ping a Dynamixel servo using the Waveshare WS-TTL-CAN converter
# in transparency mode. It's based on the standard ping.py example from the Dynamixel SDK.
#
# Requirements:
# 1. Dynamixel servo configured with ID and baudrate
# 2. Waveshare WS-TTL-CAN converter properly configured as described below
# 3. Physical connection between the computer, WS-TTL-CAN, and Dynamixel servo
#
# WS-TTL-CAN Configuration (using WS-CAN-TOOL):
# - Working Mode: Transparent Conversion
# - CAN ID: 0x60 (standard frame)
# - CAN baudrate: 1000000 bps
# - Serial baudrate: must match BAUDRATE below (e.g., 57600, 1000000)
# - Serial data bit: 8
# - Serial stop bit: 1
# - Serial parity bit: None
#
# Connections:
# - Computer <USB> WS-TTL-CAN <CAN> WS-TTL-CAN <TTL> Dynamixel

import os

if os.name == 'nt':
    import msvcrt
    def getch():
        return msvcrt.getch().decode()
else:
    import sys, tty, termios
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    def getch():
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

from dynamixel_sdk import *  # Uses Dynamixel SDK library

# Protocol version
PROTOCOL_VERSION        = 1.0  # See which protocol version is used in the Dynamixel

# Default setting
DXL_ID                  = 1    # Dynamixel ID: 1
BAUDRATE                = 57600  # Dynamixel default baudrate: 57600
DEVICENAME              = '/dev/ttyUSB0' # Check which port is being used on your controller
                                         # ex) Windows: "COM1"   Linux: "/dev/ttyUSB0" Mac: "/dev/tty.usbserial-*"

# CAN settings
CAN_ID                  = 0x60  # Default CAN ID for WS-TTL-CAN
CAN_BAUDRATE            = 1000000  # CAN bus baudrate
USE_EXTENDED_ID         = False  # Use standard CAN frame (false) or extended CAN frame (true)
DEBUG_MODE              = True   # Enable debug output

def print_section(title):
    print("\n" + "="*5 + f" {title} " + "="*5)

def main():
    # Initialize PortHandler instance
    print_section("Initializing")
    print("Using custom PortHandlerForWaveshareCAN for the Waveshare WS-TTL-CAN converter")
    
    # Create a special port handler for the Waveshare WS-TTL-CAN converter
    portHandler = PortHandlerForWaveshareCAN(
        DEVICENAME, 
        can_id=CAN_ID,
        extended_id=USE_EXTENDED_ID,
        can_baudrate=CAN_BAUDRATE,
        debug=DEBUG_MODE
    )
    
    # Show configuration instructions
    print_section("Configuration")
    portHandler.printCANConfInstructions()
    
    # Initialize PacketHandler instance
    # Set the protocol version
    # Get methods and members of Protocol1PacketHandler or Protocol2PacketHandler
    packetHandler = PacketHandler(PROTOCOL_VERSION)
    
    print_section("Port Setup")
    # Open port
    if portHandler.openPort():
        print("Succeeded to open the port")
    else:
        print("Failed to open the port")
        print("Press any key to terminate...")
        getch()
        return
    
    # Set port baudrate
    if portHandler.setBaudRate(BAUDRATE):
        print("Succeeded to change the baudrate")
    else:
        print("Failed to change the baudrate")
        print("Press any key to terminate...")
        getch()
        return
    
    print_section("Pinging Dynamixel")
    print(f"Pinging Dynamixel with ID: {DXL_ID}")
    print("Press any key to continue...")
    getch()
    
    # Try to ping the Dynamixel
    # Get Dynamixel model number
    dxl_model_number, dxl_comm_result, dxl_error = packetHandler.ping(portHandler, DXL_ID)
    
    # Check for errors
    if dxl_comm_result != COMM_SUCCESS:
        print("Communication error:")
        print("%s" % packetHandler.getTxRxResult(dxl_comm_result))
    elif dxl_error != 0:
        print("Dynamixel error:")
        print("%s" % packetHandler.getRxPacketError(dxl_error))
    else:
        print("Success! Dynamixel is responding.")
        print("[ID:%03d] Dynamixel model number: %d" % (DXL_ID, dxl_model_number))
    
    print_section("Cleanup")
    # Close port
    portHandler.closePort()
    print("Port closed")
    print("Press any key to terminate...")
    getch()

if __name__ == "__main__":
    main() 