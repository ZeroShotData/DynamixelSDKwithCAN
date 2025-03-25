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

# *********     Sync Write Example with Waveshare WS-TTL-CAN     *********
#
# This example shows how to control multiple Dynamixel servos synchronously
# using the Waveshare WS-TTL-CAN converter in transparency mode.
#
# Requirements:
# - Same as can_ping_example.py
# - Multiple Dynamixel servos connected to the bus
#
# Operation:
# - The example syncs the goal position of multiple Dynamixels to make them move simultaneously

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
BAUDRATE                = 57600  # Dynamixel default baudrate: 57600
DEVICENAME              = '/dev/ttyUSB0' # Check which port is being used on your controller

# CAN settings
CAN_ID                  = 0x60  # Default CAN ID for WS-TTL-CAN
CAN_BAUDRATE            = 1000000  # CAN bus baudrate
USE_EXTENDED_ID         = False  # Use standard CAN frame (false) or extended CAN frame (true)
DEBUG_MODE              = True   # Enable debug output

# Define the IDs of the Dynamixels to control (modify as needed)
DXL_ID_LIST             = [1, 2, 3]  # IDs for each Dynamixel

# Dynamixel addresses (may vary depending on your model)
ADDR_MX_TORQUE_ENABLE       = 24
ADDR_MX_GOAL_POSITION       = 30
ADDR_MX_PRESENT_POSITION    = 36
ADDR_MX_MOVING              = 46

# Data value
TORQUE_ENABLE               = 1     # Value for enabling the torque
TORQUE_DISABLE              = 0     # Value for disabling the torque
DXL_MINIMUM_POSITION_VALUE  = 100   # Dynamixel will rotate between this value
DXL_MAXIMUM_POSITION_VALUE  = 900   # and this value

def print_error(packet_handler, dxl_comm_result, dxl_error=0):
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
    
    # Initialize GroupSyncWrite instance
    groupSyncWrite = GroupSyncWrite(portHandler, packetHandler, ADDR_MX_GOAL_POSITION, 2)
    
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
    
    # Enable torque for all Dynamixels
    print_section("Torque Control")
    for dxl_id in DXL_ID_LIST:
        dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(
            portHandler, dxl_id, ADDR_MX_TORQUE_ENABLE, TORQUE_ENABLE)
        if dxl_comm_result != COMM_SUCCESS or dxl_error != 0:
            print(f"Failed to enable torque on Dynamixel ID {dxl_id}:")
            print_error(packetHandler, dxl_comm_result, dxl_error)
        else:
            print(f"Dynamixel ID {dxl_id}: Torque enabled")
    
    # Check if all Dynamixels can be pinged
    print_section("Checking Connections")
    all_connected = True
    for dxl_id in DXL_ID_LIST:
        dxl_model_number, dxl_comm_result, dxl_error = packetHandler.ping(portHandler, dxl_id)
        if dxl_comm_result != COMM_SUCCESS or dxl_error != 0:
            print(f"Failed to ping Dynamixel ID {dxl_id}:")
            print_error(packetHandler, dxl_comm_result, dxl_error)
            all_connected = False
        else:
            print(f"Dynamixel ID {dxl_id}: Connected (Model: {dxl_model_number})")
    
    if not all_connected:
        print("Not all Dynamixels could be found. Check connections and IDs.")
        print("Press any key to terminate...")
        getch()
        # Disable torque on all servos before exiting
        for dxl_id in DXL_ID_LIST:
            packetHandler.write1ByteTxRx(portHandler, dxl_id, ADDR_MX_TORQUE_ENABLE, TORQUE_DISABLE)
        portHandler.closePort()
        return
    
    print("All Dynamixels connected successfully!")
    print("Press any key to continue with synchronized position control...")
    getch()
    
    # Start position control loop
    print_section("Sync Position Control")
    print("Moving all Dynamixels synchronously between positions...")
    print("Press any key to stop...")
    
    toggle_position = True
    
    while True:
        # Check if key was pressed
        if msvcrt.kbhit() if os.name == 'nt' else sys.stdin.isatty():
            getch()
            break
            
        # Clear previous parameters
        groupSyncWrite.clearParam()
        
        # Set goal position for all servos
        target_position = DXL_MAXIMUM_POSITION_VALUE if toggle_position else DXL_MINIMUM_POSITION_VALUE
        print(f"Moving all servos to position: {target_position}")
        
        # Add parameters for all Dynamixels
        for dxl_id in DXL_ID_LIST:
            # Allocate goal position value to send
            param_goal_position = [DXL_LOBYTE(target_position), DXL_HIBYTE(target_position)]
            
            # Add Dynamixel goal position value to the Syncwrite parameter storage
            dxl_addparam_result = groupSyncWrite.addParam(dxl_id, param_goal_position)
            if not dxl_addparam_result:
                print(f"Failed to add parameters for Dynamixel ID {dxl_id}")
                break
        
        # Syncwrite goal position
        dxl_comm_result = groupSyncWrite.txPacket()
        if dxl_comm_result != COMM_SUCCESS:
            print("Failed to send sync write packet:")
            print_error(packetHandler, dxl_comm_result)
        
        # Toggle position for next iteration
        toggle_position = not toggle_position
        
        # Wait for all Dynamixels to complete their motion
        time.sleep(2)
    
    # Disable torque on all servos
    print_section("Cleanup")
    print("Disabling torque on all Dynamixels...")
    for dxl_id in DXL_ID_LIST:
        dxl_comm_result, dxl_error = packetHandler.write1ByteTxRx(
            portHandler, dxl_id, ADDR_MX_TORQUE_ENABLE, TORQUE_DISABLE)
        if dxl_comm_result != COMM_SUCCESS or dxl_error != 0:
            print(f"Failed to disable torque on Dynamixel ID {dxl_id}:")
            print_error(packetHandler, dxl_comm_result, dxl_error)
        else:
            print(f"Dynamixel ID {dxl_id}: Torque disabled")
    
    # Close port
    portHandler.closePort()
    print("Port closed")
    print("Program completed")

if __name__ == "__main__":
    main() 