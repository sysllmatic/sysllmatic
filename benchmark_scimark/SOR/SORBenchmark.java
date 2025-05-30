package jnt.scimark2;

public class SORBenchmark {
    public static void main(String[] args) {
        // Define matrix size and number of iterations
        int N = 100;
        double mintime = 2.0;
        Random R = new Random(101010);
        Boolean optimized = args.length > 0 && Boolean.parseBoolean(args[0]);
        // Print the benchmark result
        double result = Kernel.measureSOR(N, mintime, R, optimized);
        System.out.printf("%.2f%n", result);
    }
}