#!/usr/bin/env bash

scriptname=$(basename ${0})
scriptdir=$(dirname ${0})

# default user to log in with on master node
ssh_user=ubuntu
# default ssh key to use when logging in to master node
ssh_key=~/.ssh/id_rsa

function die_with_error() {
    echo "error: ${1}"
    exit 1
}

function print_usage() {
    echo "${scriptname} [OPTIONS] <master-host>"
    echo ""
    echo "Sets up kubectl for working against a particular k8s cluster."
    echo "********************************************************************"
    echo " NOTE: the script works under the assumption that kubeadm was used"
    echo "       to set up cluster and that admin.conf was copied to "
    echo "       ~/.kube/config."
    echo "********************************************************************"
    echo
    echo "It copies the kubectl config (via scp) from the given master"
    echo "and merges the config with your existing ~/.kube/config."
    echo "On success, the kubectl context will be set to the specified cluster."
    echo ""
    echo "OPTIONS:"
    echo "--kube-name=NAME  The name to set for the kubectl context before"
    echo "                  merging it into ~/.kube/config."
    echo "                  Default: <master-host>"
    echo "--ssh-user=USER   The username to use when logging in to master node."
    echo "                  Default: ${ssh_user}"
    echo "--ssh-key=PATH    SSH key used to login to master node."
    echo "                  Default: ${ssh_key}"
    echo "--help            Displays this message."
    echo ""
}

for arg in ${@}; do
    case ${arg} in
        --kube-name=*)
            kube_name=${arg#*=}
            ;;
        --ssh-user=*)
            ssh_user=${arg#*=}
            ;;
        --ssh-key=*)
            ssh_key=${arg#*=}
            ;;
        --help)
            print_usage
            exit 0
            ;;
        --*)
            die_with_error "unrecognized option: ${arg}"
            ;;
        *)
            # no option, assume only positional arguments left
            break
            ;;
    esac
    shift
done

if [ -z $1 ]; then
    die_with_error "missing argument: no <master_host> given"
fi
master_node=${1}

if [ -z ${kube_name} ]; then
    kube_name=${master_node}
fi

if [ ! -d ~/.kube ]; then
    mkdir ~/.kube
fi

# take care of ~ expansion
ssh_key="${ssh_key/#\~/$HOME}"
if ! [ -f ${ssh_key} ]; then
    die_with_error "could not find master ssh key: ${ssh_key}"
fi
# ensure proper rights set on key
cp ${ssh_key} /tmp/.tmp_ssh_key
chmod 600 /tmp/.tmp_ssh_key

# NOTE: assumption is that kubeadm was used to set up cluster and that
#       the admin.conf was copied to $HOME/.kube/config
echo "copying kubectl config from ${master_node} (user: ${ssh_user}, key: ${ssh_key})..."
scp -q -i /tmp/.tmp_ssh_key ${ssh_user}@${master_node}:~/.kube/config /tmp/${kube_name}.conf
exitcode=${?}
rm -f /tmp/.tmp_ssh_key
if [ ${exitcode} -ne 0 ]; then
    die_with_error "failed to get kubectl config"
fi

# rename all occurences of `kubernetes` (used for all names in the kubeconfig)
# to the name of the master node
sed -i "s/kubernetes/${kube_name}/g" /tmp/${kube_name}.conf

# rename context to master node name
ctx_name=$(KUBECONFIG=/tmp/${kube_name}.conf kubectl config current-context)
KUBECONFIG=/tmp/${kube_name}.conf kubectl config rename-context ${ctx_name} ${kube_name}

#
# merge kubeconfig into ~/.kube/config or create if it doesn't exist
#
if [ -f ~/.kube/config ]; then
    # merge with existing ~/.kube/conf
    echo "kubeconfig will be merged into existing ~/.kube/config ..."
    cp ~/.kube/config ~/.kube/config.bak
    mergepaths=/tmp/${kube_name}.conf:~/.kube/config
else
    # ~/.kube/conf will be created
    echo "kubeconfig will be written to ~/.kube/config ..."
    mergepaths=/tmp/${kube_name}.conf
fi
KUBECONFIG=${mergepaths} kubectl config view --flatten > ~/.kube/config-merged
mv ~/.kube/config-merged ~/.kube/config

kubectl config use-context ${kube_name}
echo "kubectl set up to use context $(kubectl config current-context)"
