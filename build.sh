#!/bin/bash

# 1. Create the output directory
mkdir -p core_logic

# 2. Compile C++ files into a Shared Object (.so) library
# -fPIC: Position Independent Code (Required for shared libs)
# -shared: Create the library instead of an executable
# -o: The output path
g++ -fPIC -shared -o core_logic/core_logic.so route_brain.cpp booking_brain.cpp

echo "Compilation Complete. Library saved to core_logic/core_logic.so"