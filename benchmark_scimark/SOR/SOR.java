package jnt.scimark2;

import java.util.Random;

public class SOR {
    // Executes the Successive Over-Relaxation (SOR) algorithm.
    public static void execute(double omega, double[][] G, long num_iterations) {
        int M = G.length;
        int N = G[0].length;

        double omega_over_four = omega * 0.25;
        double one_minus_omega = 1.0 - omega;

        // Update interior points for each iteration.
        int Mm1 = M - 1;
        int Nm1 = N - 1;
        for (long p = 0; p < num_iterations; p++) {
            for (int i = 1; i < Mm1; i++) {
                double[] Gi = G[i];
                double[] Gim1 = G[i - 1];
                double[] Gip1 = G[i + 1];
                for (int j = 1; j < Nm1; j++) {
                    Gi[j] = omega_over_four * (Gim1[j] + Gip1[j] + Gi[j - 1] + Gi[j + 1])
                            + one_minus_omega * Gi[j];
                }
            }
        }
    }

    // Helper method to generate a random matrix with dimensions M x N.
    private static double[][] randomMatrix(int M, int N) {
        double[][] A = new double[M][N];
        Random R = new Random(101010);
        for (int i = 0; i < M; i++) {
            for (int j = 0; j < N; j++) {
                A[i][j] = R.nextDouble();
            }
        }
        return A;
    }


    private static double normabs(double[] x, double[] y) {
        int N = x.length;
        double sum = 0.0;

        for (int i = 0; i < N; i++)
            sum += Math.abs(x[i] - y[i]);

        return sum;
    }

    /**
    * Main method, do not change.
    */
    public static void main(String[] args) {
        final int SOR_SIZE = 100;      
        final long cycles = 65536;      // Fixed number of iterations.
        double omega = 1.25;            // Relaxation factor

        // Create a random matrix of dimensions SOR_SIZE x SOR_SIZE.
        double[][] G = randomMatrix(SOR_SIZE, SOR_SIZE);

        // Execute the SOR algorithm.
        execute(omega, G, cycles);

        // Compute the error between the two matrices (should be 0.0 for a matrix of random values)
        double[][] G_baseline = randomMatrix(SOR_SIZE, SOR_SIZE);
        double error = 0.0;
        for (int i = 0; i < SOR_SIZE; i++) {
            error += normabs(G[i], G_baseline[i]);
        }

        // Print the error result
        System.out.println(error * 1.0e-6);
    }
}


