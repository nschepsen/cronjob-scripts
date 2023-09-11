#!/bin/bash

# Prepare, HEADER: Define useful FUNCTIONS, GLOBALS & HELPERS

TAB="  " # 2 spaced tab steps
# MariaDB login credentials (docker instance)
CREDENTIALS=('DB_USR' 'DB_PWD') # replace by valid credentials
DB_INSTANCE="mariadb" # docker instance name
# DBs used by Seafile, e.g. ccnet_db, seafile_db and seahub_db
DBs=('ccnet' 'seafile' 'seahub') # Attention! not default names
# Define a path where "DB DUMPS" will be stored
DB_DUMPS_PATH="/home/ubuntu/storage/"
# The sync application is "RClone" syncs files to the YandexDisk
RCLONE_CFG_FILE="/home/ubuntu/.config/rclone/rclone.conf"

function summary()
{
    # Check if there were provided arguments e.g. "$1"
    if [ -z "$1" ]
        then
            echo 'Warning: There were no arguments provided'
            return 1
    fi
    # Parse useful informations out ouf Rclone OUTPUT
    KPA=('Transferred' 'Errors' 'Checks' 'Elapsed')
    for tag in "${KPA[@]}"
        do
            OUTPUT=$(echo "$1" | grep "$tag" | tr -s ' ')
            if [ -n "$OUTPUT" ]
                then
                    echo "${TAB}${TAB}"${OUTPUT} # TODO: The "newline" Problem
            fi
        done
    # usage: summary "$1", where "$1" is the rclone OUTPUT provided by --stats-log-level NOTICE
}

T0=$(date +%s) # Measurement: Start TIME

# Prepare, STEP 0: Set Environment Variables

SF_VERSION=$(docker image inspect docker.seadrive.org/seafileltd/seafile-pro-mc:latest | grep -Eo -m 1 'SEAFILE_VERSION=[0-9\.]+' | awk -F '=' '{print $2}')

echo "Hello, You are running Seafile Server v${SF_VERSION}"
echo "Step 0: Prepare"
echo "${TAB}Date: $(date)"
echo "${TAB}Version: ${SF_VERSION}"

SEAFILE_DATA_PATH="/opt/dockers/seafile/seafile-data/"

if [ ! -d "$SEAFILE_DATA_PATH" ]
    then
        echo "Error: '$SEAFILE_DATA_PATH' is not found... Exit!"
        exit 1
fi
echo "${TAB}SfData: ${SEAFILE_DATA_PATH::-1}"

# MariaDB, STEP 1: Dump MariaDB (docker instance)

echo "Step 1: MariaDB"
mkdir -p "$DB_DUMPS_PATH" # create a directory
# delete SQL dumps older than 14 days
find "$DB_DUMPS_PATH" -mtime +14 -type f -delete
echo "${TAB}Dumping into the directory: ${DB_DUMPS_PATH::-1}"
SQL_GZIPPED="${DB_DUMPS_PATH}seafile-${SF_VERSION}-$(date +%Y%m%d%H%M).sql.gz"
# Don't forget to change the name of your MariaDB docker instance
docker exec -e MYSQL_PWD="${CREDENTIALS[1]}" "${DB_INSTANCE}" mysqldump -u"${CREDENTIALS[0]}" --databases "${DBs[@]}" | gzip > "$SQL_GZIPPED"

# YandexDisk, STEP 2: Sync our DATA using RClone

echo "Step 2: Remote Storage"
echo "${TAB}Rcloning to the YandexDisk (DB)"
OUTPUT=$(rclone sync "$DB_DUMPS_PATH" YandexDisk:DBRecGZips --config "$RCLONE_CFG_FILE" --stats 24h -v 2>&1 > /dev/null)
summary "$OUTPUT"
echo "${TAB}Rcloning to the YandexDisk (SD)"
OUTPUT=$(rclone sync "$SEAFILE_DATA_PATH" YandexDisk:Seafile --config "$RCLONE_CFG_FILE" --stats 24h -v 2>&1 > /dev/null)
summary "$OUTPUT"
T1=$(date +%s) # Measurement: End TIME
echo "Completed! The execution time was $(($T1 - $T0)) seconds"
