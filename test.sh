#!/bin/bash

set -e

echo "starting up"

git clean -xdf

GIT_BRANCH=test
PATH=$WORKSPACE/venv/bin:/usr/local/bin:$PATH
if [ ! -d "venv" ]; then
        virtualenv venv
fi
. venv/bin/activate

# install test requirements like tox
pip install --upgrade -r requirements_develop.txt

## All of this will go away when netshow-core is in PyPI

# Delete working directories
if [ -d wheel_dir ]; then
  echo "Delete wheel directory"
  rm -rf wheel_dir
fi
if [ -d .temp ]; then
  echo "Delete temp install directory"
  rm -rf .temp
fi

# Make working directories
echo "Create wheel directory"
mkdir wheel_dir
echo "Create temp install directory"
mkdir .temp

# Go into the temp directory and install netshow-lib
echo "Go into temp install directory"
cd .temp

echo "Install netshow-core repo"
git clone -b $GIT_BRANCH https://github.com/CumulusNetworks/netshow-core.git netshow-core

echo " Install netshow-core-lib"
cd netshow-core/netshow-lib

echo "Create wheel for netshow-core-lib"
python setup.py bdist_wheel
echo "Install wheel in wheel directory"
cp dist/* ../../../wheel_dir/

echo "Create wheel for netshow-core"
cd ../netshow
python setup.py bdist_wheel
echo "Install wheel in wheel directory"
cp dist/* ../../../wheel_dir/

echo "Return back to the directory with test.sh"
cd ../../../

echo "Run Tox"
tox
