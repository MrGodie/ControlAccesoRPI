# RPiAccessControl

Access control system based on a sequence of presses on physical buttons connected to the GPIO inputs of a Raspberry Pi. The system captures a sequence of button presses, compares it against a configured valid key, and displays in the terminal whether access was granted or denied.

## Features

Capture of button presses from physical buttons connected to GPIO.

Temporary storage of the sequence until it reaches the defined length (between 4 and 6 presses).

Automatic comparison of the captured sequence against the configured valid key.

Terminal messages: Access granted or Access denied.

Automatic reset of the capture state after each attempt, with no need to restart the program.

Debounce logic to prevent duplicate registrations from a single physical press.

## Requirements

## Hardware

Raspberry Pi (model 5)

Monitor

Keyboard

Resistors

Jumper wires / breadboard

## Software

Raspberry Pi OS