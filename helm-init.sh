#!/bin/bash

#
# A script that sets up a secure Tiller server in the kubernetes cluster pointed
# to by the KUBECONFIG.
#

set -e

scriptname=$(basename ${0})

function log() {
    echo -e "\e[32m[${scriptname}]: ${1}\e[0m"
}

function die_with_error() {
    echo "error: ${1}"
    exit 1
}

which cfssl 2>&1 > /dev/null || die_with_error "error: cfssl needs to be on your PATH"
which cfssljson 2>&1 > /dev/null|| die_with_error "error: cfssljson needs to be on your PATH"
which kubectl 2>&1 > /dev/null|| die_with_error "error: kubectl needs to be on your PATH"
which helm 2>&1 > /dev/null|| die_with_error "error: helm needs to be on your PATH"

[[ -z ${KUBECONFIG} ]] && die_with_error "KUBECONFIG needs to be set"

#
# prepare a PKI with certificates for helm and tiller
#
pki_dir=./pki
mkdir -p ${pki_dir}
# create a CA cert to sign other certs
if ! [ -f ${pki_dir}/ca.pem ]; then
    log "creating a CA certificate under ${pki_dir} ..."
    cert-create-ca --output-dir=${pki_dir} "/CN=helm-ca" 2>&1 > /dev/null
fi
# create certificate for tiller
if ! [ -f ${pki_dir}/tiller.pem ]; then
    log "creating a server certificate for tiller under ${pki_dir} ..."
    cert-create-casigned-server --output-dir=${pki_dir} "tiller" 2>&1 > /dev/null
fi
# create certificate for helm
if ! [ -f ${pki_dir}/helm.pem ]; then
    log "creating a client certificate for helm under ${pki_dir} ..."
    cert-create-casigned-client --output-dir=${pki_dir} "helm" 2>&1 > /dev/null
fi

# create an RBAC service account for tiller
log "creating a tiller service-account and RBAC setup ..."
rbac_manifest_path=$(mktemp /tmp/tillerrbac-XXX.yaml)
cat > ${rbac_manifest_path} <<EOF
apiVersion: v1
kind: ServiceAccount
metadata:
  name: tiller
  namespace: kube-system
---
apiVersion: rbac.authorization.k8s.io/v1beta1
kind: ClusterRoleBinding
metadata:
  name: tiller
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
subjects:
  - kind: ServiceAccount
    name: tiller
    namespace: kube-system
EOF
kubectl apply -f ${rbac_manifest_path}

#
# Initialize tiller to make use of the service account and make use of the
# generated cert.
#
log "running helm init ..."
helm init \
     --service-account=tiller \
     --tiller-tls \
     --tiller-tls-cert=${pki_dir}/tiller.pem \
     --tiller-tls-key=${pki_dir}/tiller-key.pem \
     --tiller-tls-verify \
     --tls-ca-cert=${pki_dir}/ca.pem

log "Done. To make use of helm make sure to set the following environment variables: "
cat <<EOF
export HELM_TLS_CA_CERT=$(realpath ${pki_dir})/ca.pem
export HELM_TLS_CERT=$(realpath ${pki_dir})/helm.pem
export HELM_TLS_KEY=$(realpath ${pki_dir})/helm-key.pem
export HELM_TLS_ENABLE=true
EOF
