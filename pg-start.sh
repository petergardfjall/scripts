#!/bin/bash

#
# Starts a postgres server in a separate Docker container.
#
# If supplied a first argument, it will be taken as a host directory that either
# already holds a database or will be used to intialize a database.
#
# Without arguments the database is not persistent and only exists as long as
# the container exists.
#

set -e

# host port on which to expose postgres server's port 5432
export POSTGRES_PORT=${POSTGRES_PORT:-5432}
export POSTGRES_USER=${POSTGRES_USER:-postgres}
export POSTGRES_PASSWORD=${POSTGRES_PASSWORD:-password}

container_name="${container_name:-pg-server}"

# The first program argument denotes a directory that will be used to store
# data.
data_dir="${1}"
if [ -n "${data_dir}" ]; then
    echo "using data directory ${data_dir}"
    data_dir="$(realpath ${data_dir})"
    mkdir -p "${data_dir}"
    host_volume_opts="-e PGDATA=/var/lib/postgresql/data/pgdata -v ${data_dir}:/var/lib/postgresql/data/pgdata -v /etc/passwd:/etc/passwd:ro -u $(id -u):$(id -g)"
fi

echo "starting postgres container ..."
docker run -d --rm --name="${container_name}" \
       -p ${POSTGRES_PORT}:5432 \
       -e POSTGRES_USER=${POSTGRES_USER} \
       -e POSTGRES_PASSWORD=${POSTGRES_PASSWORD} \
       -e TZ=UTC ${host_volume_opts} \
       postgres:12

function cleanup {
    echo "exit: killing postgres container ..."
    docker rm -f "${container_name}"
}
trap cleanup EXIT

until docker exec "${container_name}" /usr/bin/pg_isready; do
    echo "waiting for postgres server to be ready ..."
    sleep 5s
done
echo "postgres ready"

docker logs -f ${container_name}
