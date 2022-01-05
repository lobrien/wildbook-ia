#!/bin/bash

set -ex

setup

source /bin/setup

# Supply EXEC_PRIVILEGED=1 to run your given command as the privileged user.
if [ $EXEC_PRIVILEGED ]; then
    exec $@
else
    exec gosu ${HOST_USER}:${HOST_USER} $@
fi
