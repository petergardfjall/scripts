#!/bin/bash

#
# A script that uses duplicity to back up a given set of local directories
# to a Google Drive folder.
#
# Run without arguments to see help text.
#

set -e

scriptname=$(basename ${0})

function log() {
    echo "[${scriptname}] ${1}"
}

function die_with_error() {
    echo $1 2>&1
    echo
    echo "usage: ${scriptname} <google-account-mail>/folder DIR ..."
    echo ""
    echo "Backs up each given local directory DIR to the given Google Drive"
    echo "folder using the specified Google account. To delegate duplicity"
    echo "access rights to your Drive, you need to create an OAuth client ID"
    echo "credential (of type 'Other') in the Google Developer Console."
    echo "For details on setting up the Google service account refer to:"
    echo "  http://duplicity.nongnu.org/duplicity.1.html#sect22"
    echo 
    echo "The following environment variables MUST be set:"
    echo "  GOOGLE_DRIVE_SETTINGS=/path/to/gdrive/client/settings"
    echo "For details on the appearance of such a settings file, refer to"
    echo "the duplicity man page 'a Note on Pydrive backend'."
    echo "The script must be run interactively the first time, since the"
    echo "user will need to open a consent screen in the browser."
    echo
    echo "The following environment variables MAY be set:"
    echo "  EXCLUDE_FILELIST=/path/to/exclude/filelist"
    echo "This is a file listing file patterns that are to be exclued from"
    echo "the backup. See the duplicity man page (FILE SELECTION)."
    echo 
    echo "The script produces a full backup every FULL_BACKUP_PERIOD days "
    echo "(default 14). The script will keep at most RETAINED_FULL_BACKUPS "
    echo "(default 2) full backup chains around in the targeted folder."
    echo ""
    echo "NOTE: to be able to backup all files in system directories you need "
    echo "      to run this script with sudo privileges."
    echo ""
    echo "To restore a certain backed up dir/file to a given point in time use"
    echo "(run as root to get restored file ownerships correct):"
    echo "  # duplicity restore --no-encryption [--file-to-restore <relpath>] [--time <time>] pydrive://<google-account-mail>:/<folder> <local_dest_dir>"
    exit 1
}

if [ "${GOOGLE_DRIVE_SETTINGS}" = "" ]; then
    die_with_error "error: must set \${GOOGLE_DRIVE_SETTINGS}"
fi

if ! [ -f ${GOOGLE_DRIVE_SETTINGS} ]; then
    die_with_error "error: \${GOOGLE_DRIVE_SETTINGS} file does not exist: ${GOOGLE_DRIVE_SETTINGS}"
    exit 1
fi

if [ "${EXCLUDE_FILELIST}" != "" ]; then
    if ! [ -f ${EXCLUDE_FILELIST} ]; then
	die_with_error "error: \${EXCLUDE_FILELIST} file does not exist: ${EXCLUDE_FILELIST}"
    fi
    
    EXCLUDE_FILELIST_OPT="--exclude-filelist=${EXCLUDE_FILELIST}"
fi


if [ "$(whoami)" != "root" ]; then
    die_with_error "error: must run as root (to get access permissions right)"
fi

if [ "${1}" = "" ]; then
    die_with_error "error: no Google drive folder given"
fi
# can for example be
#   user.name@gmail.com/backups/myhost1
DRIVE_URL=pydrive://${1}
shift
# can, for example, be /home/peterg and /etc
BACKUP_DIRS=${@}
if [ "${BACKUP_DIRS}" = "" ]; then
    die_with_error "error: no local directories to be backed up given"
fi


# Number of days between every time a new full backup chain is started.
FULL_BACKUP_PERIOD=${FULL_BACKUP_PERIOD:-14}
# Number of full backup chains to keep around.
RETAINED_FULL_BACKUPS=${RETAINED_FULL_BACKUPS:-2}

included_dirs=""
for local_dir in ${BACKUP_DIRS}; do
    log "will back up local dir: ${local_dir}"
    included_dirs="${included_dirs} --include=${local_dir} "
done


log "backing up to ${DRIVE_URL}"
log "doing backup (full backup every ${FULL_BACKUP_PERIOD} days) ..."
duplicity incremental --full-if-older-than ${FULL_BACKUP_PERIOD}D \
	  --verbosity=warning --no-encryption --progress \
	  ${EXCLUDE_FILELIST_OPT} \
	  ${included_dirs} --exclude='**' / ${DRIVE_URL}

log "removing backups to keep only ${RETAINED_FULL_BACKUPS} full backup chains ..."
duplicity remove-all-but-n-full ${RETAINED_FULL_BACKUPS} --force ${DRIVE_URL}
