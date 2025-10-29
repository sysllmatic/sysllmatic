#!/bin/bash
set -e  # Exit on error

# === Step 1: Remove old tar and checksum file ===
echo "Removing old checksum file..."
rm -f /home/hpeng/E2COOL/benchmark_dacapo/benchmarks/bms/biojava/downloads/biojava-7.1.1.tar.gz.MD5
echo "Removing old tar file..."
rm -f /home/hpeng/E2COOL/benchmark_dacapo/benchmarks/bms/biojava/downloads/biojava-7.1.1.tar.gz

# === Step 2: Compress updated source ===
echo "Compressing updated biojava source..."
cd /home/hpeng/E2COOL/benchmark_dacapo/benchmarks/bms/biojava/build/
tar -czvf biojava-7.1.1.tar.gz *
# Move the tar.gz to downloads/
mv biojava-7.1.1.tar.gz ../downloads/

# === Step 3: Clean old biojava build directory ===
echo "Cleaning old build directory..."
if [ -d /home/hpeng/E2COOL/benchmark_dacapo/benchmarks/bms/biojava/build/ ]; then
    sudo rm -rf /home/hpeng/E2COOL/benchmark_dacapo/benchmarks/bms/biojava/build/
fi

# === Step 4: Switch to Java 8 for building ==
echo "Switching to Java 8 for build..."
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH

# === Step 5: Build biojava benchmark ===
cd /home/hpeng/E2COOL/benchmark_dacapo/benchmarks/
echo "Building DaCapo benchmark"
ant biojava

# === Step 6: Switch to Java 11 for running ===
echo "Switching to Java 11 for benchmark run..."
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH

# === Step 7: Run the biojava benchmark ===
echo "Running DaCapo biojava benchmark..."
if [ -f dacapo-evaluation-git-4e3de06d-dirty.jar ]; then
    java -jar dacapo-evaluation-git-4e3de06d-dirty.jar --no-validation biojava
else
    java -jar dacapo-evaluation-git-4e3de06d.jar --no-validation biojava
fi
