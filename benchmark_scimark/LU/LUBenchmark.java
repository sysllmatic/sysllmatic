package jnt.scimark2;

public class LUBenchmark {
    public static void main(String[] args) {
        double min_time = 2.0; // Given constant
        Random R = new Random(101010); // Given constant
        int LU_size = 1000; // Given constant
        Boolean optimized = args.length > 0 && Boolean.parseBoolean(args[0]);
        double result = Kernel.measureLU(LU_size, min_time, R, optimized);
        System.out.printf("%.2f%n", result);
    }
}
