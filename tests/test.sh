#!/usr/bin/env sh

echo 'Building tester'
make > /dev/null

[ -f ./test ] && (echo 'Running tester' && LD_LIBRARY_PATH=libtap ./test)
