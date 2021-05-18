"""
构建语义图，句法图和顺序图
"""
import os
import pickle
import pickle as pkl
import random
from math import log
import numpy as np
import scipy.sparse as sp

'''
路径信息
'''
# 语料库路径
dataset = 'mr'
os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
os.path.abspath(os.path.dirname(os.getcwd()))
os.path.abspath(os.path.join(os.getcwd(), ".."))

# 输入路径
input1 = os.sep.join(['..', 'data_tgcn', dataset, 'build_train', dataset])  # 数据集
input2 = os.sep.join(['..', 'data_tgcn', dataset, 'stanford'])
input3 = os.sep.join(['..', 'data_tgcn', dataset, 'lstm'])
input4 = os.sep.join(['..', 'data_tgcn', dataset, 'lstm', dataset])

# 输出路径
output1 = os.sep.join(['..', 'data_tgcn', dataset, 'build_train', dataset])  # 数据集的输出路径
output2 = os.sep.join(['..', 'data_tgcn', dataset, 'build_train'])

'''
参数信息
'''
# 参数：词嵌入的维度，滑动窗口的大小，词嵌入的字典(若为空，没有初始化的特征向量)
word_embeddings_dim = 300
window_size = 20
word_vector_map = {}

'''
读取数据集
'''
# 读取文档信息
# eg: ["0	train	1", "1	train	1"]
doc_name_list = []  # 所有文档
doc_train_list = [] # 用于训练的文档
doc_test_list = []  # 用于测试的文档
f = open(input1 + '.txt', 'r', encoding='latin1')
lines = f.readlines()
for line in lines:
    doc_name_list.append(line.strip())
    temp = line.split("\t")
    if temp[1].find('test') != -1:
        doc_test_list.append(line.strip())
    elif temp[1].find('train') != -1:
        doc_train_list.append(line.strip())
f.close()

# 读取文档原始文本
# eg:["idiotic and ugly", ...]
doc_content_list = []
f = open(input1 + '.clean.txt', 'r')
lines = f.readlines()
for line in lines:
    doc_content_list.append(line.strip())
f.close()

# 提取用于训练的文档名称，并打乱顺序
train_ids = []
for train_name in doc_train_list:
    train_id = doc_name_list.index(train_name)
    train_ids.append(train_id)
random.shuffle(train_ids)

# 记录用于训练的文档名称，并用换行分隔
train_ids_str = '\n'.join(str(index) for index in train_ids)
f = open(output1 + '.train.index', 'w')
f.write(train_ids_str)
f.close()

# 提取用于测试的文档名称，并打乱顺序
test_ids = []
for test_name in doc_test_list:
    test_id = doc_name_list.index(test_name)
    test_ids.append(test_id)
random.shuffle(test_ids)

# 记录用于测试的文档名称，并用换行分隔
test_ids_str = '\n'.join(str(index) for index in test_ids)
f = open(output1 + '.test.index', 'w')
f.write(test_ids_str)
f.close()

# 构建打乱顺序后的文档名称和文档原始文本
ids = train_ids + test_ids
shuffle_doc_name_list = []
shuffle_doc_words_list = []
for id in ids:
    shuffle_doc_name_list.append(doc_name_list[int(id)])
    shuffle_doc_words_list.append(doc_content_list[int(id)])
shuffle_doc_name_str = '\n'.join(shuffle_doc_name_list)
shuffle_doc_words_str = '\n'.join(shuffle_doc_words_list)

# 记录打乱顺序的文档名称和文档原始文本
f = open(output1 + '_doc_shuffle.txt', 'w')
f.write(shuffle_doc_name_str)
f.close()

f = open(output1 + '_word_shuffle.txt', 'w')
f.write(shuffle_doc_words_str)
f.close()

'''
构建词汇表
'''
# 记录单词在整个语料库中出现的次数，
# eg: {"miller":15, "tels":21, ...}
word_freq = {}
# 记录整个语料库中的单词, eg: {"to", "misses"}
word_set = set()
for doc_words in shuffle_doc_words_list:
    words = doc_words.split()
    for word in words:
        word_set.add(word)
        if word in word_freq:
            word_freq[word] += 1
        else:
            word_freq[word] = 1

# 词汇表和词汇数量
vocab = list(word_set)
vocab_size = len(vocab)

