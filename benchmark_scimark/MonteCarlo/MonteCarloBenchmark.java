package jnt.scimark2;

public class MonteCarloBenchmark {
    public static void main(String[] args) {
        double mintime = 2.0; // Given constant
        Random R = new Random(101010);
        Boolean optimized = args.length > 0 && Boolean.parseBoolean(args[0]);
        double result = Kernel.measureMonteCarlo(mintime, R, optimized);
        System.out.printf("%.2f%n", result);
    }
}