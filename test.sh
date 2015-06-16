#!/bin/bash

set -e

echo "starting up"

PATH=$WORKSPACE/venv/bin:/usr/local/bin:$PATH
if [ ! -d "venv" ]; then
        virtualenv venv
fi
. venv/bin/activate

pip install -r requirements_develop.txt

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
git clone ssh://git@github.com/CumulusNetworks/netshow-core.git netshow-core

echo " Install netshow-core-lib"
cd netshow-core/netshow-lib

echo "Move into devel branch"
git checkout devel
echo "Create wheel for netshow-core-lib"
python setup.py bdist_wheel
echo "Install wheel in wheel directory"
cp dist/* ../../../wheel_dir/

echo " Install netshow-core-lib"
cd ../netshow
echo "Create wheel for netshow-core-lib"
python setup.py bdist_wheel
echo "Install wheel in wheel directory"
cp dist/* ../../../wheel_dir/

echo "Return back to the directory with test.sh"
cd ../../../

echo "Run Tox"
tox