# 记录每个单词出现的文档索引，
# eg: {"wang": [0, 6450, 7368, 10267], "xiaoshuai": [0], ....}
word_doc_list = {}
for i in range(len(shuffle_doc_words_list)):
    doc_words = shuffle_doc_words_list[i]
    words = doc_words.split()
    appeared = set()
    for word in words:
        if word in appeared:
            continue
        if word in word_doc_list:
            doc_list = word_doc_list[word]
            doc_list.append(i)
            word_doc_list[word] = doc_list
        else:
            word_doc_list[word] = [i]
        appeared.add(word)

# 记录每个单词出现的文档的数量，
# eg:{"wang": 4, "xiaoshuai": 1, ....}
word_doc_freq = {}
for word, doc_list in word_doc_list.items():
    word_doc_freq[word] = len(doc_list)

# 建立词汇与id的字典和反向字典
word_id_map = {} # {”1970s“: 0, ”behalf“: 1, ...}
id_word_map = {} # {0: ”1970s“, 1: "behalf": 1}
for i in range(vocab_size):
    word_id_map[vocab[i]] = i
    id_word_map[i] = vocab[i]

# 记录词汇表，并用换行分隔
vocab_str = '\n'.join(vocab)
f = open(output1 + '_vocab.txt', 'w')
f.write(vocab_str)
f.close()

'''
标签
'''
# 提取所有的标签
label_set = set()
for doc_meta in shuffle_doc_name_list:
    temp = doc_meta.split('\t')
    label_set.add(temp[2])
label_list = list(label_set)

# 记录标签信息
label_list_str = '\n'.join(label_list)
f = open(output1 + '_labels.txt', 'w')
f.write(label_list_str)
f.close()

'''
构建特征
'''
# 选取训练集中的 90% 用于训练
train_size = len(train_ids)
val_size = int(0.1 * train_size)
real_train_size = train_size - val_size
real_train_doc_names = shuffle_doc_name_list[:real_train_size]

# 记录用于训练的文档信息
real_train_doc_names_str = '\n'.join(real_train_doc_names)
f = open(output1 + '.real_train.name', 'w')
f.write(real_train_doc_names_str)
f.close()

# 构建用于训练的文档的特征向量x(压缩稀疏行矩阵)
row_x = []  # 与每个文档词嵌入维度对应文档标号
col_x = []  # 每个文档词嵌入的每个维度的编号
data_x = []  # 每个文档词嵌入的每个维度的均值
for i in range(real_train_size):
    doc_vec = np.array([0.0 for k in range(word_embeddings_dim)])
    doc_words = shuffle_doc_words_list[i]
    words = doc_words.split()
    doc_len = len(words)
    for word in words:
        if word in word_vector_map:
            word_vector = word_vector_map[word]
            doc_vec += np.array(word_vector)
    for j in range(word_embeddings_dim):
        row_x.append(i)
        col_x.append(j)
        data_x.append(doc_vec[j] / doc_len)

x = sp.csr_matrix((data_x, (row_x, col_x)), shape=(real_train_size, word_embeddings_dim))


# 构建输出(独热编码)，eg: [[1 0], [0 1], [0 1], ...]
y = []
for i in range(real_train_size):
    doc_meta = shuffle_doc_name_list[i]
    temp = doc_meta.split('\t')
    label = temp[2]
    one_hot = [0 for l in range(len(label_list))]
    label_index = label_list.index(label)
    one_hot[label_index] = 1
    y.append(one_hot)
y = np.array(y)

# 构建测试文档的特征向量tx(压缩稀疏行矩阵)
test_size = len(test_ids)

row_tx = []
col_tx = []
data_tx = []
for i in range(test_size):
    doc_vec = np.array([0.0 for k in range(word_embeddings_dim)])
    doc_words = shuffle_doc_words_list[i + train_size]
    words = doc_words.split()
    doc_len = len(words)
    for word in words:
        if word in word_vector_map:
            word_vector = word_vector_map[word]
            doc_vec += np.array(word_vector)

    for j in range(word_embeddings_dim):
        row_tx.append(i)
        col_tx.append(j)
        data_tx.append(doc_vec[j] / doc_len)

tx = sp.csr_matrix((data_tx, (row_tx, col_tx)), shape=(test_size, word_embeddings_dim))

# 构建输出(独热编码)，eg: [[1 0], [0 1], [0 1], ...]
ty = []
for i in range(test_size):
    doc_meta = shuffle_doc_name_list[i + train_size]
    temp = doc_meta.split('\t')
    label = temp[2]
    one_hot = [0 for l in range(len(label_list))]
    label_index = label_list.index(label)
    one_hot[label_index] = 1
    ty.append(one_hot)
ty = np.array(ty)

