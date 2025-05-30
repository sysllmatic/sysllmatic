package jnt.scimark2;

public class SparseCompRowBenchmark {
    public static void main(String[] args) {
        int N = 1000; // Given constant
        int nz = 5000; // Givent constant
        double mintime = 2.0; // Given constant
        Random R = new Random(101010);
        Boolean optimized = args.length > 0 && Boolean.parseBoolean(args[0]);
        double result = Kernel.measureSparseMatmult(N, nz, mintime, R, optimized);
        System.out.printf("%.2f%n", result);
    }
}