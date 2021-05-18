from PyInstaller.utils.hooks import collect_data_files

hiddenimports = ['sklearn.utils.sparsetools._graph_validation',
                 'sklearn.utils.sparsetools._graph_tools',
                 'sklearn.utils.lgamma',
                 'sklearn.utils.weight_vector']

datas = collect_data_files('sklearn')