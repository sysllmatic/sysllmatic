#!/bin/bash
set -e  # Exit on error

# === Step 1: Remove old tar and checksum file ===
echo "Removing old checksum file..."
rm -f /home/hpeng/E2COOL/benchmark_dacapo/benchmarks/bms/fop/downloads/fop-2.8-src.tar.gz.MD5
echo "Removing old tar file..."
rm -f /home/hpeng/E2COOL/benchmark_dacapo/benchmarks/bms/fop/downloads/fop-2.8-src.tar.gz

# === Step 2: Compress updated source ===
echo "Compressing updated fop source..."
cd /home/hpeng/E2COOL/benchmark_dacapo/benchmarks/bms/fop/build/
tar -czvf fop-2.8-src.tar.gz *
# Move the tar.gz to downloads/
mv fop-2.8-src.tar.gz ../downloads/

# === Step 3: Clean old fop build directory ===
echo "Cleaning old build directory..."
if [ -d /home/hpeng/E2COOL/benchmark_dacapo/benchmarks/bms/fop/build/ ]; then
    sudo rm -rf /home/hpeng/E2COOL/benchmark_dacapo/benchmarks/bms/fop/build/
fi

# === Step 4: Switch to Java 8 for building ===
echo "Switching to Java 8 for build..."
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH

# === Step 5: Build fop benchmark ===
cd /home/hpeng/E2COOL/benchmark_dacapo/benchmarks/
echo "Building DaCapo benchmark"
ant fop

# === Step 6: Run the fop benchmark ===
echo "Running DaCapo fop benchmark..."
if [ -f dacapo-evaluation-git-4e3de06d-dirty.jar ]; then
    java -jar dacapo-evaluation-git-4e3de06d-dirty.jar --no-validation fop
else
    java -jar dacapo-evaluation-git-4e3de06d.jar --no-validation fop
fi
