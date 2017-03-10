#!/bin/bash
cat /sys/bus/w1/devices/28-000004c3ec5f/w1_slave | tail -1 | cut -d ' ' -f 10 | cut -d '=' -f 2
