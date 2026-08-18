#!/bin/bash

# Verificar existencia y tamaño de los archivos
for file in time_results.txt ctime_results.txt cprofile_results.txt pyinstrument_results.html; do
  if [ ! -f "$file" ]; then
    echo "Error: El archivo $file no existe."
    exit 1
  fi
  if [ $(wc -c <"$file") -lt 2 ]; then
    echo "Error: El archivo $file tiene menos de 2 caracteres."
    exit 1
  fi
done

echo "Todos los archivos existen y tienen al menos 2 caracteres."
