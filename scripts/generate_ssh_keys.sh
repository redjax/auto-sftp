#!/bin/bash

KEYNAME="colossus_docuhost_backup"
PUBLIC_KEYNAME="${KEYNAME}.pub"

function check_key_exists() {
    ## $1=keyname

    if [[ -f "~/.ssh/${KEYNAME}" ]]; then
        echo "Found key '${KEYNAME}' at path ~/.ssh/${KEYNAME}. Skipping key generation"
        return 3
    else
        return 0
    fi
}

function generate_ssh_keys() {
    echo "Generating SSH keys."
}

function main() {
    check_key_exists $KEYNAME

    case $? in
    0)
        generate_ssh_keys
        ;;
    1)
        echo "[ERROR] Unhandled exception checking if key '${KEYNAME}' exists at ~/.ssh."

        return 1
        ;;
    2)
        echo "[ERROR] Unhandled error"
        return 2
        ;;
    3)
        echo "Key '${KEYNAME}' exists at ~/.ssh."
        ;;
    esac
}

main

case $? in
0)
    echo "Keys created successfully."

    exit 0
    ;;
1)
    echo "Unhandled error creating SSH keys."

    exit 1
    ;;
2)
    echo "Unknown error creating SSH keys."

    exit 2
    ;;
3)
    echo "Key already exists at path ~/.ssh/${KEYNAME}"

    exit 0
    ;;
esac
