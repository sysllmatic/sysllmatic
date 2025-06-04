include ../../.env
# sudo apt update
# sudo apt install openjdk-17-jdk
# sudo update-alternatives --config java
# sudo update-alternatives --config javac

JAVAC = javac
JAVA = java
JFLAGS = -d . 

SRCS = *.java
SORBENCHMARK_CLASS = jnt/scimark2/SORBenchmark

MAIN_CLASS = jnt/scimark2/SOR
OPTIMIZED_CLASS = jnt.scimark2.SOROptimized

compile:
	rm -rf *.class
	rm -rf jnt/
	$(JAVAC) $(JFLAGS) $(SRCS) ../Random.java ../Stopwatch.java

run:
	@$(JAVA) $(MAIN_CLASS)

run_optimized:
	@$(JAVA) $(OPTIMIZED_CLASS)

measure:
	sudo modprobe msr
	sudo ${USER_PREFIX}/MEASURE/main "$(JAVA) $(MAIN_CLASS)" java SOR
	sudo chmod -R 777 ${USER_PREFIX}/src/runtime_logs/java.csv

measure_optimized:
	sudo modprobe msr
	sudo ${USER_PREFIX}/MEASURE/main "$(JAVA) $(OPTIMIZED_CLASS)" java SOROptimized
	sudo chmod -R 777 ${USER_PREFIX}/src/runtime_logs/java.csv

measure_mflops:
	@$(JAVA) $(SORBENCHMARK_CLASS) false

measure_mflops_optimized:
	@$(JAVA) $(SORBENCHMARK_CLASS) true