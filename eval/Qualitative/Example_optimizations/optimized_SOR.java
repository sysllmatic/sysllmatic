package jnt.scimark2;

import java.util.Random;

public class SOROptimized {
    
    public static void execute(double omega, double[][] G, long num_iterations) {
        int M = G.length;
        int N = G[0].length;

        double omega_over_four = omega * 0.25;
        double one_minus_omega = 1.0 - omega;

        
        int Mm1 = M - 1;
        int Nm1 = N - 1;
        for (long p = 0; p < num_iterations; p++) {
            for (int i = 1; i < Mm1; i++) {
                double[] Gi = G[i];
                double[] Gim1 = G[i - 1];
                double[] Gip1 = G[i + 1];
                int j;
                for (j = 1; j < Nm1 - 1; j += 2) { 
                    double newValue1 = omega_over_four * (Gim1[j] + Gip1[j] + Gi[j - 1] + Gi[j + 1])
                            + one_minus_omega * Gi[j];
                    double newValue2 = omega_over_four * (Gim1[j + 1] + Gip1[j + 1] + Gi[j] + Gi[j + 2])
                            + one_minus_omega * Gi[j + 1];
                    Gi[j] = newValue1;
                    Gi[j + 1] = newValue2;
                }
                
                if (j < Nm1) {
                    Gi[j] = omega_over_four * (Gim1[j] + Gip1[j] + Gi[j - 1] + Gi[j + 1])
                            + one_minus_omega * Gi[j];
                }
            }
        }
    }

    
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

    
    public static void main(String[] args) {
        final int SOR_SIZE = 100;      
        final long cycles = 65536;      
        double omega = 1.25;            

        
        double[][] G = randomMatrix(SOR_SIZE, SOR_SIZE);

        
        execute(omega, G, cycles);

        
        double[][] G_baseline = randomMatrix(SOR_SIZE, SOR_SIZE);
        double error = 0.0;
        for (int i = 0; i < SOR_SIZE; i++) {
            error += normabs(G[i], G_baseline[i]);
        }

        
        System.out.println(error * 1.0e-6);
    }
}
