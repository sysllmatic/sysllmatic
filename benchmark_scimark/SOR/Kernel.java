package jnt.scimark2;

public class Kernel {
    public static double measureSOR(int N, double min_time, Random R, boolean optimized) {
        double[][] G = RandomMatrix(N, N, R);

        Stopwatch Q = new Stopwatch();
        long cycles = 1;
        while (true) {
            Q.start();
            if (optimized) {
                SOROptimized.execute(1.25, G, cycles);
            } else {
                SOR.execute(1.25, G, cycles);
            }
            Q.stop();
            if (Q.read() >= min_time) break;

            cycles *= 2;
        }
        // approx Mflops
        return ((double) N - 1) * ((double) N - 1) * (double) cycles * 6.0 / Q.read() * 1.0e-6;
    }

    private static double[][] RandomMatrix(int M, int N, Random R) {
        double[][] A = new double[M][N];

        for (int i = 0; i < N; i++)
            for (int j = 0; j < N; j++)
                A[i][j] = R.nextDouble();
        return A;
    }
}
