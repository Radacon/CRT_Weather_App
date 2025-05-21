#!/bin/bash

GPIO=6

# Export GPIO if not already exported
if [ ! -e /sys/class/gpio/gpio$GPIO ]; then
    echo $GPIO > /sys/class/gpio/export
fi

# Set direction to output
echo out > /sys/class/gpio/gpio$GPIO/direction

# Set GPIO to HIGH (1)
echo 0 > /sys/class/gpio/gpio$GPIO/value
