package jnt.scimark2;

import java.util.Random;

public class SparseCompRowOptimized {
    // Sparse matrix-vector multiply using compressed row storage.
    public static void matmult(double[] y, double[] val, int[] row,
                               int[] col, double[] x, long NUM_ITERATIONS) {
        int M = row.length - 1;
        for (long reps = 0; reps < NUM_ITERATIONS; reps++) {
            for (int r = 0; r < M; r++) {
                double sum = 0.0;
                int rowStart = row[r];
                int rowEnd = row[r + 1];
                for (int i = rowStart; i < rowEnd; i++) {
                    sum += x[col[i]] * val[i];
                }
                y[r] = sum;
            }
        }
    }

    // Helper method to generate a random vector.
    private static double[] randomVector(int N, Random R) {
        double[] A = new double[N];
        for (int i = 0; i < N; i++) {
            A[i] = R.nextDouble();
        }
        return A;
    }

    // Computes the sum of absolute differences between two vectors.
    private static double normabs(double[] a, double[] b) {
        double sum = 0.0;
        for (int i = 0; i < a.length; i++) {
            sum += Math.abs(a[i] - b[i]);
        }
        return sum;
    }

    public static void main(String[] args) {
        // Parameters for the test.
        int N = 1000;              // Size of the vector / number of rows.
        int nz = 10000;            // Total number of nonzeros in the matrix.
        long cycles = 524288;      // Fixed cycles
        double regressionThreshold = 1.0e-10;
        long seed = 101010;        

        // Create random number generators.
        Random rand1 = new Random(seed);
        Random rand2 = new Random(seed + 1);

        // Generate vector x.
        double[] x = randomVector(N, rand1);

        // Build the sparse matrix in compressed row format.
        int nr = nz / N;       // Average nonzeros per row.
        int anz = nr * N;      // Actual number of nonzeros.
        double[] val = randomVector(anz, rand2);
        int[] col = new int[anz];
        int[] row = new int[N + 1];
        row[0] = 0;
        for (int r = 0; r < N; r++) {
            int rowr = row[r];
            row[r + 1] = rowr + nr;
            int step = r / nr;
            if (step < 1) step = 1;
            for (int i = 0; i < nr; i++) {
                col[rowr + i] = i * step;
            }
        }

        // Prepare output arrays.
        double[] yTest = new double[N];
        double[] yRef = new double[N];

        // Run the multiplication with a fixed number of cycles (simulate optimized run).
        matmult(yTest, val, row, col, x, cycles);

        // Run the multiplication with 1 iteration (reference run).
        matmult(yRef, val, row, col, x, 1);

        // Compare the two results.
        double difference = normabs(yTest, yRef);

        System.out.println(difference);
    }
}