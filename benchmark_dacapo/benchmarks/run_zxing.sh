#!/bin/bash
set -e  # Exit on error

# === Step 1: Remove old tar and checksum file ===
echo "Removing old checksum file..."
rm -f /home/hpeng/E2COOL/benchmark_dacapo/benchmarks/bms/zxing/downloads/zxing-zxing-3.5.2.tar.gz.MD5
echo "Removing old tar file..."
rm -f /home/hpeng/E2COOL/benchmark_dacapo/benchmarks/bms/zxing/downloads/zxing-zxing-3.5.2.tar.gz

# === Step 2: Compress updated source ===
echo "Compressing updated zxing source..."
cd /home/hpeng/E2COOL/benchmark_dacapo/benchmarks/bms/zxing/build/
tar -czvf zxing-zxing-3.5.2.tar.gz *
# Move the tar.gz to downloads/
mv zxing-zxing-3.5.2.tar.gz ../downloads/

# === Step 3: Clean old zxing build directory ===
echo "Cleaning old build directory..."
if [ -d /home/hpeng/E2COOL/benchmark_dacapo/benchmarks/bms/zxing/build/ ]; then
    sudo rm -rf /home/hpeng/E2COOL/benchmark_dacapo/benchmarks/bms/zxing/build/
fi

# === Step 4: Switch to Java 8 for building ===
echo "Switching to Java 8 for build..."
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH

# === Step 5: Build zxing benchmark ===
cd /home/hpeng/E2COOL/benchmark_dacapo/benchmarks/
echo "Building DaCapo benchmark"
ant zxing

# === Step 6: Run the zxing benchmark ===
echo "Running DaCapo zxing benchmark..."
if [ -f dacapo-evaluation-git-4e3de06d-dirty.jar ]; then
    java -jar dacapo-evaluation-git-4e3de06d-dirty.jar --no-validation zxing
else
    java -jar dacapo-evaluation-git-4e3de06d.jar --no-validation zxing
fi
