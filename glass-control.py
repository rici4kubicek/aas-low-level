# !/usr/bin/python
import sys
from MFRC522 import MFRC522
import signal
from NANOPISPI import NANOPISPI
from array import array

nanopi = NANOPISPI.NANOPISPI(1)
nanopi.cs_init([6])
nanopi.cs_set(0, 0)
nanopi.open(0,0,1000000)

continue_reading = True


# Capture SIGINT for cleanup when the script is aborted
def end_read(signal, frame):
    global continue_reading
    print("Ctrl+C captured, ending read.")
    continue_reading = False


# Hook the SIGINT
signal.signal(signal.SIGINT, end_read)

# Create an object of the class MFRC522
MIFAREReader = MFRC522.MFRC522(0,0, nanopi)

# Welcome message
print("Welcome to the MFRC522 data read example")
print("Press Ctrl-C to stop.")

# continue_reading = False
# This loop keeps checking for chips. If one is near it will get the UID and authenticate
while continue_reading:

    # Scan for cards
    (status, TagType) = MIFAREReader.request(MIFAREReader.PICC_REQIDL)

    # If a card is found
    if status == MIFAREReader.MI_OK:
        print("Card detected")

    # Get the UID of the card
    (status, uid) = MIFAREReader.anticoll(1)

    # If we have the UID, continue
    if status == MIFAREReader.MI_OK:

        # Print UID
        print("Card read UID: {}, {}, {}, {}".format(hex(uid[0]), hex(uid[1]), hex(uid[2]), hex(uid[3])))

        # This is the default key for authentication
        key = [0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF]

        # Select the scanned tag
        MIFAREReader.select_tag(uid)
        # MIFAREReader.MFRC522_SAK(uid)

        # Authenticate
        # status = MIFAREReader.MFRC522_Auth(MIFAREReader.PICC_AUTHENT1A, 7, key, uid)

        # Check if authenticated
        # if status == MIFAREReader.MI_OK:

        MIFAREReader.dump_ultralight(uid)
        MIFAREReader.stop_crypto1()
        # else:
        #     print("Authentication error")
