import matplotlib.pyplot as plt
import numpy as np

def convert_to_grid_index(coordinate, map_size):
    """
    Convert a (lat, lon) tuple into a grid index.
    """
    lat, lon = coordinate
    height, width = map_size
    x, y = int(height - (lat + 90) / 180 * height), int((lon + 180) / 360 * width)
    return x * width + y

def generate_observed_data(map_size, num_data):
    """
    Generate observed data for testing.
    """
    observed_data = []
    for _ in range(num_data):
        lat = np.random.uniform(-90, 90)
        lon = np.random.uniform(-180, 180)
        observed_data.append((lat, lon))
    return observed_data

def generate_transition_matrix(n_grids):
    """
    Generate a random transition matrix.
    """
    transition_matrix = np.random.rand(n_grids, n_grids)
    total = np.sum(transition_matrix, axis=0)
    transition_matrix /= total[:, np.newaxis]
    return transition_matrix

def generate_emission_matrix(n_grids):
    """
    Generate a random emission matrix.
    """
    emission_matrix = np.random.rand(n_grids)
    return emission_matrix

def generate_initial_probability_vector(n_grids):
    """
    Generate a random initial probability vector.
    """
    initial_probability_vector = np.random.rand(n_grids)
    total = np.sum(initial_probability_vector)
    initial_probability_vector /= total
    return initial_probability_vector

import matplotlib.pyplot as plt

# Preprocessing
map_size = (10, 10)  # raster map size
n_grids = map_size[0] * map_size[1]  # number of grids

# Assume we have observed data as a list of tuples (lat, lon)
observed_data = [(37.7749, -122.4194), (37.7750, -122.4193), (37.7751, -122.4192)]

# Convert observed data into grid indices
observed_indices = [convert_to_grid_index(index, map_size) for index in observed_data]

# Initialize the initial probability vector
initial_probability_vector = np.ones(n_grids) / n_grids

# Initialize the transition and emission matrices
transition_matrix = generate_transition_matrix(n_grids)
emission_matrix = generate_emission_matrix(n_grids)
# Initialize the emission matrix
emission_matrix = np.random.rand(n_grids)

# Scale the emission matrix so that its values are between 0 and 1
emission_matrix = (emission_matrix - emission_matrix.min()) / (emission_matrix.max() - emission_matrix.min())

# Print out the arrays for debugging
print("Initial probability vector:")
print(initial_probability_vector)
print("\nTransition matrix:")
print(transition_matrix)
print("\nEmission matrix:")
print(emission_matrix)

# Prediction
# Initialize the probabilities array
probabilities = np.zeros(n_grids)

# Update the probabilities for each observed data point
for data in observed_indices:
    probabilities = np.dot(transition_matrix, probabilities) * emission_matrix[data]
    probabilities /= np.sum(probabilities)

# Plot the probability vector as a heatmap with text labels
fig, ax = plt.subplots()
im = ax.imshow(probabilities.reshape(map_size), cmap='hot')
fig.colorbar(im, ax=ax)

# Add text labels to each grid
for i in range(map_size[0]):
    for j in range(map_size[1]):
        x, y = j, i
        text = ax.text(x, y, f"{probabilities[y * map_size[1] + x]:.3f}", ha="center", va="center", color="black")

plt.show()


print(probabilities)
