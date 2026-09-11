#!/usr/bin/env bash
set -euo pipefail

registry=${1:-registry/sources.json}
jq -er '
  if type != "object" or
     keys != ["repository", "schema_version", "sources"] or
     .schema_version != "probing.registry/v1" or
     .repository != "gasserp/probing-data" or
     (.sources | type) != "array"
  then
    error("registry has an unexpected top-level shape")
  elif (.sources | length) > 0
  then
    "true"
  else
    "false"
  end
' "$registry"
