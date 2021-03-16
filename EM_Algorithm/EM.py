
from matplotlib import rcParams
rcParams["font.family"] = "sans-serif"
rcParams["font.sans-serif"] = ["Arial"]
# import matplotlib
# matplotlib.rc('font', family='sans-serif')
# matplotlib.rc('font', serif='Arial')
# matplotlib.rc('text', usetex='false')
# matplotlib.rcParams.update({'font.size': 18})
from basic.binning import binning
import numpy as np
import matplotlib.pyplot as plt
import math
from sklearn.cluster import KMeans

### data: (n,1)-array
class EM:
    def __init__(self, data):
        self.data = data

    def GMM(self, n_components, tolerance=10e-5):
        """EM algorithm with pdf=Gaussian (GMM)
        Parameters
        ----------
        n_components : int
            Number of components.
        tolerance : float
            Convergence criteria
        data : array (n_samples,1)
        Returns
        -------

        """
        ## (f,m,s) are growing array
        data = self.data
        ##  initialize EM parameters
        f, m, s, loop, improvement = self.init_GMM(n_components=n_components)
        while (loop < 100 or improvement > tolerance) and loop < 5000:
            # prior_prob = self.__weighting(f, m, s)
            prior_prob = self.__weighting(f, m, s, function=oneD_gaussian)
            f, m, s = self.__update_f_m_s(prior_prob, f, m, s)
            improvement = self.__cal_improvement(f, m, s)
            loop += 1
        f, m, s = self.__reshape_all(f, m, s, n_rows=loop+1, n_cols=n_components)
        self.f = f
        self.m = m
        self.s = s
        labels, data_cluster, ln_likelihood = self.predict(data)
        return f, m, s, labels, data_cluster

    def PEM(self, n_components, tolerance=10e-5):
        data = self.data
        f, tau, s, loop, improvement = self.init_PEM(n_components=n_components)
        while (loop < 10 or improvement > tolerance) and loop < 5000:
            prior_prob = self.__weighting(f, tau, function=exp_pdf)
            f, tau, s = self.__update_f_m_s(prior_prob, f, tau, s)
            improvement = self.__cal_improvement(f, tau)
            loop += 1
        f, tau, s = self.__reshape_all(f, tau, s, n_rows=loop+1, n_cols=n_components)
        self.f = f
        self.m = tau
        self.s = s
        labels, data_cluster, ln_likelihood = self.predict(data)
        return f, tau, s, labels, data_cluster

    ##  initialize parameters
    def init_PEM(self, n_components):
        data = self.data
        self.n_components = n_components
        mean = np.mean(data)
        std = np.std(data, ddof=1)
        f = np.ones(n_components) / n_components
        tau = np.linspace(abs(mean - 0.5 * std), mean + 0.5 * std, n_components)
        s = tau.copy()
        loop = 0
        improvement = 10
        return f, tau, s, loop, improvement

    def plot_EM_results(self):
        f = self.f
        m = self.m
        s = self.s
        fig, axs = plt.subplots(3, sharex=True)
        axs[-1].set_xlabel('iteration', fontsize=15)
        self.__plot_EM_result(m, axs[0], ylabel='mean')
        self.__plot_EM_result(s, axs[1], ylabel='std')
        self.__plot_EM_result(f, axs[2], ylabel='fraction')

    def plot_fit_exp(self):
        data = self.data
        f = self.f[-1,:]
        m = self.m[-1,:]
        s = self.s[-1,:]
        n_components = self.n_components
        n_sample = len(data)

        bin_width = (12/n_sample)**(1/3)*np.mean(data)/n_components**1.3 ## scott's formula for poisson process
        # bin_width = (12/n_sample)**(1/3)*np.mean(data) ## scott's formula for poisson process
        bin_number = int((max(data)-min(data))/bin_width)
        pd, center = binning(data, bin_number)  # plot histogram
        data_std_new = np.std(data, ddof=1)
        x = np.arange(0.01, max(data) + data_std_new, 0.01)
        y_fit = exp_pdf(x, args=[f, m])
        for i in range(n_components):
            plt.plot(x, y_fit[i, :], '-')
        plt.plot(x, sum(y_fit), '-')
        plt.xlabel('dwell time (s)', fontsize=15)
        plt.ylabel('probability density (1/$\mathregular{s^2}$)', fontsize=15)
        plt.xlim([0, np.mean(data)+data_std_new])

    ##  plot data histogram and its gaussian EM (GMM) results
    def plot_fit_gauss(self):
        data = self.data
        f = self.f[-1,:]
        m = self.m[-1,:]
        s = self.s[-1,:]
        n_components = self.n_components

        bin_number = np.log2(len(data)).astype('int') + 3
        pd, center = binning(data, bin_number)  # plot histogram
        data_std_new = np.std(data, ddof=1)
        x = np.arange(0, max(data) + data_std_new, 0.05)
        y_fit = oneD_gaussian(x, args=[f, m, s])
        for i in range(n_components):
            plt.plot(x, y_fit[i, :], '-')
        plt.plot(x, sum(y_fit), '-')
        plt.xlabel('step size (nm)', fontsize=15)
        plt.ylabel('probability density (1/$\mathregular{nm^2}$)', fontsize=15)

    ##  get predicted data_cluster and its log-likelihood
    def predict(self, data):
        f = self.f[-1,:]
        m = self.m[-1, :]
        s = self.s[-1, :]
        n_components = self.n_components
        prior_prob = self.prior_prob
        labels = np.array([np.argmax(prior_prob[:, i]) for i in range(len(data))])  ## find max of prob
        data_cluster = [data[labels == i] for i in range(n_components)]
        ln_likelihood = sum([sum(log_oneD_gaussian(data, args=[f, m, s])[i]) for i, data in enumerate(data_cluster)])
        self.ln_likelihood = ln_likelihood
        return labels, data_cluster, ln_likelihood

    def AIC(self):
        ln_likelihood = self.ln_likelihood
        n_components = self.n_components
        AIC = -2 * ln_likelihood + (n_components * 3 - 1) * 2
        return AIC

    def BIC(self):
        n_samples = len(self.data)
        ln_likelihood = self.ln_likelihood
        n_components = self.n_components
        BIC = -2 * ln_likelihood + (n_components * 3 - 1) * np.log(n_samples)
        return BIC

    ##  initialize mean, std and fraction of gaussian
    def init_GMM(self, n_components):
        self.n_components = n_components
        data = self.data.reshape((-1, 1))
        f, m, s = self.__get_f_m_s_kmeans(data)
        loop = 0
        improvement = 10
        return f, m, s, loop, improvement

    def __get_f_m_s_kmeans(self, data):
        n_sample = len(data)
        n_components = self.n_components
        labels = KMeans(n_clusters=n_components).fit(data).labels_
        data_cluster = [data[labels == i] for i in range(n_components)]
        m = np.array([np.mean(data) for data in data_cluster])
        index = np.argsort(m)
        f = np.array([len(data) / n_sample for data in data_cluster])[index]
        m = m[index]
        s = np.array([np.std(data, ddof=1) for data in data_cluster])[index]
        self.f_i = f
        self.m_i = m
        self.s_i = s
        return f, m, s

    ##  calculate the probability belonging to each cluster, (m,s)
    def __weighting(self, *args, function):
        """Calculate prior probability of each data point
        Parameters
        ----------
        f, m, s : growing array, (n,)
            fractions, mean, std
        n_components : int
            Number of components.
        Returns
        -------
        prior_prob : array, (n_components, n_samples)

        """
        data = self.data
        n_components = self.n_components
        para = []
        for arg in args:
            para += [arg[-n_components:]]
        p = function(data, args=para) ##(n_components, n_samples)
        prior_prob = p / sum(p)
        self.p = p
        self.prior_prob = prior_prob
        return prior_prob

    # ##  calculate the probability belonging to each cluster, (m,s)
    # def __weighting(self, f, m, s):
    #     """Calculate prior probability of each data point
    #     Parameters
    #     ----------
    #     f, m, s : growing array, (n,)
    #         fractions, mean, std
    #     n_components : int
    #         Number of components.
    #     Returns
    #     -------
    #     prior_prob : array, (n_components, n_samples)
    #
    #     """
    #     data = self.data
    #     n_components = self.n_components
    #     f = f[-n_components:]
    #     m = m[-n_components:]
    #     s = s[-n_components:]
    #     p = oneD_gaussian(data, args=[f, m, s]) ##(n_components, n_samples)
    #     prior_prob = p / sum(p)
    #     self.p = p
    #     self.prior_prob = prior_prob
    #     return prior_prob

    ##  update mean, std and fraction using matrix multiplication, (n_feture, n_sample) * (n_sample, 1) = (n_feture, 1)
    def __update_f_m_s(self, prior_prob, f, m, s):
        data = self.data
        n_sample = len(data)
        f_new = np.sum(prior_prob, axis=1) / n_sample
        m_new = np.matmul(prior_prob, data).ravel() / np.sum(prior_prob, axis=1)
        s_new = np.sqrt( np.matmul(prior_prob, data ** 2).ravel()/np.sum(prior_prob, axis=1) - m_new**2 )
        f, m, s = self.__append_arrays([f,f_new], [m,m_new], [s,s_new])
        self.f = f
        self.m = m
        self.s = s
        return f, m, s

    def __append_arrays(self, *args):
        arrays = []
        for arg in args:
            arrays += [np.append(arg[0], arg[1])]
        return arrays

    ##  calculate max improvement among all parameters
    def __cal_improvement(self, *args):
        ##  arg: [f, m, s], not reshaped array
        """Calculate prior probability of each data point
                Parameters
                ----------
                f, m, s : growing array, (n,)
                    fractions, mean, std
                Returns
                -------
                prior_prob : array, (n_components, n_samples)

        """
        n_components = self.n_components
        improvement = []
        for arg in args:
            # arg = np.array(arg)
            arg_old = arg[-2*n_components:-n_components] ##  last 2n to last n
            arg_new = arg[-n_components:]
            diff = abs(arg_new - arg_old)
            improvement = max(np.append(improvement, diff)) ## take max of all args diff
        return improvement

    ##  reshape all arrays to (loop,n_components)
    def __reshape_all(self, *args, n_rows, n_cols):
        results = []
        for arg in args:
            results += [np.reshape(arg, (n_rows, n_cols))]
        return results

    def __plot_EM_result(self, result, ax, xlabel='iteration', ylabel='value'):
        n_feature = result.shape[1]
        iteration = result.shape[0]
        for i in range(n_feature):
            ax.plot(np.arange(0, iteration), result[:, i], '-o')
        ax.set_ylabel(f'{ylabel}', fontsize=15)





