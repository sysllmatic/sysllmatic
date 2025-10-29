#!/bin/bash
set -e  # Exit on error

# === Step 1: Remove old tar and checksum file ===
echo "Removing old checksum file..."
rm -f /home/hpeng/E2COOL/benchmark_dacapo/benchmarks/bms/graphchi/downloads/graphchi-java-src-0.2.2.tar.gz.MD5
echo "Removing old tar file..."
rm -f /home/hpeng/E2COOL/benchmark_dacapo/benchmarks/bms/graphchi/downloads/graphchi-java-src-0.2.2.tar.gz

# === Step 2: Compress updated source ===
echo "Compressing updated graphchi source..."
cd /home/hpeng/E2COOL/benchmark_dacapo/benchmarks/bms/graphchi/build/
tar -czvf graphchi-java-src-0.2.2.tar.gz *
# Move the tar.gz to downloads/
mv graphchi-java-src-0.2.2.tar.gz ../downloads/

# === Step 3: Clean old graphchi build directory ===
echo "Cleaning old build directory..."
if [ -d /home/hpeng/E2COOL/benchmark_dacapo/benchmarks/bms/graphchi/build/ ]; then
    sudo rm -rf /home/hpeng/E2COOL/benchmark_dacapo/benchmarks/bms/graphchi/build/
fi

# === Step 4: Switch to Java 8 for building ==
echo "Switching to Java 8 for build..."
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH

# === Step 5: Build graphchi benchmark ===
cd /home/hpeng/E2COOL/benchmark_dacapo/benchmarks/
echo "Building DaCapo benchmark"
ant graphchi

# === Step 6: Switch to Java 11 for running ===
echo "Switching to Java 11 for benchmark run..."
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH

# === Step 7: Run the graphchi benchmark ===
echo "Running DaCapo graphchi benchmark..."
if [ -f dacapo-evaluation-git-4e3de06d-dirty.jar ]; then
    java -jar dacapo-evaluation-git-4e3de06d-dirty.jar --no-validation graphchi
else
    java -jar dacapo-evaluation-git-4e3de06d.jar --no-validation graphchi
fi
