import tensorflow as tf
import numpy as np

from .layer import Layer

class SpatialPoolingLayer(Layer):
    """
    Represents the spatial pooling computation layer
    """
    def __init__(self, output_dim, sparsity=0.02, learning_rate=0.1, **kwargs):
        self.output_dim = output_dim
        self.sparsity = sparsity
        self.learning_rate = learning_rate
        self.top_k = int(self.sparsity * np.prod(self.output_dim))
        print('Spatial pooling layer with top-k=', self.top_k)
        super().__init__(**kwargs)

    def build(self, input_shape):
        # TODO: Implement potential pool matrix
        # Permanence of connections between neurons
        self.p = tf.Variable(tf.random_uniform((input_shape[1], self.output_dim), 0, 1), name='Permanence')
        super().build(input_shape)

    def call(self, x):
        # TODO: Implement potential pool matrix
        # Connection matrix, dependent on the permenance values
        # If permenance > 0.5, we are connected.
        connection = tf.to_int32(tf.round(self.p))

        # TODO: Only global inhibition is implemented.
        # TODO: Implement boosting
        # Compute the overlap score between input
        overlap = tf.matmul(tf.to_int32(x), connection)

        # Compute active mini-columns.
        # The top k activations of given sparsity activates
        # TODO: Implement stimulus threshold
        # TODO: Hard coded such that batch is not supported.
        _, act_indicies = tf.nn.top_k(overlap, k=self.top_k, sorted=False)
        act_indicies = tf.to_int64(tf.pad(tf.reshape(act_indicies, [self.top_k, 1]), [[0, 0], [1, 0]]))
        act_vals = tf.ones((self.top_k,))
        activation = tf.SparseTensor(act_indicies, act_vals, [1, self.output_dim])
        return activation

    def train(self, x, y):
        """
        Weight update using Hebbian learning rule.

        For each active SP mini-column, we reinforce active input connections
        by increasing the permanence, and punish inactive connections by
        decreasing the permanence.
        We only want to modify permances of connections in active mini-columns.
        Ignoring all non-connections.
        Connections are clipped between 0 and 1.
        """
        # Construct a binary connection matrix with all non-active mini-columns
        # masked to zero. This contains all connections to active units.
        active_cons = tf.matmul(c, tf.diag(y[0]))

        # Shift input X from 0, 1 to -1, 1.
        x_shifted = 2 * tf.to_int32(x) - 1
        # Compute delta matrix, which contains -1 for all connections to punish
        # and 1 for all connections to reinforce. Use broadcasting behavior.
        delta = tf.transpose(x_shifted * tf.transpose(active_cons))

        # Apply learning rate multiplier
        new_p = tf.clip_by_value(self.p + self.learning_rate * delta, 0, 1)

        # Create train op
        train_op = tf.assign(self.p, new_p)
        return tran_op