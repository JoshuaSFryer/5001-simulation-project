import math
import matplotlib.pyplot as plt
import numpy as np


def generate_exp(L, generator):
    R = generator.random()
    return cdf_exponential_inverse(L, R)


def cdf_exponential(L, X):
    return 1 - math.e ** (-L * X)


def cdf_exponential_inverse(L, R):
    return -math.log(1-R) / L


def exponential_test():
    """
    Generate a plot of several histograms illustrating some sample distributions
    generated by the method.
    """
    test_lambdas = [0.01, 0.5, 1, 2]
    num_samples = 10000
    num_bins = round(num_samples**0.5)
    sample_runs = list()

    for L in test_lambdas:
        samples = list()
        for _ in range(num_samples):
            samples.append(generate_exp(L))
        sample_runs.append(samples)
        

    # Plot

    fig = plt.gcf()
    fig.suptitle(f'Generated Exponential Distributions, n={num_samples}')

    for i, samples in enumerate(sample_runs):
        plt.subplot(2,2,i+1)
        plt.hist(sample_runs[i], num_bins)
        plt.title(f'Lambda = {test_lambdas[i]}')

    plt.tight_layout()
    plt.savefig('sample_dist.png')
        


if __name__ == '__main__':
    exponential_test()
