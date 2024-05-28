# MIT License

# Copyright (c) 2024 Yuxuan Shao

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# Version: 0.2.4

# PyERM Usage Example (Clustering)

# import the necessary packages
import pyerm
from PIL import Image
import numpy as np
from io import BytesIO
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.metrics import accuracy_score
from scipy.stats import multivariate_normal

def demo_experiment(exp: pyerm.Experiment):
    # task init
    exp.task_init("Clustering")

    # data generation & init
    dataset_params = {
        "n_samples_one_type": 100,
        "mean1": np.random.rand(2),
        "cov1": np.random.rand(2, 2),
        "mean2": np.random.rand(2),
        "cov2": np.random.rand(2, 2),
        "mean3": np.random.rand(2),
        "cov3": np.random.rand(2, 2),
    }
    exp.data_init("2D Gaussian Data", dataset_params)

    # method init
    method_params = {
        'n_clusters': 3,
        'random_state': np.random.randint(100),
    }
    exp.method_init("KMeans", method_params)

    # data generation & processing
    data1 = np.random.multivariate_normal(dataset_params['mean1'], dataset_params['cov1'], dataset_params['n_samples_one_type'])
    data2 = np.random.multivariate_normal(dataset_params['mean2'], dataset_params['cov2'], dataset_params['n_samples_one_type'])
    data3 = np.random.multivariate_normal(dataset_params['mean3'], dataset_params['cov3'], dataset_params['n_samples_one_type'])
    X = np.vstack((data1, data2, data3))
    y_true = np.array([0]*100 + [1]*100 + [2]*100)
    indices = np.random.permutation(len(X))
    X = X[indices]
    y_true = y_true[indices]

    # method execution
    kmeans = KMeans(**method_params)
    exp.experiment_start(f"This is the {exp.run_times+1}th experiment", tags=['demo', 'test'], experimenters=['Alice', 'Bob'])
    y_pred = kmeans.fit_predict(X)

    accuracy = accuracy_score(y_true, y_pred)
    print(f'Clustering accuracy: {accuracy:.2f}')

    fig, ax = plt.subplots()
    ax.scatter(X[:, 0], X[:, 1], c=y_pred, cmap='viridis', marker='o')
    ax.scatter(kmeans.cluster_centers_[:, 0], kmeans.cluster_centers_[:, 1], s=300, c='red', marker='x')
    ax.set_title('KMeans Clustering of 2D Gaussian Data')
    ax.set_xlabel('X1')
    ax.set_ylabel('X2')

    buf = BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)

    image = Image.open(buf)

    # experiment over and result saving
    rst_dict = {
        'accuracy': accuracy,
    }
    img_dict = {
        'clustering_result': image,
    }
    exp.experiment_over(rst_dict, img_dict)



# hyperparameters for the experiment

# the default path is '~/experiments.db'
exp = pyerm.Experiment()
for i in range(5):
    demo_experiment(exp)



