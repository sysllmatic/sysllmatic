package jnt.scimark2;
import java.io.*;

import jnt.scimark2.FFTOptimized;

public class Kernel {
    private static double[] x;

    public static double measureFFT(int N, double mintime, boolean optimized, Random R) {
        // initialize FFT data as complex (N real/img pairs)
        double[] x = RandomVector(2 * N, R);
        double[] oldx = NewVectorCopy(x);
        long cycles = 1;
        Stopwatch Q = new Stopwatch();

        while (true) {
            Q.start();
            for (int i = 0; i < cycles; i++) {
                if (optimized){
                    FFTOptimized.transform(x);    // forward transform
                    FFTOptimized.inverse(x);        // backward transform
                } else {
                    FFT.transform(x);    // forward transform
                    FFT.inverse(x);        // backward transform
                }
            }
            Q.stop();
            if (Q.read() >= mintime)
                break;

            cycles *= 2;
        }
        // approx Mflops

        return num_flops(N) * cycles / Q.read() * 1.0e-6;
    }

    private static double[] NewVectorCopy(double[] x) {
        int N = x.length;

        double[] y = new double[N];
        System.arraycopy(x, 0, y, 0, N);

        return y;
    }

    public static double num_flops(int N) {
        double logN = log2(N);

        return (5.0 * (double) N - 2) * logN + 2 * ((double) N + 1);
    }

     protected static int log2(int n) {
        int log = 0;
        for (int k = 1; k < n; k *= 2, log++) ;
        if (n != (1 << log))
            throw new Error("FFT: Data length is not a power of 2!: " + n);
        return log;
    }

    private static double[] RandomVector(int N, Random R) {
        double[] A = new double[N];

        for (int i = 0; i < N; i++)
            A[i] = R.nextDouble();
        return A;
    }
}
