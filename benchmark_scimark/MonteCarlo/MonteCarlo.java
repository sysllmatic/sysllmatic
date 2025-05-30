package jnt.scimark2;

public class MonteCarlo {
    final static int SEED = 113;

    public static void main(String[] args) {
        int cycles = 1073741824;
        double result = integrate(cycles);
        System.out.println(result);
    } 

    public static double integrate(long Num_samples) {

        Random R = new Random(SEED);
        long under_curve = 0;
        for (long count = 0; count < Num_samples; count++) {
            double x = R.nextDouble();
            double y = R.nextDouble();

            if (x * x + y * y <= 1.0)
                under_curve++;
        }

        return ((double) under_curve / Num_samples) * 4.0;
    }
}
