
from matplotlib import rcParams
rcParams["font.family"] = "sans-serif"
rcParams["font.sans-serif"] = ["Arial"]

from basic.select import get_files, select_folder
import scipy.io as sio
import numpy as np
import matplotlib.pyplot as plt
from sklearn.mixture import GaussianMixture
from EM_Algorithm.EM import EM


# def GMM_results(data, n_components, tolerance=10e-5):
#     ### fit GMM
#     f_save, m_save, s_save, label, data_cluster, BIC, AIC = GMM(data, n_components, tolerance=tolerance)
#     ##  plot EM results(mean, std, fractio with iteration)
#     plot_EM_results(m_save, s_save, f_save)
#     ##  plot data histogram and its gaussian EM (GMM) results
#     plot_fit_gauss(step, f_save[-1,:], m_save[-1,:], s_save[-1,:])
#
#     return f_save[-1,:], m_save[-1,:] ,s_save[-1,:], data_cluster, label, BIC, AIC
#
#
#
# def poiEM_results(data, n_components, tolerance=10e-5):
#     ##  fit EM
#     f_save, tau_save = exp_EM(data, n_components, tolerance=tolerance)
#     ##  plot EM results(mean, std, fractio with iteration)
#     plot_EM_results_exp([f_save, tau_save], ['fraction', 'dwell time'])
#     ##  plot data histogram and its gaussian EM (GMM) results
#     plot_fit_pdf(dwell, exp_pdf, [f_save[-1,:], tau_save[-1,:]])
#
#     return f_save[-1,:], tau_save[-1,:]
#

if __name__ == '__main__':
        
    conc = [0.0, 0.5, 1.0, 1.5, 2.0, 3.0]
    # conc = [0.0, 1.0, 1.5, 2.0]
    # conc = [3.0]
    
    path_folder = select_folder()
    steps = []
    dwells = []
    tolerance = 1e-3

    all_fractions = []
    all_centers = []
    all_stds = []

    # name = f'S5S1_{c}
    all_tau = []
    all_ftau = []
    all_stau = []
    for c in conc:
        path_data = get_files(f'S5S1_{c}*.mat', dialog=False, path_folder=path_folder)
        step = []
        dwell = []
        for path in path_data:
            data = sio.loadmat(path)
            step = np.append(step, data['step'])
            dwell = np.append(dwell, [data['dwell']])

        ## get Gaussian EM results
        EM_g = EM(step)
        n_components_g = EM_g.opt_components(tolerance=1e-2, mode='GMM', criteria='BIC', figure=False)
        f, m, s, labels, data_cluster = EM_g.GMM(n_components_g)
        EM_g.plot_fit_gauss(scatter=True)

        steps += [step]
        dwells += [dwell]

        all_fractions += [f[-1, :]]
        all_centers += [m[-1,:]]
        all_stds += [s[-1,:]]

    
        ## get poisson EM results
        EM_p = EM(dwell)
        n_components_p = EM_p.opt_components(tolerance=1e-2, mode='PEM', criteria='AIC', figure=False)
        f_tau, tau, s_tau, labels, data_cluster = EM_p.PEM(n_components_p)
        # EM_p.plot_fit_exp()
        all_ftau += [f_tau[-1, :]]
        all_tau += [tau[-1, :]]
        all_stau += [s_tau[-1,:]]


    
    
