#!/bin/bash

#
# A script that uses duplicity to back up a given set of local directories
# to an Amazon S3 bucket.
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
    echo "usage: ${scriptname} <s3bucket>[/<folder>] DIR ..."
    echo ""
    echo "Backs up each given local directory DIR to the given S3 bucket."
    echo "The following environment variables need to be set:"
    echo "  AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_DEFAULT_REGION."
    echo ""
    echo "The script produces a full backup every FULL_BACKUP_PERIOD days "
    echo "(default 14). The script will keep at most RETAINED_FULL_BACKUPS "
    echo "(default 2) full backup chains around in the targeted bucket.".
    echo ""
    echo "NOTE: to be able to backup all files in system directories you need "
    echo "      to run this script with sudo privileges."
    echo ""
    echo "To restore a certain backed up dir/file to a given point in time use"
    echo "(run as root to get restored file ownerships correct):"
    echo "  # source my-aws-credentials.env"
    echo "  # duplicity restore --no-encryption [--file-to-restore <relpath>] [--time <time>] <S3-URL> <local_dest_dir>"
    exit 1
}


if [ "$(whoami)" != "root" ]; then
    die_with_error "error: must run as root (to get access permissions right)"
fi

if [ "${1}" = "" ]; then
    die_with_error "error: no S3 bucket [and optional folder] given"
fi
# can, for example, be peterg-backup/titan
S3_BUCKET=${1}
shift
# can, for example, be /home/peterg and /etc
BACKUP_DIRS=${@}
if [ "${BACKUP_DIRS}" = "" ]; then
    die_with_error "error: no local directories to be backed up given"
fi


[[ "${AWS_ACCESS_KEY_ID}" = "" ]] && die_with_error "error: not set: AWS_ACCESS_KEY_ID"
[[ "${AWS_SECRET_ACCESS_KEY}" = "" ]] && die_with_error "error: not set: AWS_SECRET_ACCESS_KEY"
[[ "${AWS_DEFAULT_REGION}" = "" ]] && die_with_error "error: not set: AWS_DEFAULT_REGION"

# Number of days between every time a new full backup chain is started.
FULL_BACKUP_PERIOD=${FULL_BACKUP_PERIOD:-14}
# Number of full backup chains to keep around.
RETAINED_FULL_BACKUPS=${RETAINED_FULL_BACKUPS:-2}

S3_OPTS="--s3-use-new-style"
if echo ${AWS_DEFAULT_REGION} | grep --silent "eu"; then
    # if in europe, we need to specify this option. See
    # "a Note on European S3 Buckets" in the duplicity man page.
    S3_OPTS="${S3_OPTS} --s3-european-buckets"
fi

S3_URL=s3://s3-${AWS_DEFAULT_REGION}.amazonaws.com/${S3_BUCKET}

included_dirs=""
for local_dir in ${BACKUP_DIRS}; do
    log "will back up local dir: ${local_dir}"
    included_dirs="${included_dirs} --include=${local_dir} "
done

log "backing up to ${S3_URL}"
log "doing backup (full backup every ${FULL_BACKUP_PERIOD} days) ..."
duplicity incremental --full-if-older-than ${FULL_BACKUP_PERIOD}D \
	  --verbosity=warning --no-encryption --progress \
	  ${S3_OPTS} ${included_dirs} --exclude='**' / ${S3_URL}

log "removing backups to keep only ${RETAINED_FULL_BACKUPS} full backup chains ..."
duplicity remove-all-but-n-full ${RETAINED_FULL_BACKUPS} --force ${S3_URL}
