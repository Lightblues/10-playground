import tensorflow as tf


# train
model = build_model(ratings, embedding_dim=30, init_stddev=0.5)
model.train(num_iterations=1000, learning_rate=10.)
model.train(
    learning_rate=8., num_iterations=3000, optimizer=tf.optimizers.AdagradOptimizer)


# 稀疏矩阵
tf.SparseTensor(
  indices=[[0, 0], [0, 1], [1,3]],
  values=[5.0, 3.0, 1.0],
  dense_shape=[2, 4]
)

# 计算稀疏矩阵的loss
def sparse_mean_square_error(sparse_ratings, user_embeddings, movie_embeddings):
    """
    Args:
    sparse_ratings: A SparseTensor rating matrix, of dense_shape [N, M]
    user_embeddings: A dense Tensor U of shape [N, k] where k is the embedding
      dimension, such that U_i is the embedding of user i.
    movie_embeddings: A dense Tensor V of shape [M, k] where k is the embedding
      dimension, such that V_j is the embedding of movie j.
    Returns:
    A scalar Tensor representing the MSE between the true ratings and the
      model's predictions.
    """
    predictions = tf.gather_nd(
      tf.matmul(user_embeddings, movie_embeddings, transpose_b=True),
      sparse_ratings.indices)
    loss = tf.losses.mean_squared_error(sparse_ratings.values, predictions)
    return loss
    # or
    # predictions = tf.reduce_sum(
    #     tf.gather(user_embeddings, sparse_ratings.indices[:, 0]) *
    #     tf.gather(movie_embeddings, sparse_ratings.indices[:, 1]),
    #     axis=1)
    # loss = tf.losses.mean_squared_error(sparse_ratings.values, predictions)
    # return loss


# 推荐系统 RS
"""
U_var = ...
V_var = ...
loss = ...
model = CFModel(U_var, V_var, loss)
model.train(iterations=100, learning_rate=1.0)
user_embeddings = model.embeddings['user_id']
movie_embeddings = model.embeddings['movie_id']
"""