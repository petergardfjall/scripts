#!/bin/bash

#
# Starts a clickhouse database server in a separate Docker container.
#
# If supplied a first argument, it will be taken as a host directory that either
# already holds a database or will be used to intialize a database.
#
# Without arguments the database is not persistent and only exists as long as
# the container exists.
#
# After starting up you can use the server with a call like:
#   echo 'SELECT version();' | curl --user clickhouse:password http://localhost:8123/ --data-binary @-
#
#   clickhouse-client --user=clickhouse --password=password [--query '<query>']
#

set -e

# Port used by clickhouse-client.
export CLICKHOUSE_PORT=${CLICKHOUSE_PORT:-9000}
# HTTP port.
export CLICKHOUSE_HTTP_PORT=${CLICKHOUSE_HTTP_PORT:-8123}
export CLICKHOUSE_USER=${CLICKHOUSE_USER:-clickhouse}
export CLICKHOUSE_PASSWORD=${CLICKHOUSE_PASSWORD:-password}

container_name="${container_name:-clickhouse-server}"

# The first program argument denotes a directory that will be used to store
# data.
data_dir="${1}"
if [ -n "${data_dir}" ]; then
    echo "using data directory ${data_dir}"
    data_dir="$(realpath ${data_dir})"
    mkdir -p "${data_dir}/ch_data"
    mkdir -p "${data_dir}/ch_logs"
    host_volume_opts="-v ${data_dir}/ch_data:/var/lib/clickhouse/ -v ${data_dir}/ch_logs:/var/log/clickhouse-server/  -v /etc/passwd:/etc/passwd:ro -u $(id -u):$(id -g)"
fi

echo "starting clickhouse container ..."

docker run -d --rm --name="${container_name}" \
       -p ${CLICKHOUSE_HTTP_PORT}:8123 \
       -p ${CLICKHOUSE_PORT}:9000 \
       -e CLICKHOUSE_USER=${CLICKHOUSE_USER} \
       -e CLICKHOUSE_PASSWORD=${CLICKHOUSE_PASSWORD} \
       --ulimit nofile=262144:262144 \
       ${host_volume_opts} \
       clickhouse/clickhouse-server:25.8-alpine

function cleanup {
    echo "exit: killing clickhouse container ..."
    docker rm -f "${container_name}"
}
trap cleanup EXIT

docker logs -f ${container_name}
