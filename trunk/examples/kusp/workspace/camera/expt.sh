#!/bin/bash
rm -rf /tmp/rawdata
ssh elrond ndelay $1
ns_control -c dski.nspec netspec
X_VALUE=$1 postprocess f camera3.pipes
X_VALUE=$1 postprocess f dski.pipes