##  args: list of parameters, x: np array
def oneD_gaussian(x, args):
    # x: (n,)
    # args: (k), args[0,1,2...,k-1]: (m)
    # output: (k,n)
    f = np.array(args[0])
    xm = np.array(args[1])
    s = np.array(args[2])
    y = []
    for f, xm, s in zip(f, xm, s):
        if s <= 0:
            s = 0.01
        y += [f*1/s/np.sqrt(2*math.pi)*np.exp(-(x-xm)**2/2/s**2)]
    y = np.array(y)
    return y.reshape(y.shape[0], y.shape[1])

def log_oneD_gaussian(x, args):
    f = np.array(args[0])
    xm = np.array(args[1])
    s = np.array(args[2])
    lny = []
    for f, xm, s in zip(f, xm, s):
        if s <= 0:
            s = 0.01
        lny += [np.log(f) - np.log(s*np.sqrt(2*math.pi)) - (x-xm)**2/2/s**2]
    lny = np.array(lny)
    return lny.reshape(lny.shape[0], lny.shape[1])

##  args: list
def exp_pdf(t, args):
    f = np.array(args[0])
    tau = np.array(args[1])
    y = []
    for f,tau in zip(f,tau):
        y += [f * 1 / tau * np.exp(-t / tau)]
    y = np.array(y)
    return y.reshape(y.shape[0], y.shape[1])

def ln_exp_pdf(t, args):
    f = np.array(args[0])
    tau = np.array(args[1])
    lny = []
    for f,tau in zip(f,tau):
        lny += [np.log(f/tau) - t/tau]
    lny = np.array(lny)
    return lny.reshape(lny.shape[0], lny.shape[1])