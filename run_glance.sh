#!/bin/bash

echo $HOSTNAME
netw=`/home/obs/bin/whereami`

#python create_report.py
#create_tree_data.py
git add *
git commit -m "Regular commit of $HOSTNAME on the ${netw} network at `date`"
git push