# allx: 所有的训练文档和所有的词汇的特征向量，x的超集
word_vectors = np.random.uniform(-0.01, 0.01, (vocab_size, word_embeddings_dim))

for i in range(len(vocab)):
    word = vocab[i]
    if word in word_vector_map:
        vector = word_vector_map[word]
        word_vectors[i] = vector

row_allx = []
col_allx = []
data_allx = []
for i in range(train_size):
    doc_vec = np.array([0.0 for k in range(word_embeddings_dim)])
    doc_words = shuffle_doc_words_list[i]
    words = doc_words.split()
    doc_len = len(words)
    for word in words:
        if word in word_vector_map:
            word_vector = word_vector_map[word]
            doc_vec = doc_vec + np.array(word_vector)

    for j in range(word_embeddings_dim):
        row_allx.append(int(i))
        col_allx.append(j)
        data_allx.append(doc_vec[j] / doc_len)

for i in range(vocab_size):
    for j in range(word_embeddings_dim):
        row_allx.append(int(i + train_size))
        col_allx.append(j)
        data_allx.append(word_vectors.item((i, j)))

row_allx = np.array(row_allx)
col_allx = np.array(col_allx)
data_allx = np.array(data_allx)

allx = sp.csr_matrix((data_allx, (row_allx, col_allx)), shape=(train_size + vocab_size, word_embeddings_dim))

# 所有训练文档和所有词汇的输出 y
ally = []
for i in range(train_size):
    doc_meta = shuffle_doc_name_list[i]
    temp = doc_meta.split('\t')
    label = temp[2]
    one_hot = [0 for l in range(len(label_list))]
    label_index = label_list.index(label)
    one_hot[label_index] = 1
    ally.append(one_hot)

for i in range(vocab_size):
    one_hot = [0 for l in range(len(label_list))]
    ally.append(one_hot)

ally = np.array(ally)

print(x.shape, y.shape, tx.shape, ty.shape, allx.shape, ally.shape)

# 记录信息
f = open(output2 + "/ind.{}.x".format(dataset), 'wb')
pkl.dump(x, f)
f.close()

f = open(output2 + "/ind.{}.y".format(dataset), 'wb')
pkl.dump(y, f)
f.close()

f = open(output2 + "/ind.{}.tx".format(dataset), 'wb')
pkl.dump(tx, f)
f.close()

f = open(output2 + "/ind.{}.ty".format(dataset), 'wb')
pkl.dump(ty, f)
f.close()

f = open(output2 + "/ind.{}.allx".format(dataset), 'wb')
pkl.dump(allx, f)
f.close()

f = open(output2 + "/ind.{}.ally".format(dataset), 'wb')
pkl.dump(ally, f)
f.close()

'''
Doc word heterogeneous graph 1
'''

# 单词之间的局部共现语言属性
windows = []

for doc_words in shuffle_doc_words_list:
    words = doc_words.split()
    length = len(words)
    if length <= window_size:
        windows.append(words)
    else:
        for j in range(length - window_size + 1):
            window = words[j: j + window_size]
            windows.append(window)

word_window_freq = {}
for window in windows:
    appeared = set()
    for i in range(len(window)):
        if window[i] in appeared:
            continue
        if window[i] in word_window_freq:
            word_window_freq[window[i]] += 1
        else:
            word_window_freq[window[i]] = 1
        appeared.add(window[i])

word_pair_count = {}
for window in windows:
    for i in range(1, len(window)):
        for j in range(0, i):
            word_i = window[i]
            word_i_id = word_id_map[word_i]
            word_j = window[j]
            word_j_id = word_id_map[word_j]
            if word_i_id == word_j_id:
                continue
            word_pair_str = str(word_i_id) + ',' + str(word_j_id)
            if word_pair_str in word_pair_count:
                word_pair_count[word_pair_str] += 1
            else:
                word_pair_count[word_pair_str] = 1
            # two orders
            word_pair_str = str(word_j_id) + ',' + str(word_i_id)
            if word_pair_str in word_pair_count:
                word_pair_count[word_pair_str] += 1
            else:
                word_pair_count[word_pair_str] = 1

row = []
col = []
weight = []
weight1 = []
weight2 = []

# 根据stanford句法依存构建边权重 dict {"like,moore":2, "moore,like":2, "progressive,moore": 1}
data1 = pickle.load(open(input2 + "/{}_pair_stan.pkl".format(dataset), "rb"))
max_count1 = 0.0
min_count1 = 0.0
count1 = []
for key in data1:
    if data1[key] > max_count1:
        max_count1 = data1[key]
    if data1[key] < min_count1:
        min_count1 = data1[key]
    count1.append(data1[key])
