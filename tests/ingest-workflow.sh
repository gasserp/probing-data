#!/usr/bin/env bash
set -euo pipefail

helper=.github/scripts/registry-has-sources.sh

check_registry() {
  local expected=$1
  local registry=$2
  local actual
  actual=$(printf '%s\n' "$registry" | bash "$helper" -)
  test "$actual" = "$expected"
}

check_registry false \
  '{"schema_version":"probing.registry/v1","repository":"gasserp/probing-data","sources":[]}'
check_registry true \
  '{"schema_version":"probing.registry/v1","repository":"gasserp/probing-data","sources":[{"enabled":false},{"enabled":false}]}'
check_registry true \
  '{"schema_version":"probing.registry/v1","repository":"gasserp/probing-data","sources":[{"enabled":true}]}'
