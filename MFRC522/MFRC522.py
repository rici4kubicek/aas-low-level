# https://github.com/mxgxw/MFRC522-python
# !/usr/bin/env python
# -*- coding: utf8 -*-
#
#    Copyright 2014,2018 Mario Gomez <mario.gomez@teubi.co>
#
#    This file is part of MFRC522-Python
#    MFRC522-Python is a simple Python implementation for
#    the MFRC522 NFC Card Reader for the Raspberry Pi.
#
#    MFRC522-Python is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    MFRC522-Python is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public License
#    along with MFRC522-Python.  If not, see <http://www.gnu.org/licenses/>.
#

import spidev
from nightWiring import io
import signal
import time
import binascii

from array import array

# A demo GPIO map for Raspberry Pi with ICA HAT, 'i' means integer.
ledMap = array('i', [7])


class MFRC522:
    NRSTPD = 7

    MAX_LEN = 16

    PCD_IDLE = 0x00
    PCD_AUTHENT = 0x0E
    PCD_RECEIVE = 0x08
    PCD_TRANSMIT = 0x04
    PCD_TRANSCEIVE = 0x0C
    PCD_RESETPHASE = 0x0F
    PCD_CALCCRC = 0x03

    PICC_REQIDL = 0x26
    PICC_REQALL = 0x52
    PICC_ANTICOLL = 0x93
    PICC_ANTICOLL2 = 0x95
    PICC_SElECTTAG = 0x93
    PICC_SElECTTAG2 = 0x95
    PICC_AUTHENT1A = 0x60
    PICC_AUTHENT1B = 0x61
    PICC_READ = 0x30
    PICC_WRITE = 0xA0
    PICC_UL_WRITE = 0xA2
    PICC_DECREMENT = 0xC0
    PICC_INCREMENT = 0xC1
    PICC_RESTORE = 0xC2
    PICC_TRANSFER = 0xB0
    PICC_HALT = 0x50

    MI_OK = 0
    MI_NOTAGERR = 1
    MI_ERR = 2

    Reserved00 = 0x00
    CommandReg = 0x01
    CommIEnReg = 0x02
    DivlEnReg = 0x03
    CommIrqReg = 0x04
    DivIrqReg = 0x05
    ErrorReg = 0x06
    Status1Reg = 0x07
    Status2Reg = 0x08
    FIFODataReg = 0x09
    FIFOLevelReg = 0x0A
    WaterLevelReg = 0x0B
    ControlReg = 0x0C
    BitFramingReg = 0x0D
    CollReg = 0x0E
    Reserved01 = 0x0F

    Reserved10 = 0x10
    ModeReg = 0x11
    TxModeReg = 0x12
    RxModeReg = 0x13
    TxControlReg = 0x14
    TxAutoReg = 0x15
    TxSelReg = 0x16
    RxSelReg = 0x17
    RxThresholdReg = 0x18
    DemodReg = 0x19
    Reserved11 = 0x1A
    Reserved12 = 0x1B
    MifareReg = 0x1C
    Reserved13 = 0x1D
    Reserved14 = 0x1E
    SerialSpeedReg = 0x1F

    Reserved20 = 0x20
    CRCResultRegM = 0x21
    CRCResultRegL = 0x22
    Reserved21 = 0x23
    ModWidthReg = 0x24
    Reserved22 = 0x25
    RFCfgReg = 0x26
    GsNReg = 0x27
    CWGsPReg = 0x28
    ModGsPReg = 0x29
    TModeReg = 0x2A
    TPrescalerReg = 0x2B
    TReloadRegH = 0x2C
    TReloadRegL = 0x2D
    TCounterValueRegH = 0x2E
    TCounterValueRegL = 0x2F

    Reserved30 = 0x30
    TestSel1Reg = 0x31
    TestSel2Reg = 0x32
    TestPinEnReg = 0x33
    TestPinValueReg = 0x34
    TestBusReg = 0x35
    AutoTestReg = 0x36
    VersionReg = 0x37
    AnalogTestReg = 0x38
    TestDAC1Reg = 0x39
    TestDAC2Reg = 0x3A
    TestADCReg = 0x3B
    Reserved31 = 0x3C
    Reserved32 = 0x3D
    Reserved33 = 0x3E
    Reserved34 = 0x3F

    serNum = []

    def __init__(self, spi_bus, spi_device, nanopi_instance):
        # io.setup()
        # io.setupGPIO(ledMap, 1)
        # io.pinMode(0, io.OUTPUT)
        # io.digitalWrite(0, io.HIGH)
        # io.digitalWrite(0, io.LOW)
        # time.sleep(0.1)
        # io.digitalWrite(0, io.HIGH)
        # time.sleep(0.1)
        # self.spi = spidev.SpiDev()
        # self.spi.open(spi_bus, spi_device)
        # self.spi.max_speed_hz = 1000000
        self.nanopi = nanopi_instance
        self.init()

    def reset(self):
        self.write_spi(self.CommandReg, self.PCD_RESETPHASE)
        # time.sleep(0.2)

    def write_spi(self, addr, val):
        # self.spi.xfer([(addr << 1) & 0x7E, val])
        self.nanopi.write([(addr << 1) & 0x7E, val])

    def read_spi(self, addr):
        # val = self.spi.xfer([((addr << 1) & 0x7E) | 0x80, 0])
        # return val[1]
        val = self.nanopi.read_byte([((addr << 1) & 0x7E) | 0x80, 0])
        return val

    def set_bit_mask(self, reg, mask):
        tmp = self.read_spi(reg)
        self.write_spi(reg, tmp | mask)

    def clear_bit_mask(self, reg, mask):
        tmp = self.read_spi(reg);
        self.write_spi(reg, tmp & (~mask))

    def antenna_on(self):
        temp = self.read_spi(self.TxControlReg)
        if ~(temp & 0x03):
            self.set_bit_mask(self.TxControlReg, 0x03)

    def antenna_off(self):
        self.clear_bit_mask(self.TxControlReg, 0x03)

    def to_card(self, command, send_data):
        back_data = []
        back_len = 0
        status = self.MI_ERR
        irq_en = 0x00
        wait_irq = 0x00
        last_bits = None
        n = 0
        i = 0

        if command == self.PCD_AUTHENT:
            irq_en = 0x12
            wait_irq = 0x10
        if command == self.PCD_TRANSCEIVE:
            irq_en = 0x77
            wait_irq = 0x30

        self.write_spi(self.CommIEnReg, irq_en | 0x80)
        self.clear_bit_mask(self.CommIrqReg, 0x80)
        self.set_bit_mask(self.FIFOLevelReg, 0x80)

        self.write_spi(self.CommandReg, self.PCD_IDLE);

        while i < len(send_data):
            self.write_spi(self.FIFODataReg, send_data[i])
            i = i + 1

        self.write_spi(self.CommandReg, command)

        if command == self.PCD_TRANSCEIVE:
            self.set_bit_mask(self.BitFramingReg, 0x80)

        i = 2000
        while True:
            n = self.read_spi(self.CommIrqReg)
            i = i - 1
            if ~((i != 0) and ~(n & 0x01) and ~(n & wait_irq)):
                break

        self.clear_bit_mask(self.BitFramingReg, 0x80)

        if i != 0:
            if (self.read_spi(self.ErrorReg) & 0x1B) == 0x00:
                status = self.MI_OK

                if n & irq_en & 0x01:
                    status = self.MI_NOTAGERR

                if command == self.PCD_TRANSCEIVE:
                    n = self.read_spi(self.FIFOLevelReg)
                    last_bits = self.read_spi(self.ControlReg) & 0x07
                    if last_bits != 0:
                        back_len = (n - 1) * 8 + last_bits
                    else:
                        back_len = n * 8

                    if n == 0:
                        n = 1
                    if n > self.MAX_LEN:
                        n = self.MAX_LEN

                    i = 0
                    while i < n:
                        back_data.append(self.read_spi(self.FIFODataReg))
                        i = i + 1;
            else:
                status = self.MI_ERR

        return status, back_data, back_len

    def request(self, req_mode):
        tag_type = []

        self.write_spi(self.BitFramingReg, 0x07)

        tag_type.append(req_mode);
        (status, backData, backBits) = self.to_card(self.PCD_TRANSCEIVE, tag_type)
        # print("status {} backdata {} backbit {}".format(status, backData, backBits))

        if (status != self.MI_OK) | (backBits != 0x10):
            status = self.MI_ERR

        return status, backBits

    def anticoll(self, level):
        ser_num_check = 0

        ser_num = []

        self.write_spi(self.BitFramingReg, 0x00)

        if level == 1:
            ser_num.append(self.PICC_ANTICOLL)
        if level == 2:
            ser_num.append(self.PICC_ANTICOLL2)
        ser_num.append(0x20)

        (status, backData, backBits) = self.to_card(self.PCD_TRANSCEIVE, ser_num)
        # print("status {} backData {} backBits {}".format(status, backData, backBits))

        if status == self.MI_OK:
            i = 0
            if len(backData) == 5:
                while i < 4:
                    ser_num_check = ser_num_check ^ backData[i]
                    i = i + 1
                if ser_num_check != backData[i]:
                    status = self.MI_ERR
            else:
                status = self.MI_ERR

        return status, backData

    def sak(self, uid):

        ser_num = []

        self.write_spi(self.BitFramingReg, 0x00)

        ser_num.append(self.PICC_ANTICOLL)
        ser_num.append(0x70)
        ser_num.append(0x88)
        ser_num.append(uid[0])
        ser_num.append(uid[1])
        ser_num.append(uid[2])
        bcc = 0x88 ^ uid[0] ^ uid[1]^ uid[2]
        ser_num.append(bcc)

        crc = self.calculate_crc(ser_num)

        ser_num.append(crc[0])
        ser_num.append(crc[1])

        (status, backData, backBits) = self.to_card(self.PCD_TRANSCEIVE, ser_num)
        # print("SAK status {} backdata {} backBits {}".format(status, backData, backBits))

        return backData

    def calculate_crc(self, pIndata):
        self.clear_bit_mask(self.DivIrqReg, 0x04)
        self.set_bit_mask(self.FIFOLevelReg, 0x80);
        i = 0
        while i < len(pIndata):
            self.write_spi(self.FIFODataReg, pIndata[i])
            i = i + 1
        self.write_spi(self.CommandReg, self.PCD_CALCCRC)
        i = 0xFF
        while True:
            n = self.read_spi(self.DivIrqReg)
            i = i - 1
            if not ((i != 0) and not (n & 0x04)):
                break
        p_out_data = []
        p_out_data.append(self.read_spi(self.CRCResultRegL))
        p_out_data.append(self.read_spi(self.CRCResultRegM))
        return p_out_data

    def select_tag(self, ser_num):
        buf = []
        buf.append(self.PICC_SElECTTAG)
        buf.append(0x70)
        i = 0
        while i < 5:
            buf.append(ser_num[i])
            i = i + 1
        p_out = self.calculate_crc(buf)
        buf.append(p_out[0])
        buf.append(p_out[1])
        (status, backData, backLen) = self.to_card(self.PCD_TRANSCEIVE, buf)

        if (status == self.MI_OK) and (backLen == 0x18):
            print("Size: " + str(backData[0]))
            return backData[0]
        else:
            return 0

    def select_tag2(self, ser_num):
        buf = []
        buf.append(self.PICC_SElECTTAG2)
        buf.append(0x70)
        i = 3
        while i < 7:
            buf.append(ser_num[i])
            i = i + 1

        bcc = ser_num[3] ^ ser_num[4] ^ ser_num[5] ^ ser_num[6]
        buf.append(bcc)

        pOut = self.calculate_crc(buf)
        buf.append(pOut[0])
        buf.append(pOut[1])
        (status, backData, backLen) = self.to_card(self.PCD_TRANSCEIVE, buf)
        print("SelectTag2 status {} backdata {} backLen {}".format(status, backData, backLen))

        if (status == self.MI_OK) and (backLen == 0x18):
            print("Size: " + str(backData[0]))
            return backData[0]
        else:
            return 0

    def ntag216_auth(self, sectorkey):
        buff = []

        buff.append(0x1B)

        # Now we need to append the authKey which usually is 6 bytes of 0xFF
        i = 0
        while i < len(sectorkey):
            buff.append(sectorkey[i])
            i = i + 1
        i = 0

        p_out = self.calculate_crc(buff)
        buff.append(p_out[0])
        buff.append(p_out[1])

        # Now we start the authentication itself
        (status, backData, backLen) = self.to_card(self.PCD_TRANSCEIVE, buff)
        print("Auth status {} backdata {} backLen {}".format(status, backData, backLen))
        # Check if an error occurred
        if not (status == self.MI_OK):
            print("AUTH ERROR!!")
        if not (self.read_spi(self.Status2Reg) & 0x08) != 0:
            print("AUTH ERROR(status2reg & 0x08) != 0")

        # Return the status
        return status

    def auth(self, auth_mode, block_addr, sectorkey, ser_num):
        buff = []

        # First byte should be the authMode (A or B)
        buff.append(auth_mode)

        # Second byte is the trailerBlock (usually 7)
        buff.append(block_addr)

        # Now we need to append the authKey which usually is 6 bytes of 0xFF
        i = 0
        while i < len(sectorkey):
            buff.append(sectorkey[i])
            i = i + 1
        i = 0

        # Next we append the first 4 bytes of the UID
        while i < 4:
            buff.append(ser_num[i])
            i = i + 1

        # Now we start the authentication itself
        (status, backData, backLen) = self.to_card(self.PCD_AUTHENT, buff)

        # Check if an error occurred
        if not (status == self.MI_OK):
            print("AUTH ERROR!!")
        if not (self.read_spi(self.Status2Reg) & 0x08) != 0:
            print("AUTH ERROR(status2reg & 0x08) != 0")

        # Return the status
        return status

    def stop_crypto1(self):
        self.clear_bit_mask(self.Status2Reg, 0x08)

    def read_ultralight(self, block_addr):
        recv_data = []
        recv_data.append(self.PICC_READ)
        recv_data.append(block_addr)
        pOut = self.calculate_crc(recv_data)
        recv_data.append(pOut[0])
        recv_data.append(pOut[1])
        (status, backData, backLen) = self.to_card(self.PCD_TRANSCEIVE, recv_data)
        if not (status == self.MI_OK):
            print("Error while reading!")
        i = 0
        if len(backData) == 16:
            b = []
            for item in backData:
                b.append(hex(item))
            print("Sector " + str(block_addr) + " " + str(b))

    def read(self, block_addr):
        recv_data = []
        recv_data.append(self.PICC_READ)
        recv_data.append(block_addr)
        pOut = self.calculate_crc(recv_data)
        recv_data.append(pOut[0])
        recv_data.append(pOut[1])
        (status, backData, backLen) = self.to_card(self.PCD_TRANSCEIVE, recv_data)

        if not (status == self.MI_OK):
            print("Error while reading!")
        i = 0
        if len(backData) == 16:
            b = []
            for item in backData:
                b.append(hex(item))
            print("Sector " + str(block_addr) + " " + str(b))

    def write(self, block_addr, write_data):
        buff = []
        buff.append(self.PICC_UL_WRITE)
        buff.append(block_addr)
        buff.append(write_data[0])
        buff.append(write_data[1])
        buff.append(write_data[2])
        buff.append(write_data[3])
        crc = self.calculate_crc(buff)
        buff.append(crc[0])
        buff.append(crc[1])

        (status, backData, backLen) = self.to_card(self.PCD_TRANSCEIVE, buff)

        return status

    def dump_classic_1k(self, key, uid):
        i = 0
        while i < 64:
            status = self.auth(self.PICC_AUTHENT1A, i, key, uid)
            # Check if authenticated
            if status == self.MI_OK:
                self.read(i)
            else:
                print("Authentication error")
            i = i + 1

    def dump_ultralight(self, uid):
        i = 0
        while i < 16:
            self.read(i)
            i = i + 1

    def init(self):

        io.digitalWrite(0, io.HIGH)
        self.reset();

        # data = ''.join([chr(0x82), chr(0)])
        self.write_spi(self.TxModeReg, 0x0)
        self.write_spi(self.RxModeReg, 0x0)
        self.write_spi(self.ModWidthReg, 0x26)

        self.write_spi(self.TModeReg, 0x80)
        self.write_spi(self.TPrescalerReg, 0xA9)

        self.write_spi(self.TReloadRegH, 0x03)
        self.write_spi(self.TReloadRegL, 0xe8)

        self.write_spi(self.TxAutoReg, 0x40)
        self.write_spi(self.ModeReg, 0x3D)
        self.antenna_on()

        # self.Write_MFRC522(self.TModeReg, 0x8D)
        # self.Write_MFRC522(self.TPrescalerReg, 0x3E)
        # self.Write_MFRC522(self.TReloadRegL, 30)
        # self.Write_MFRC522(self.TReloadRegH, 0)
        #
        # self.Write_MFRC522(self.TxAutoReg, 0x40)
        # self.Write_MFRC522(self.ModeReg, 0x3D)
        # self.AntennaOn()

        # self.Write_MFRC522(self.TModeReg, 0x8D)
        # self.Write_MFRC522(self.TPrescalerReg, 0x3E)
        # self.Write_MFRC522(self.TReloadRegL, 0x1E)
        # self.Write_MFRC522(self.TReloadRegH, 0x00)
        # self.Write_MFRC522(self.TxAutoReg, 0x40)
        # self.Write_MFRC522(self.ModeReg, 0x3D)
        #
        # # Set antenna gain to 48dB
        # self.Write_MFRC522(self.RFCfgReg, 0x70)
        #
        # self.AntennaOn()
#
# spi.open("/dev/spidev0.0")
# print("open")
# spi.write([0x24, 0])
# print("1st write")
# spi.write([0x26, 0])
# spi.write([0x48, 0x26])
# spi.write([0x54, 0x80])
# spi.write([0x56, 0xa9])
# spi.write([0x58, 0x03])
# spi.write([0x5a, 0xe8])
# spi.write([0x2a, 0x40])
# spi.write([0x22, 0x3d])
# print("allwrite")
#
# spi.write([0x80])
# data = spi.read(1)
# print("xfer")
# spi.close()
# print(data)