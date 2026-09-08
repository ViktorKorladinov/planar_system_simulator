import matplotlib.patches
import gurobipy as g
import matplotlib.pyplot as plt


class RoutingSites:

    def __init__(self, interfaces, rows, cols=None, filled=True, unavailable_coords=None):
        self.interfaces = interfaces
        self.rows = rows
        cols = cols if cols is not None else rows
        self.cols = cols
        self.filled = filled
        self.unavailable_coords = unavailable_coords

        # calculate all possible resting sites
        vertices = self.get_all_vertices()
        self.vertices = vertices

        # init model
        model = g.Model()
        model.params.LogToConsole = 0
        model.params.OutputFlag = 0
        self.model = model

        # init model variables
        self.var_selected_vertices = self.model.addVars(vertices, vtype=g.GRB.BINARY)
        self.var_outfitted_tiles = model.addVars(cols, rows, vtype=g.GRB.BINARY)

        # set constraints
        self.set_constraints()

        # run model
        resting_sites = self.generate_rest_sites()
        self.resting_sites = resting_sites

    def is_valid_tile(self, i, j):
        """Determines if a tile is part of the valid grid based on topology"""

        if self.unavailable_coords and [i, j] in self.unavailable_coords:
            return False

        if self.filled:
            return True

        # For ring topology, only the outer ring is valid
        return (i == 0 or i == self.cols - 1 or
                j == 0 or j == self.rows - 1)

    def is_valid_vertex(self, i, j, direction):
        """
        Determines if a vertex position is valid based on topology
        For ring topology, vertices must be between two valid tiles
        """
        if self.unavailable_coords and [i, j] in self.unavailable_coords:
            return False

        # Check if the vertex is between two valid tiles
        if direction == 'e':
            return (i < self.cols - 1 and
                    self.is_valid_tile(i, j) and
                    self.is_valid_tile(i + 1, j))
        elif direction == 's':
            return (j < self.rows - 1 and
                    self.is_valid_tile(i, j) and
                    self.is_valid_tile(i, j + 1))
        elif direction == 'w':
            return (i > 0 and
                    self.is_valid_tile(i, j) and
                    self.is_valid_tile(i - 1, j))
        elif direction == 'n':
            return (j > 0 and
                    self.is_valid_tile(i, j) and
                    self.is_valid_tile(i, j - 1))
        return False

    def get_tile_vertices(self, i, j):
        if not self.is_valid_tile(i, j):
            return set()

        tile_vertices = set()

        # Only add vertices that are between two valid tiles
        if i == 0:
            if self.is_valid_vertex(i, j, 'e'):
                tile_vertices.add((i, j, 'e'))
        elif i == self.cols - 1:
            if self.is_valid_vertex(i, j, 'w'):
                tile_vertices.add((i - 1, j, 'e'))
        else:
            if self.is_valid_vertex(i, j, 'e'):
                tile_vertices.add((i, j, 'e'))
            if self.is_valid_vertex(i, j, 'w'):
                tile_vertices.add((i - 1, j, 'e'))

        if j == 0:
            if self.is_valid_vertex(i, j, 's'):
                tile_vertices.add((i, j, 's'))
        elif j == self.rows - 1:
            if self.is_valid_vertex(i, j, 'n'):
                tile_vertices.add((i, j - 1, 's'))
        else:
            if self.is_valid_vertex(i, j, 's'):
                tile_vertices.add((i, j, 's'))
            if self.is_valid_vertex(i, j, 'n'):
                tile_vertices.add((i, j - 1, 's'))

        return tile_vertices

    def get_all_vertices(self):
        vertices = set()
        for i in range(self.cols):
            for j in range(self.rows):
                for v in self.get_tile_vertices(i, j):
                    vertices.add(v)
        return vertices

    def set_constraints(self):
        for i in range(self.cols):
            for j in range(self.rows):
                if not self.is_valid_tile(i, j):
                    continue

                tile_vertices = self.get_tile_vertices(i, j)
                if not tile_vertices:
                    continue

                if (i, j) in self.interfaces:
                    self.model.addConstr(g.quicksum(self.var_selected_vertices[v] for v in tile_vertices) <= 2)
                else:
                    self.model.addConstr(g.quicksum(self.var_selected_vertices[v] for v in tile_vertices) <= 1)

                # maximizing the number of tiles with at least one waiting location
                count_tiles_outfitted = (self.var_selected_vertices[v] for v in tile_vertices)
                self.model.addConstr(g.quicksum(count_tiles_outfitted) >= self.var_outfitted_tiles[i, j])

    def visualize(self, show=True, save=False):
        if not show and not save:
            return

        fig, ax = plt.subplots(figsize=(self.cols, self.rows))

        # Draw the grid lines for valid tiles only
        for i in range(self.rows + 1):
            for j in range(self.cols):
                if self.is_valid_tile(j, i) or (i > 0 and self.is_valid_tile(j, i - 1)):
                    ax.plot([j, j + 1], [i, i], color="black")

        for j in range(self.cols + 1):
            for i in range(self.rows):
                if self.is_valid_tile(j - 1, i) or (j < self.cols and self.is_valid_tile(j, i)):
                    ax.plot([j, j], [i, i + 1], color="black")

        # Draw vertices and selected sites - MODIFIED for top-left origin
        for v in self.vertices:
            x = v[0] + (0.5 if v[2] == 'e' else 0)
            y = v[1] + (0.5 if v[2] == 's' else 0)  # Removed self.rows - inversion
            selected = int(round(self.var_selected_vertices[v].x))

            if selected:
                color = 'yellow'
                xy = (x + 0.25, y + 0.25)  # Adjusted y coordinate
                ax.add_patch(matplotlib.patches.Rectangle(xy, .5, .5, facecolor=color, alpha=0.4))
            else:
                color = 'blue' if v[2] == 'e' else 'red' if v[2] == 's' else 'black'
            ax.plot(x + 0.5, y + 0.5, 'o', color=color)  # Adjusted y coordinate

        # interface locations - MODIFIED for top-left origin
        for (i, j) in self.interfaces:
            if self.is_valid_tile(i, j):
                xy = (i, j)  # Removed self.rows - inversion
                ax.add_patch(matplotlib.patches.Rectangle(xy, 1, 1, facecolor='red', alpha=0.2, hatch='/'))

        # Set the axis limits and aspect ratio
        ax.set_xlim(-0.5, self.cols + 0.5)
        ax.set_ylim(self.rows + 0.5, -0.5)  # Inverted y-axis limits to put (0,0) at top-left
        ax.set_aspect('equal')
        ax.axis('off')

        if show:
            plt.show()
        if save:
            plt.savefig("routing-resting_sites.pdf", format="pdf", bbox_inches="tight")
    def generate_rest_sites(self):
        """
        Generates optimal resting sites for given layout
        """
        # set objective
        self.model.setObjectiveN(-self.var_outfitted_tiles.sum(), 0, 2)
        self.model.setObjectiveN(-self.var_selected_vertices.sum(), 1, 1)

        # run model
        self.model.optimize()

        # parse results
        resting_sites = []
        for v in self.vertices:
            if int(round(self.var_selected_vertices[v].x)) == 1:
                resting_sites.append(v)
        return resting_sites

    def find_nearest_rest_sites(self, x, y, amount=None):
        """
        Finds the N nearest resting sites for given x,y coordinates
        """
        amount = amount if amount is not None else len(self.resting_sites)
        distances = []

        for site in self.resting_sites:
            site_x, site_y, _ = site
            distance = abs(site_x - x) + abs(site_y - y)
            distances.append((distance, site))

        distances.sort(key=lambda d: d[0])
        return [site for _, site in distances[:amount]]


if __name__ == '__main__':
    # Example usage with ring topology
    interface_list = [(0, 3), (2, 13)]
    arr = [[0, 2], [0, 3], [0, 4], [0, 5], [0, 6], [1, 3], [1, 4], [1, 5], [2, 3], [2, 4], [2, 5], [3, 3], [3, 4], [3, 5], [5, 3], [5, 4], [5, 5], [6, 3], [6, 4], [6, 5], [7, 3], [7, 4], [7, 5], [8, 3], [8, 4], [8, 5], [8, 6]]
    sites = RoutingSites(interface_list, 9, 9, True, arr)  # 6x6 ring
    sites.visualize(show=True, save=False)
    print(sites.resting_sites)
