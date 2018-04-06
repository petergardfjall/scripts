#!/bin/bash

scriptname=$(basename ${0})

# default user to log in with on nodes
ssh_user=ubuntu
# default ssh key to use when logging in to bides
ssh_key=~/.ssh/id_rsa

function log() {
    echo -e "\e[32m[${scriptname}] ${1}\e[0m"
}

function die_with_error() {
    echo -e "\e[33m[${scriptname}] error: ${1}\e[0m"
    exit 1
}

function print_usage() {
    echo "${scriptname} [OPTIONS] HOST ..."
    echo
    echo "Perform a full reset on a set of kubernetes nodes installed via"
    echo "kubeadm. This includes running 'kubeadm reset', clearing iptables,"
    echo "and removing any weave state files. Assumes that 'kubectl' is "
    echo "installed on the first host given."
    echo
    echo "OPTIONS:"
    echo ""
    echo "--ssh-user=USER   The username to use when logging in to master node."
    echo "                  Default: ${ssh_user}"
    echo "--ssh-key=PATH    SSH key used to login to master node."
    echo "                  Default: ${ssh_key}"
    echo "--help            Displays this message."
}

for arg in ${@}; do
    case ${arg} in
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

# take care of tilde expansion
log "ssh login user: ${ssh_user}"
log "ssh login key:  ${ssh_key}"

[ -z ${1} ] && die_with_error "no HOST(s) given"

master=${1}

ssh_master="ssh -i ${ssh_key} ${ssh_user}@${master}"

log "getting k8s namespaces from master ${master} ..."
namespaces=$(${ssh_master} kubectl get ns -o jsonpath='{.items[*].metadata.name}')
log "found namespaces: ${namespaces}"
for ns in ${namespaces}; do
    if echo ${ns} | egrep -v 'kube-system|default|kube-public'; then
        log "deleting namespace ${ns} ..."
        ${ssh_master} kubectl delete ns ${ns}
        # wait for namespace to be fully deleted (and allocated
        # resources, such as volumes/loadbalancers to be released)
        while ${ssh_master} kubectl get ns ${ns} > /dev/null; do
            log "waiting for namespace ${ns} to be deleted ..."
            sleep 10s
        done
    fi
done

log "deleting weave daemonset ..."
${ssh_master} kubectl delete ds -n kube-system weave-net

# clear each node
for node in ${@}; do
    ssh_node="ssh -i ${ssh_key} ${ssh_user}@${node}"

    log "clearing node ${node} ..."
    log "${node}: kubeadm reset ..."
    ${ssh_node} sudo kubeadm reset
    cat > /tmp/reset-weave.sh <<EOF
sudo curl -fsSL git.io/weave -o /usr/local/bin/weave
sudo chmod +x /usr/local/bin/weave
sudo weave reset --force
sudo rm /opt/cni/bin/weave-*
EOF
    log "${node}: reset weave ..."
    ${ssh_node} bash -s < /tmp/reset-weave.sh
    log "${node}: reset iptables ..."
    cat > /tmp/flush.sh <<EOF
sudo iptables -F
sudo iptables -X
sudo iptables -t nat -F
sudo iptables -t mangle -F
sudo iptables -P INPUT ACCEPT
sudo iptables -P FORWARD ACCEPT
sudo iptables -P OUTPUT ACCEPT
EOF
    if ${ssh_node} sudo systemctl status etcd.service > /dev/null; then
        log "${node}: clearing etcd state ..."
        ${ssh_node} sudo systemctl stop etcd.service
        # NOTE: assumed location of etcd --data-dir
        ${ssh_node} sudo rm -rf /var/lib/etcd/member
    fi
    ${ssh_node} bash -s < /tmp/flush.sh
    log "${node}: restart docker ..."
    ${ssh_node} sudo systemctl restart docker
    log "${node}: uninstall kubelet kubeadm ..."
    ${ssh_node} sudo apt-get purge -y kubelet kubeadm
done
