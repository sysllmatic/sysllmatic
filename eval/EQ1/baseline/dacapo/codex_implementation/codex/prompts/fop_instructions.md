# fop-Specific Build and Validation Instructions

1. **Set the Java toolchain to JDK 8 before building anything:**
   ```bash
   export JAVA_HOME=/usr/lib/jvm/java-1.8.0-openjdk-amd64
   export PATH="$JAVA_HOME/bin:$PATH"
   ```
   Verify `java -version` and `javac -version` report 1.8 before proceeding.

2. **Top-level build (from `benchmarks/`):**
   ```bash
   ant fop
   ```
   This compiles the fop benchmark and prepares its distributables.

3. **Switch to Java 11 for running:**
   ```bash
   export JAVA_HOME=/usr/lib/jvm/java-11-openjdk-amd64
   export PATH=$JAVA_HOME/bin:$PATH
   ```
   Verify `java -version` and `javac -version` report 11 before proceeding.

4. **Benchmark run command (from `benchmarks/`):**
   ```bash
   java -jar dacapo-evaluation-git-4e3de06d.jar --no-validation fop
   ```
   Use this to exercise the optimized changes quickly. You may add `-t/ -s` knobs if needed, but keep `--no-validation` to avoid the known LOG4J2 warning.

5. **Per-application source build/tests (from `benchmarks/bms/fop/build`):**
   - Clean + compile:
     ```bash
     mvn -q clean
     mvn -q compile
     ```
   - Targeted correctness tests:
     ```bash
     mvn test -Dtest=$TEST
     ```
     Replace `$TEST` with the suite or class you want to run.

Ensure each command succeeds before moving to later phases; capture logs for failures so you can diagnose and fix them.
