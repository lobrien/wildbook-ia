#!/bin/bash
cd $(dirname $0)

# <CORRECT_PYTHON>
# GET CORRECT PYTHON ON ALL PLATFORMS
export PYMAJOR="$(python -c "import sys; print(sys.version_info[0])")"
export SYSNAME="$(expr substr $(uname -s) 1 10)"
if [ "$SYSNAME" = "MINGW32_NT" ]; then
    export PYEXE=python
else
    if [ "$PYMAJOR" = "3" ]; then
        # virtual env?
        export PYEXE=python
    else
        export PYEXE=python2.7
    fi
fi
# </CORRECT_PYTHON>

$PYEXE ibeis/tests/reset_testdbs.py $@
echo "PYEXE = $PYEXE"
#python ibeis/tests/test_gui_import_images.py --set-dbdir
#python ibeis/tests/test_gui_add_roi.py


#profiler.sh ibeis/tests/reset_testdbs.py
