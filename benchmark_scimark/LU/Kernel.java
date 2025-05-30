package jnt.scimark2;

public class Kernel {
    // each measurement returns approx Mflops

    public static double measureLU(int N, double min_time, Random R, boolean optimized) {
        // compute approx Mlfops, or O if LU yields large errors

        double[][] A = RandomMatrix(N, N, R);
        double[][] lu = new double[N][N];
        int[] pivot = new int[N];

        Stopwatch Q = new Stopwatch();

        long cycles = 1;
        while (true) {
            Q.start();
            for (int i = 0; i < cycles; i++) {
                CopyMatrix(lu, A);
                if (optimized) {
                    LUOptimized.factor(lu, pivot);
                } else {
                    LU.factor(lu, pivot);
                }
            }
            Q.stop();
            if (Q.read() >= min_time) break;

            cycles *= 2;
        }

        return num_flops(N) * cycles / Q.read() * 1.0e-6;
    }

    private static double num_flops(int N) {
        // rougly 2/3*N^3
        return (2.0 * (double) N * (double) N * (double) N / 3.0);
    }

    private static void CopyMatrix(double[][] B, double[][] A) {
        int M = A.length;
        int N = A[0].length;

        int remainder = N & 3;         // N mod 4;

        for (int i = 0; i < M; i++) {
            double[] Bi = B[i];
            double[] Ai = A[i];
            System.arraycopy(Ai, 0, Bi, 0, remainder);
            for (int j = remainder; j < N; j += 4) {
                Bi[j] = Ai[j];
                Bi[j + 1] = Ai[j + 1];
                Bi[j + 2] = Ai[j + 2];
                Bi[j + 3] = Ai[j + 3];
            }
        }
    }

    private static double[][] RandomMatrix(int M, int N, Random R) {
        double[][] A = new double[M][N];

        for (int i = 0; i < N; i++)
            for (int j = 0; j < N; j++)
                A[i][j] = R.nextDouble();
        return A;
    }
}
