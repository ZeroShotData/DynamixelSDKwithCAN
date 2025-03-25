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

# *********     Read/Write Example with Waveshare WS-TTL-CAN     *********
#
# This example shows how to read and write Dynamixel registers using the Waveshare 
# WS-TTL-CAN converter in transparency mode.
#
# Requirements:
# - Same as can_ping_example.py
#
# Operation:
# - The example reads the present position and writes a goal position to make the
#   Dynamixel move between two positions.

import os
import time

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

# CAN settings
CAN_ID                  = 0x60  # Default CAN ID for WS-TTL-CAN
CAN_BAUDRATE            = 1000000  # CAN bus baudrate
USE_EXTENDED_ID         = False  # Use standard CAN frame (false) or extended CAN frame (true)
DEBUG_MODE              = True   # Enable debug output

# Dynamixel addresses (may vary depending on your model)
ADDR_MX_TORQUE_ENABLE       = 24
ADDR_MX_GOAL_POSITION       = 30
ADDR_MX_PRESENT_POSITION    = 36
ADDR_MX_MOVING              = 46

# Data value
TORQUE_ENABLE               = 1     # Value for enabling the torque
TORQUE_DISABLE              = 0     # Value for disabling the torque
DXL_MINIMUM_POSITION_VALUE  = 100   # Dynamixel will rotate between this value
DXL_MAXIMUM_POSITION_VALUE  = 900   # and this value (note that the Dynamixel would not move when the position value is out of movable range)
DXL_MOVING_STATUS_THRESHOLD = 20    # Dynamixel moving status threshold

def print_error(packet_handler, dxl_comm_result, dxl_error):
    if dxl_comm_result != COMM_SUCCESS:
        print("%s" % packet_handler.getTxRxResult(dxl_comm_result))
    elif dxl_error != 0:
        print("%s" % packet_handler.getRxPacketError(dxl_error))

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
    
    # Enable Dynamixel Torque
    print_section("Torque Control")
    dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_MX_TORQUE_ENABLE, TORQUE_ENABLE)
    if dxl_comm_result != COMM_SUCCESS or dxl_error != 0:
        print("Failed to enable torque:")
        print_error(packetHandler, dxl_comm_result, dxl_error)
        portHandler.closePort()
        return
    else:
        print("Dynamixel has been successfully connected and torque is enabled")
    
    print("Press any key to continue with position control...")
    getch()
    
    # Start position control loop
    print_section("Position Control")
    print("Moving the Dynamixel between positions...")
    print("Press any key to stop...")
    
    while True:
        # Check if a key was pressed
        if msvcrt.kbhit() if os.name == 'nt' else sys.stdin.isatty():
            getch()
            break
            
        # Write goal position (alternate between minimum and maximum)
        # Read current position first to determine which way to move
        dxl_present_position, dxl_comm_result, dxl_error = packetHandler.read2ByteTxRx(
            portHandler, DXL_ID, ADDR_MX_PRESENT_POSITION
        )
        
        if dxl_comm_result != COMM_SUCCESS or dxl_error != 0:
            print("Failed to read present position:")
            print_error(packetHandler, dxl_comm_result, dxl_error)
            continue
        
        # Determine target position based on current position
        if dxl_present_position < (DXL_MINIMUM_POSITION_VALUE + DXL_MAXIMUM_POSITION_VALUE) / 2:
            dxl_goal_position = DXL_MAXIMUM_POSITION_VALUE
        else:
            dxl_goal_position = DXL_MINIMUM_POSITION_VALUE
            
        # Write the goal position
        dxl_comm_result, dxl_error = packetHandler.write2ByteTxRx(
            portHandler, DXL_ID, ADDR_MX_GOAL_POSITION, dxl_goal_position
        )
        
        if dxl_comm_result != COMM_SUCCESS or dxl_error != 0:
            print("Failed to write goal position:")
            print_error(packetHandler, dxl_comm_result, dxl_error)
            continue
            
        print(f"Current Position: {dxl_present_position}  ->  Goal Position: {dxl_goal_position}")
        
        # Wait for the Dynamixel to reach the position
        while True:
            # Read moving status
            dxl_moving, dxl_comm_result, dxl_error = packetHandler.read1ByteTxRx(
                portHandler, DXL_ID, ADDR_MX_MOVING
            )
            
            if dxl_comm_result != COMM_SUCCESS or dxl_error != 0:
                print_error(packetHandler, dxl_comm_result, dxl_error)
                break
                
            # Exit loop if Dynamixel is not moving
            if dxl_moving == 0:
                break
                
            time.sleep(0.1)
            
        # Sleep before attempting next move
        time.sleep(1)
    
    # Disable Dynamixel Torque
    print_section("Cleanup")
    print("Disabling torque...")
    dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(portHandler, DXL_ID, ADDR_MX_TORQUE_ENABLE, TORQUE_DISABLE)
    if dxl_comm_result != COMM_SUCCESS or dxl_error != 0:
        print("Failed to disable torque:")
        print_error(packetHandler, dxl_comm_result, dxl_error)
    else:
        print("Dynamixel torque disabled")
    
    # Close port
    portHandler.closePort()
    print("Port closed")
    print("Program completed")

if __name__ == "__main__":
    main() 