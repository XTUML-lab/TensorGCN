# TensorGCN

The implementation of TensorGCN in paper:

Liu X, You X, Zhang X, et al. Tensor graph convolutional networks for text classification[C]//Proceedings of the AAAI Conference on Artificial Intelligence. 2020, 34(05): 8409-8416.


# Require

Python 3.6

Tensorflow >= 2.5.0


# Reproduing Results

#### 1. Build three graphs

Run TGCN_2layers/build_graph_tgcn.py

#### 2. Training

Run TGCN_2layers/train.py


# Example input data

1. `/data_tgcn/mr/build_train/mr.clean.txt` 每个文档的原始文本。每一行都是一个文档。文档名称为：行号-1

2. `/data_tgcn/mr/build_train/mr.txt` 文档的信息，每一行为一个文档的信息，分别为：文档的名称，训练/测试的分组，文档的标签

3. `/data_tgcn/mr/stanford/mr_pair_stan.pkl` 包含数据集的所有句法关系词对。

4. `/data_tgcn/mr/build_train/mr_semantic_0.05.pkl` 包含数据集的所有语义关系词对。

