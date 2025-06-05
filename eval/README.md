# Evaluation Methodology

This section describes the evaluation methodology used in our paper, which includes both **qualitative** and **quantitative** components. The quantitative evaluation is structured around four core **Evaluation Questions (EQ1–EQ4)** and focuses on improvements across various performance metrics.

## Quantitative Evaluation

We evaluate the effectiveness of our approach using two primary quantitative metrics across multiple performance dimensions (latency, energy, throughput, memory, CPU cycles):

### 1. Relative Improvement (`x`)

- **Definition**: This measures the ratio of the performance metric *before* and *after* optimization.
- **Computation**:
  - For most metrics (e.g., latency, energy):  
    `Relative Improvement = Before / After`
  - For **throughput**, since higher is better:  
    `Relative Improvement = After / Before`
- **Interpretation**:
  - A value of `1x` indicates no change.
  - Values greater than `1x` indicate performance improvement.
- **Correctness Requirement**: Only **correct** programs (i.e., those that pass all test cases) are included in this calculation.

### 2. %Optimized (`%opt`)

- **Definition**: The percentage of programs that are both **correct** and demonstrate a **minimum of 10% improvement** in a given metric.
- **Formula**:  
  `%opt = (# of Correct Programs Improved ≥10%) / (Total # of Programs) * 100`

## Qualitative Evaluation

In addition to the numerical analysis, we perform a qualitative analysis to examine:
- The types of optimizations applied
- Examples of optimizations performed
- Line of code difference after optimization
