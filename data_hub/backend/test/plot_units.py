import matplotlib.pyplot as plt

plt.ion()

edge_points = [
    [121.508, 25.04053],
    [121.50961, 25.04047],
    [121.50806, 25.03905],
    [121.5092, 25.03876],
]


def show_pos(point):
    plt.clf()
    xs, ys = zip(*edge_points)
    plt.scatter(xs, ys, c='g')
    plt.scatter(*point, c='r')
    plt.show()
    plt.pause(0.01)


if __name__ == '__main__':
    pass
    p1 = edge_points[0]
    p2 = edge_points[3]

    import numpy as np

    n = 20

    for p in np.linspace(p1, p2, n):
        show_pos(p)
        print(p)
    plt.ioff()
    plt.show()