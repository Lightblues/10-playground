#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Jul 24 11:02:23 2021

@author: easonshi

from 机器学习算法笔记(三十三)：SVM 使用多项式特征与核函数 https://louyu.cc/articles/machine-learning/2019/10/?p=2087/
"""

from sklearn.svm import SVC  # 这里直接导入SVC，而不是LinearSVC
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
import numpy as np
import matplotlib.pyplot as plt
from sklearn import datasets

# 加载moons数据集，形状是两个半月形，并加上噪音
X, y = datasets.make_moons(noise=0.15, random_state=666)


def PolynomialSVC(degree, C=1.0):
    return Pipeline([
        ("poly", PolynomialFeatures(degree=degree)),  # 使用多项式特征
        ("std_scaler", StandardScaler()),  # 进行标准化
        ("linearSVC", LinearSVC(C=C))       # C 为正则项
    ])


poly_svc = PolynomialSVC(degree=3)      # 三阶
poly_svc.fit(X, y)


def plot_decision_boundary(model, axis):
    x0, x1 = np.meshgrid(
        np.linspace(axis[0], axis[1], int(
            (axis[1] - axis[0]) * 100)).reshape(-1, 1),
        np.linspace(axis[2], axis[3], int(
            (axis[3] - axis[2]) * 100)).reshape(-1, 1),
    )
    X_new = np.c_[x0.ravel(), x1.ravel()]

    y_predict = model.predict(X_new)
    zz = y_predict.reshape(x0.shape)

    from matplotlib.colors import ListedColormap
    custom_cmap = ListedColormap(['#EF9A9A', '#FFF59D', '#90CAF9'])

    plt.contourf(x0, x1, zz, linewidth=5, cmap=custom_cmap)


plot_decision_boundary(poly_svc, axis=[-1.5, 2.5, -1.0, 1.5])
plt.scatter(X[y == 0, 0], X[y == 0, 1])
plt.scatter(X[y == 1, 0], X[y == 1, 1])
plt.show()


# %%
# 多项式，相较于上面的 LinearSVMC 理论上应该差不多；但实际上效果似乎差些

def PolynomialKernelSVC(degree, C=1.0):
    return Pipeline([
        ("std_scaler", StandardScaler()),
        ("kernelSVC", SVC(kernel="poly", degree=degree, C=C))  # 核函数传入poly，也就是多项式核的意思
    ])


poly_kernel_svc = PolynomialKernelSVC(degree=3, C=1)
poly_kernel_svc.fit(X, y)

plot_decision_boundary(poly_kernel_svc, axis=[-1.5, 2.5, -1.0, 1.5])
plt.scatter(X[y == 0, 0], X[y == 0, 1])
plt.scatter(X[y == 1, 0], X[y == 1, 1])
plt.show()


# %%
"""
高斯核函数/RDF
理论参见原文；不同 gamma 控制了曲线的你和能力
"""

def RBFKernelSVC(gamma):
    return Pipeline([
        ("std_scaler", StandardScaler()),  # 进行标准化处理
        ("svc", SVC(kernel="rbf", gamma=gamma))  # 核函数采用rbf核
    ])


svc = RBFKernelSVC(gamma=1)     # gamma越大，高斯分布越集中（倾向 overfit）
svc.fit(X, y)


def plot_decision_boundary(model, axis):
    x0, x1 = np.meshgrid(
        np.linspace(axis[0], axis[1], int(
            (axis[1] - axis[0]) * 100)).reshape(-1, 1),
        np.linspace(axis[2], axis[3], int(
            (axis[3] - axis[2]) * 100)).reshape(-1, 1),
    )
    X_new = np.c_[x0.ravel(), x1.ravel()]

    y_predict = model.predict(X_new)
    zz = y_predict.reshape(x0.shape)

    from matplotlib.colors import ListedColormap
    custom_cmap = ListedColormap(['#EF9A9A', '#FFF59D', '#90CAF9'])

    plt.contourf(x0, x1, zz, linewidth=5, cmap=custom_cmap)


plot_decision_boundary(svc, axis=[-1.5, 2.5, -1.0, 1.5])
plt.scatter(X[y == 0, 0], X[y == 0, 1])
plt.scatter(X[y == 1, 0], X[y == 1, 1])
plt.show()


# %%
