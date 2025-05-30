package jnt.scimark2;

public class Kernel {
    public static double measureMonteCarlo(double min_time, Random R, boolean optimized) {
        Stopwatch Q = new Stopwatch();

        long cycles = 1;
        while (true) {
            Q.start();
            if (optimized){
                MonteCarloOptimized.integrate(cycles);
            } else {
                MonteCarlo.integrate(cycles);
            }
            Q.stop();
            if (Q.read() >= min_time) break;

            cycles *= 2;
        }
        // approx Mflops

        return ((double) cycles) * 4.0 / Q.read() * 1.0e-6;
    }
}
