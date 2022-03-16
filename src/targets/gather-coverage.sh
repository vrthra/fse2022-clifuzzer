#!/bin/bash

OUTPUTDIR=./csv
if [ ! -d "$OUTPUTDIR" ]; then
    mkdir $OUTPUTDIR
fi
cp ~/gather-coverage.py .
cp gather-coverage.py bc/
cp gather-coverage.py binutils/
cp gather-coverage.py bison/
cp gather-coverage.py coreutils/
cp gather-coverage.py gdb/
cp gather-coverage.py groff/
cp gather-coverage.py spell/

cd bc
python3 gather-coverage.py . > dc.csv
cp dc.csv ../csv/
cd -

cd binutils
python3 gather-coverage.py . > as.csv
cp as.csv ../csv/
cd -

cd bison
python3 gather-coverage.py . > bison.csv
cp bison.csv ../csv/
cd -

cd coreutils
python3 gather-coverage.py . > ptx.csv
cp ptx.csv ../csv/
cd -

cd gdb
python3 gather-coverage.py . > gdb.csv
cp gdb.csv ../csv/
cd -

cd groff
python3 gather-coverage.py . > troff.csv
cp troff.csv ../csv/
cd -

cd spell
python3 gather-coverage.py . > spell.csv
cp spell.csv ../csv/
cd -
