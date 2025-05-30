# include ../../.env

compile:
	/usr/bin/g++ -g -c -pipe -fomit-frame-pointer -march=native  -std=c++11 -fopenmp ${FILE_NAME}.cpp -o ${FILE_NAME}.cpp.o
	/usr/bin/g++ -g ${FILE_NAME}.cpp.o -o ${FILE_NAME}.gpp_run -fopenmp 

compile_optimized:
	/usr/bin/g++ -g -c -pipe -fomit-frame-pointer -march=native  -std=c++11 -fopenmp optimized_${FILE_NAME}.cpp -o optimized_${FILE_NAME}.cpp.o
	/usr/bin/g++ -g optimized_${FILE_NAME}.cpp.o -o optimized_${FILE_NAME}.gpp_run -fopenmp 

measure:
	sudo modprobe msr
	sudo ${USER_PREFIX}/RAPL/main "${USER_PREFIX}/benchmark_human_eval/${FILE_NAME}/stress_${FILE_NAME}.gpp_run" c++ stress_${FILE_NAME}
	sudo chmod -R 777 ${USER_PREFIX}/src/runtime_logs/c++.csv

compile_stress:
	/usr/bin/g++ -g -c -pipe -fomit-frame-pointer -march=native  -std=c++11 -fopenmp stress_${FILE_NAME}.cpp -o stress_${FILE_NAME}.cpp.o
	/usr/bin/g++ -g stress_${FILE_NAME}.cpp.o -o stress_${FILE_NAME}.gpp_run -fopenmp

measure_optimized:
	sudo modprobe msr
	sudo ${USER_PREFIX}/RAPL/main "${USER_PREFIX}/benchmark_human_eval/${FILE_NAME}/stress_optimized_${FILE_NAME}.gpp_run" c++ stress_optimized_${FILE_NAME}
	sudo chmod -R 777 ${USER_PREFIX}/src/runtime_logs/c++.csv

compile_stress_optimized:
	/usr/bin/g++ -g -c -pipe -fomit-frame-pointer -march=native  -std=c++11 -fopenmp stress_optimized_${FILE_NAME}.cpp -o stress_optimized_${FILE_NAME}.cpp.o
	/usr/bin/g++ -g stress_optimized_${FILE_NAME}.cpp.o -o stress_optimized_${FILE_NAME}.gpp_run -fopenmp

run:
	./${FILE_NAME}.gpp_run

run_optimized:
	./optimized_${FILE_NAME}.gpp_run

generate_flame_report:
	sudo perf record -F 90000 -e cycles:u -g --call-graph dwarf -o data -- ./flamegraph_${FILE_NAME}.gpp_run
	sudo perf report -i data -f -n --stdio --sort overhead > flame_report.txt

compile_code_for_flame_report:
	/usr/bin/g++ -g -c -pipe -fomit-frame-pointer -march=native  -std=c++11 -fopenmp flamegraph_${FILE_NAME}.cpp -o flamegraph_${FILE_NAME}.cpp.o
	/usr/bin/g++ -g flamegraph_${FILE_NAME}.cpp.o -o flamegraph_${FILE_NAME}.gpp_run -fopenmp  