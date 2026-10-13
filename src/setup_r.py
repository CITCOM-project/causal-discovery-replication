import rpy2.robjects.packages as rpackages
from rpy2 import robjects
from rpy2.robjects.vectors import StrVector

robjects.r('.libPaths(c("~/.local/share/R/library", .libPaths()))')

utils = rpackages.importr("utils")
utils.chooseCRANmirror(ind=1)

# Install BiocManager and required packages
utils.install_packages(StrVector(["BiocManager"]))
biocmanager = rpackages.importr("BiocManager")
biocmanager.install(StrVector(["graph", "RBGL", "pcalg", "SID"]))
