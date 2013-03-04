#! /bin/sh

#
# Performs a full (history-less) copy of an existing Git repository 
# to a new location. The new repository will have the same file tree
# as the old repository, but with the change history truncated.
#
# The operation initializes a new Git repository, and
# populates it with the current contents of an existing
# repository, without history.
#


if [ "${1}" = "" ]; then
  echo "error: missing source repo URL"
  echo "  usage: ${0} <source repo> <destination dir>"
  exit 1
fi
if [ "${2}" = "" ]; then
  echo "error: missing destination dir"
  echo "  usage: ${0} <source repo> <destination dir>"
  exit 1
fi


source_repo=${1}
destination_dir=`readlink -f ${2}`

# contents of old repository without git files
source_clone=`mktemp -d`
git clone ${source_repo} ${source_clone}
rm -rf ${source_clone}/.git
rm ${source_clone}/.gitignore

# create new repo and populate with current contents of old repo
git init --bare ${destination_dir}
dest_clone=`mktemp -d`
git clone ${destination_dir} ${dest_clone}
cp -r ${source_clone}/* ${dest_clone}
cd ${dest_clone}
git add *
git commit -am "initial commit"
git push origin master -u
cd ${destination_dir}
git update-server-info
