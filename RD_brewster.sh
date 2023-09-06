#! /bin/bash
#
# Temporary setup!
#
# Local address 10.0.0.61
#
# Create a tunnel to run Microsoft Remote Desktop to truffle over ssh.
# The remote host name should be entered into RD as "localhost:13389"

# while true; do
#     ssh -N -L rd_truffle:13389:localhost:3389 home
#     sleep 60
# done

set -x
ssh -N -L rd_truffle:13389:localhost:3389 Pablo@73.89.21.230
