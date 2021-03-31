
from EM_Algorithm.gen_gauss import gen_gauss
from EM_Algorithm.EM import *

if __name__ == '__main__':
    n_sample = 200
    data = gen_gauss(mean=[6,12,18,24], std=[2,2,2,2], n_sample=[n_sample]*4)
    data = data.reshape(-1,1)
    n_sample = len(data)
    ##  fit GMM
    EMg = EM(data)
    opt_components = EMg.opt_components(tolerance=1e-2, mode='GMM', criteria='AIC', figure=False)

    f, m, s = EMg.GMM(opt_components, tolerance=1e-2)
    EMg.plot_EM_results()
    EMg.plot_fit_gauss(scatter='True')





