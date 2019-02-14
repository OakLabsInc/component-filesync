#!/bin/bash

mkdir -p green blue
if [ ! -L live ] || [ ! -L idle ]; then
   ln -snf green live
   ln -snf blue idle
fi
