#!/bin/bash
set -e  # Exit on error

# === Step 1: Remove old tar and checksum file ===
echo "Removing old checksum file..."
rm -f /home/hpeng/E2COOL/benchmark_dacapo/benchmarks/bms/pmd/downloads/pmd-src-6.55.0.tar.gz.MD5
echo "Removing old tar file..."
rm -f /home/hpeng/E2COOL/benchmark_dacapo/benchmarks/bms/pmd/downloads/pmd-src-6.55.0.tar.gz

# === Step 2: Compress updated source ===
echo "Compressing updated pmd source..."
cd /home/hpeng/E2COOL/benchmark_dacapo/benchmarks/bms/pmd/build/
tar -czvf pmd-src-6.55.0.tar.gz *
# Move the tar.gz to downloads/
mv pmd-src-6.55.0.tar.gz ../downloads/

# === Step 3: Clean old pmd build directory ===
echo "Cleaning old build directory..."
if [ -d /home/hpeng/E2COOL/benchmark_dacapo/benchmarks/bms/pmd/build/ ]; then
    sudo rm -rf /home/hpeng/E2COOL/benchmark_dacapo/benchmarks/bms/pmd/build/
fi

# === Step 4: Switch to Java 8 for building ===
echo "Switching to Java 8 for build..."
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH

# === Step 5: Build pmd benchmark ===
cd /home/hpeng/E2COOL/benchmark_dacapo/benchmarks/
echo "Building DaCapo benchmark"
ant pmd

# === Step 6: Switch to Java 11 for running ===
echo "Switching to Java 11 for benchmark run..."
export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
export PATH=$JAVA_HOME/bin:$PATH

# === Step 7: Run the pmd benchmark ===
echo "Running DaCapo pmd benchmark..."
if [ -f dacapo-evaluation-git-4e3de06d-dirty.jar ]; then
    java -jar dacapo-evaluation-git-4e3de06d-dirty.jar --no-validation pmd
else
    java -jar dacapo-evaluation-git-4e3de06d.jar --no-validation pmd
fi
