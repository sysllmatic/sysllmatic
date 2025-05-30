package jnt.scimark2;

import java.util.concurrent.ThreadLocalRandom;

public class MonteCarloOptimized {
    public static void main(String[] args) {
        long cycles = 1073741824;
        double result = integrate(cycles);
        System.out.println(result);
    } 

    public static double integrate(long numSamples) {
        long underCurve = 0;
        final int batchSize = 4; 
        double x, y;
        for (long count = 0; count < numSamples; count += batchSize) {
            for (int i = 0; i < batchSize && count + i < numSamples; i++) {
                x = ThreadLocalRandom.current().nextDouble();
                y = ThreadLocalRandom.current().nextDouble();
                if (x * x + y * y <= 1.0) underCurve++;
            }
        }

        return ((double) underCurve / numSamples) * 4.0;
    }
}