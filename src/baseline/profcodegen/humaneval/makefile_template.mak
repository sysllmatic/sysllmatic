# include ../../.env

compile:
	/usr/bin/g++ -g -c -pipe -fomit-frame-pointer -march=native  -std=c++11 -fopenmp ${FILE_NAME}.cpp -o ${FILE_NAME}.cpp.o
	/usr/bin/g++ -g ${FILE_NAME}.cpp.o -o ${FILE_NAME}.gpp_run -fopenmp -lssl -lcrypto

compile_optimized:
	/usr/bin/g++ -g -c -pipe -fomit-frame-pointer -march=native  -std=c++11 -fopenmp optimized_${FILE_NAME}.cpp -o optimized_${FILE_NAME}.cpp.o
	/usr/bin/g++ -g optimized_${FILE_NAME}.cpp.o -o optimized_${FILE_NAME}.gpp_run -fopenmp -lssl -lcrypto

measure:
	sudo modprobe msr
	sudo ${USER_PREFIX}/RAPL/main "${USER_PREFIX}/src/baseline/profcodegen/humaneval/${FILE_NAME}/${FILE_NAME}.gpp_run" c++ ${FILE_NAME}
	sudo chmod -R 777 ${USER_PREFIX}/src/runtime_logs/c++.csv

measure_optimized:
	sudo modprobe msr
	sudo ${USER_PREFIX}/RAPL/main "${USER_PREFIX}/src/baseline/profcodegen/humaneval/${FILE_NAME}/optimized_${FILE_NAME}.gpp_run" c++ optimized_${FILE_NAME}
	sudo chmod -R 777 ${USER_PREFIX}/src/runtime_logs/c++.csv

run:
	./${FILE_NAME}.gpp_run

run_optimized:
	./optimized_${FILE_NAME}.gpp_run