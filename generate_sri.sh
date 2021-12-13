#!/bin/bash

echo -n sha384-; \
    cat $1 | \
    openssl dgst -sha384 -binary | \
    base64