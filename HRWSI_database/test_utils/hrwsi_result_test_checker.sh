# Checks that the last four characters of the tests mean they passed
if [[ $1 != 'PASS' ]]; then echo 'test failure!!!';exit 1;else echo 'test success!!!';exit 0;fi;