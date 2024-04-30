#!/usr/bin/env sh

# Checks that the last four characters of the tests mean they passed
echo "Input --> $1"
key='PASS'
echo "Key   --> $key"

if [ "$1" != $key ];
    then echo 'test failure!!!';
    exit 1;
else echo 'test success!!!';
    exit 0;
fi;