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

import time
import serial
import sys
import platform

from .port_handler import PortHandler

LATENCY_TIMER = 16
DEFAULT_BAUDRATE = 1000000
DEFAULT_CAN_ID = 0x60  # Default CAN ID (standard frame, ID 0x60)
CAN_MAX_DATA_SIZE = 8  # Maximum data size for a CAN frame
CAN_EXTENDED_ID = 0x80000000  # Bit to set for extended frame format

class PortHandlerCAN(PortHandler):
    """
    PortHandler implementation for Waveshare WS-TTL-CAN converter in transparency mode.
    
    This class extends the standard PortHandler to work with a Waveshare WS-TTL-CAN converter,
    which allows communication with Dynamixel servos over a CAN bus.
    
    Configuration requirements for the WS-TTL-CAN converter:
    1. Set to "Transparent Conversion" mode
    2. Configure the CAN ID as needed (default is 0x60)
    3. Set the baudrate appropriately (default 1000000 for Dynamixels)
    4. Make sure the serial settings match (8-N-1)
    
    Note: Before using this port handler, you must configure the 
    WS-TTL-CAN converter using the WS-CAN-TOOL software.
    """
    def __init__(self, port_name, can_id=DEFAULT_CAN_ID, extended_id=False, can_baudrate=1000000):
        """
        Initialize the PortHandlerCAN.
        
        Args:
            port_name (str): Name of the serial port
            can_id (int): CAN ID to use for communication (defaults to 0x60)
            extended_id (bool): Use extended frame format if True
            can_baudrate (int): CAN bus baudrate (must match converter setting)
        """
        super(PortHandlerCAN, self).__init__(port_name)
        self.can_id = can_id
        self.extended_id = extended_id
        self.can_baudrate = can_baudrate
        # Buffer for storing partially received packets
        self._recv_buffer = bytearray()
        # Debug mode flag
        self.debug = False
        
    def writePort(self, packet):
        """
        Write data to the port, wrapping it in a CAN frame if needed.
        
        In transparency mode, the WS-TTL-CAN converter will take this data
        and send it as the payload of a CAN frame with the configured ID.
        
        For packets larger than CAN_MAX_DATA_SIZE bytes, the data is sent
        in multiple CAN frames as required by the transparency mode.
        
        Args:
            packet (bytes or list): Data packet to write
            
        Returns:
            int: Number of bytes written
        """
        # Convert to bytearray if it's a list
        if isinstance(packet, list):
            packet = bytearray(packet)
        
        # In transparency mode, the WS-TTL-CAN converter should handle the 
        # packing of data into CAN frames automatically
        if self.debug:
            print(f"[DEBUG] Writing packet: {' '.join([f'{b:02X}' for b in packet])}")
        
        # Send the packet directly - in transparency mode the converter handles the rest
        return super(PortHandlerCAN, self).writePort(packet)

    def readPort(self, length):
        """
        Read data from the port, handling CAN frame unwrapping if needed.
        
        In transparency mode, the WS-TTL-CAN converter receives CAN frames
        and extracts the payload data, which is then read as regular serial data.
        
        Args:
            length (int): Number of bytes to read
            
        Returns:
            bytes or list: Data read from the port
        """
        data = super(PortHandlerCAN, self).readPort(length)
        
        if self.debug and data:
            if sys.version_info[0] >= 3:
                print(f"[DEBUG] Read data: {' '.join([f'{b:02X}' for b in data])}")
            else:
                print(f"[DEBUG] Read data: {' '.join([f'{b:02X}' for b in data])}")
                
        return data

    def setupPort(self, cflag_baud):
        """
        Set up the port for communication.
        
        This configures the serial port with the appropriate settings for
        the WS-TTL-CAN converter in transparency mode.
        
        Args:
            cflag_baud (int): Baudrate flag
            
        Returns:
            bool: True if successful, False otherwise
        """
        if self.is_open:
            self.closePort()

        try:
            self.ser = serial.Serial(
                port=self.port_name,
                baudrate=self.baudrate,
                # Default settings for WS-TTL-CAN converter
                bytesize=serial.EIGHTBITS,
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                timeout=0
            )

            self.is_open = True
            self.ser.reset_input_buffer()
            self.tx_time_per_byte = (1000.0 / self.baudrate) * 10.0
            
            # Display configuration information in debug mode
            if self.debug:
                print("[DEBUG] Port Configuration:")
                print(f"  - Serial Port: {self.port_name}")
                print(f"  - Serial Baudrate: {self.baudrate}")
                print(f"  - CAN ID: 0x{self.can_id:X}{' (Extended)' if self.extended_id else ' (Standard)'}")
                print(f"  - CAN Baudrate: {self.can_baudrate}")
                print("Note: Make sure the WS-TTL-CAN converter is configured with these settings")
                
            return True
            
        except serial.SerialException as e:
            print(f"Error opening port: {e}")
            return False

    def setDebug(self, enable):
        """
        Enable or disable debug mode.
        
        Args:
            enable (bool): True to enable debug output, False to disable
        """
        self.debug = enable
    
    def printCANConfInstructions(self):
        """
        Print instructions for configuring the WS-TTL-CAN converter.
        """
        print("=== WS-TTL-CAN Configuration Instructions ===")
        print("1. Download and open WS-CAN-TOOL software from Waveshare's website")
        print("2. Connect the WS-TTL-CAN converter to your computer via USB-to-TTL converter")
        print("3. Configure the following settings:")
        print("   - Set 'Working Mode' to 'Transparent Conversion'")
        print(f"   - Set 'CAN Baudrate' to {self.can_baudrate} bps")
        print(f"   - Set 'Serial Baudrate' to {self.baudrate} bps")
        print("   - Set 'Serial Data Bit' to 8")
        print("   - Set 'Serial Stop Bit' to 1")
        print("   - Set 'Serial Parity Bit' to None")
        print(f"   - Set 'CAN ID' to 0x{self.can_id:X}")
        print(f"   - Set 'Frame Type' to {'Extended Frame' if self.extended_id else 'Standard Frame'}")
        print("4. Click 'Save Device Parameters'")
        print("5. Click 'Restart Device'")
        print("===========================================")

def PortHandlerForWaveshareCAN(port_name, can_id=DEFAULT_CAN_ID, extended_id=False, can_baudrate=1000000, debug=False):
    """
    Factory function to create a PortHandlerCAN instance.
    
    Args:
        port_name (str): Name of the serial port
        can_id (int): CAN ID to use for communication
        extended_id (bool): Use extended frame format if True
        can_baudrate (int): CAN bus baudrate (must match converter setting)
        debug (bool): Enable debug output if True
        
    Returns:
        PortHandlerCAN: A port handler for CAN communication
    """
    port_handler = PortHandlerCAN(port_name, can_id, extended_id, can_baudrate)
    port_handler.setDebug(debug)
    return port_handler 