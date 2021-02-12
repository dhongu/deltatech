#!/bin/bash





for d in deltatech*/ ; do

MODUL=${d%/*}
DATABSE="rsy"

if [ 1 == 2 ]
then
    rm /tmp/en.po
    rm /tmp/ro.po

    /home/dhongu/odoo/odoo.py --config=/home/dhongu/odoo.conf --log-level=error -d $DATABSE --i18n-export=/tmp/en.po --modules=$MODUL
    mkdir ./$MODUL/i18n -p
    mv /tmp/en.po ./$MODUL/i18n/$MODUL.pot

    /home/dhongu/odoo/odoo.py --config=/home/dhongu/odoo.conf --log-level=error -d $DATABSE --i18n-export=/tmp/ro.po --modules=$MODUL --language=ro_RO
    mv /tmp/ro.po ./$MODUL/i18n/ro.po

    echo "Fisier generat: $MODUL/i18n/ro.po"

fi
tx set --auto-remote  https://www.transifex.com/projects/p/deltatech-80/resource/$MODUL/
tx set --auto-local -r deltatech-80.$MODUL "$MODUL/i18n/<lang>.po" --source-language=en --source-file $MODUL/i18n/$MODUL.pot --execute
done