count_mean1 = np.mean(count1)
count_var1 = np.var(count1)
count_std1 = np.std(count1, ddof=1)

# 根据语义依存构建边权重 dict {",moore":22, ",is": 1967, ",like": 492}
data2 = pickle.load(open(input4 + "_semantic_0.05.pkl", "rb"))
max_count2 = 0.0
min_count2 = 0.0
count2 = []
for key in data2:
    if data2[key] > max_count2:
        max_count2 = data2[key]
    if data2[key] < min_count2:
        min_count2 = data2[key]
    count2.append(data2[key])
count_mean2 = np.mean(count2)
count_var2 = np.var(count2)
count_std2 = np.std(count2, ddof=1)

# compute weights
num_window = len(windows)
for key in word_pair_count:
    temp = key.split(',')
    i = int(temp[0])
    j = int(temp[1])
    count = word_pair_count[key]
    word_freq_i = word_window_freq[vocab[i]]
    word_freq_j = word_window_freq[vocab[j]]
    pmi = log((1.0 * count / num_window) /
              (1.0 * word_freq_i * word_freq_j / (num_window * num_window)))
    if pmi <= 0:
        continue
    # pmi
    row.append(train_size + i)
    col.append(train_size + j)
    weight.append(pmi)
    # 句法依存
    if i not in id_word_map or j not in id_word_map:
        continue
    newkey = id_word_map[i] + ',' + id_word_map[j]
    if newkey in data1:
        # min-max标准化
        wei = (data1[newkey] - min_count1) / (max_count1 - min_count1)
        # 0均值标准化
        # wei = (data1[key]-count_mean1)/ count_std1
        # 出现频度比例，出现1的时候比较多
        # wei = data1[key] / data2[key]
        weight1.append(wei)
    else:
        weight1.append(pmi)
    # 语义依存
    if newkey in data2:
        # min-max标准化
        wei = (data2[newkey] - min_count2) / (max_count2 - min_count2)
        # 0均值标准化
        # wei = (data2[key]-count_mean2)/ count_std2
        # 出现频度比例，出现1的时候比较多
        # wei = data2[key] / data2[key]
        weight2.append(wei)
    else:
        weight2.append(pmi)


# doc word frequency
weight_tfidf = []
doc_word_freq = {}
for doc_id in range(len(shuffle_doc_words_list)):
    doc_words = shuffle_doc_words_list[doc_id]
    words = doc_words.split()
    for word in words:
        word_id = word_id_map[word]
        doc_word_str = str(doc_id) + ',' + str(word_id)
        if doc_word_str in doc_word_freq:
            doc_word_freq[doc_word_str] += 1
        else:
            doc_word_freq[doc_word_str] = 1

for i in range(len(shuffle_doc_words_list)):
    doc_words = shuffle_doc_words_list[i]
    words = doc_words.split()
    doc_word_set = set()
    for word in words:
        if word in doc_word_set:
            continue
        j = word_id_map[word]
        key = str(i) + ',' + str(j)
        freq = doc_word_freq[key]
        if i < train_size:
            row.append(i)
        else:
            row.append(i + vocab_size)
        col.append(train_size + j)
        idf = log(1.0 * len(shuffle_doc_words_list) /
                  word_doc_freq[vocab[j]])
        weight_tfidf.append(freq * idf)
        doc_word_set.add(word)

weight = weight + weight_tfidf
node_size = train_size + vocab_size + test_size
adj = sp.csr_matrix(
    (weight, (row, col)), shape=(node_size, node_size))

# dump objects
f = open(output2 + '/ind.{}.adj'.format(dataset), 'wb')
pkl.dump(adj, f)
f.close()

print('构图1完成')

weight = weight1 + weight_tfidf
node_size = train_size + vocab_size + test_size
adj = sp.csr_matrix(
    (weight, (row, col)), shape=(node_size, node_size))

# dump objects
f = open(output2 + '/ind.{}.adj1'.format(dataset), 'wb')
pkl.dump(adj, f)
f.close()

print('构图2完成')

weight = weight2 + weight_tfidf
node_size = train_size + vocab_size + test_size
adj = sp.csr_matrix(
    (weight, (row, col)), shape=(node_size, node_size))

# dump objects
f = open(output2 + '/ind.{}.adj2'.format(dataset), 'wb')
pkl.dump(adj, f)
f.close()

print('构图3完成')
