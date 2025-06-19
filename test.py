import pandas
import numpy
import os
from copy import deepcopy
from warnings import filterwarnings
from scpi_pkg.scdata import scdata
from scpi_pkg.scdataMulti import scdataMulti
from scpi_pkg.scest import scest
from scpi_pkg.scpi import scpi
from scpi_pkg.scplot import scplot
from scpi_pkg.scplotMulti import scplotMulti

data = pandas.read_csv("scpi_germany.csv")

filterwarnings("ignore")

id_var = 'country'
outcome_var = 'gdp'
time_var = 'year'
features = None
cov_adj = None
period_pre = numpy.arange(1960, 1991)
period_post = numpy.arange(1991, 2004)
unit_tr = 'West Germany'
unit_co = list(set(data[id_var].to_list()))
unit_co = [cou for cou in unit_co if cou != 'West Germany']
constant = False
cointegrated_data = True

data_prep = scdata(df=data, id_var=id_var, time_var=time_var,
                   outcome_var=outcome_var, period_pre=period_pre,
                   period_post=period_post, unit_tr=unit_tr,
                   unit_co=unit_co, features=features, cov_adj=cov_adj,
                   cointegrated_data=cointegrated_data, constant=constant)


print(data_prep.B)
# Set options for inference
w_constr = {'name': 'simplex', 'Q': 1}
u_missp = True
u_sigma = "HC1"
u_order = 1
u_lags = 0
e_method = "gaussian"
e_order = 1
e_lags = 0
e_alpha = 0.05
u_alpha = 0.05
sims = 200
cores = 1

numpy.random.seed(8894)
pi_si = scpi(data_prep,
             sims=sims,
             w_constr=w_constr,
             u_order=u_order,
             u_lags=u_lags,
             e_order=e_order,
             e_lags=e_lags,
             e_method=e_method,
             u_missp=u_missp,
             u_sigma=u_sigma,
             cores=cores,
             e_alpha=e_alpha,
             u_alpha=u_alpha)
print(pi_si)

####################################
# SC - plot results
plot = scplot(pi_si)