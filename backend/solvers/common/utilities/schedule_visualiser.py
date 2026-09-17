from collections import defaultdict
from typing import Tuple, List, Dict

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from jinja2 import Template

from core.config import settings
from domain.enums import GraphType, TileType
from domain.models.common.tile import Tile
from solvers.common.models import Schedule
from solvers.hexaly.models import HexalyTile


class ScheduleVisualizer:
    def __init__(self, movers: List[str] = None, coordinate_dict: Dict[str, List[Tuple[int, int]]] = None,
                 tiles: List[HexalyTile] = None, mover_amount: int = 0):
        self.movers = movers
        self.coordinate_dict = coordinate_dict
        if tiles is not None:
            self._init_coordinate_dict(tiles)
        if mover_amount > 0:
            self._init_movers(mover_amount)

    def _get_tile_name(self, tile: Tile) -> str:
        """Returns tile name.

        Args:
            tile: Tile for which the tile name should be returned.

        Returns:
            Name of the tile (medicine name or interface).
        """
        if tile.type == TileType.INTERFACE:
            return 'interface'
        return tile.dispensed_types[0]

    def _init_movers(self, mover_amount: int) -> None:
        """Initializes movers.

        Args:
            mover_amount: Amount of movers.
        """
        self.movers = [f"mover{x}" for x in range(mover_amount)]

    def _init_coordinate_dict(self, tiles: List[HexalyTile]) -> None:
        """Initializes coordinate_dict.
        Args:
            tiles: List of HexalyTiles.
        """
        coord_dict: Dict[str, List[Tuple[int, int]]] = defaultdict(list)

        for tile in tiles:
            if tile.dispensed_types:
                for medicine in tile.dispensed_types:
                    coord_dict[medicine].append((tile.x, tile.y))
            elif tile.type == TileType.INTERFACE:
                coord_dict['interface'].append((tile.x, tile.y))

        self.coordinate_dict = dict(coord_dict)

    def _schedule_to_dataframe(self, schedule: Schedule) -> pd.DataFrame:
        """Converts a Schedule Pydantic model into a pandas DataFrame compatible with the existing Plotly visualization logic.

        Args:
            schedule: Schedule to be converted to DataFrame.

        Returns:
            Dataframe created for schedule compatible with the existing Plotly visualization logic.
        """
        data = []
        for task in schedule.tasks:
            data.append({
                "Task_ID": task.task_id,
                "Mover": f"mover{task.mover_id}",
                "Patient": str(task.order_id),
                "Length": task.duration,
                "Start": task.start,
                "Finish": task.end,
                "Medicine": self._get_tile_name(task.tile),
                "Tile": f"({task.tile.x}, {task.tile.y})",
                "TicksAdded": task.ticks_added
            })

        return pd.DataFrame(data)

    def create_graphs_from_schedule(
            self,
            schedule_options: List[Tuple[Schedule, GraphType, bool, bool]]
    ) -> Tuple[Dict[GraphType, str], Dict[str, str]]:
        """
        Creates graphs and renders HTML content directly from Schedule objects.

        Args:
            schedule_options: List of tuples containing:(schedule, graph_type, should_render, show_legend).

        Returns:
            Tuple containing (dict_of_html_contents, patient_color_dict).
        """
        df_options = []
        for schedule, graph_type, should_render, show_legend in schedule_options:
            df = self._schedule_to_dataframe(schedule)
            df_options.append((df, graph_type, should_render, show_legend))

        return self.create_graphs(df_options)

    def _get_graph_type(self, graph_type: GraphType) -> str:
        if graph_type == GraphType.DISPENSED_TYPE:
            return 'Medicine'
        elif graph_type == GraphType.ORDER:
            return 'Patient'
        else:
            return 'Tile'

    def create_graphs(self, graph_options: List[Tuple[pd.DataFrame, GraphType, bool, bool]]) \
            -> Tuple[Dict[GraphType, str], Dict[str, str]]:
        """
        Creates graphs and renders HTML content.

        Args:
            graph_options: List of tuples containing: (schedule_df, graph_type, should_render, show_legend)
        Returns:
            Tuple containing (list_of_figures, dict_of_html_contents, patient_color_dict)
        """
        patient_color_dict = {'None': '#AAAAAA'}
        to_render = []

        for df, graph_type, should_render, show_legend in graph_options:
            raw_graph_type = graph_type.value
            graph_type = self._get_graph_type(graph_type)
            col_name = graph_type.capitalize()
            df[col_name] = df[col_name].astype(str)
            sorted_movers = self.movers if self.movers else sorted(list(df["Mover"].unique()))
            mover_count = len(sorted_movers)
            calculated_height = max(320, 60 + mover_count * 30)
            graph = px.bar(
                df,
                base="Start",
                x="Length",
                y="Mover",
                color=graph_type,
                orientation='h',
                category_orders={"Mover": sorted_movers}
            )
            graph.update_yaxes(
                type="category",
                categoryorder="array",
                categoryarray=sorted_movers,
                tickmode="array",
                tickvals=sorted_movers,
                ticktext=sorted_movers,
                autorange="reversed",
                title_text="Mover",
                automargin=True
            )
            graph.update_xaxes(
                title_text="Length",
                automargin=True
            )

            for trace in graph.data:
                if raw_graph_type == GraphType.DISPENSED_TYPE:
                    trace.name = f"{trace.legendgroup}"
                    coords = self.coordinate_dict.get(trace.legendgroup, [])
                    if len(coords) > 1:
                        trace.name += f" ({len(coords)}x)"
                else:
                    trace.name = f"{col_name} {trace.legendgroup}"
                patient_color_dict[trace.name] = trace.marker.color
                if 'Tile' in df.columns:
                    # Customize the hover template
                    trace.hovertemplate = "<br>".join([
                        "<b>Medicine: %{customdata[3]}</b>",
                        "<b>Mover: %{y}</b>",
                        "<b>Tile: %{customdata[0]}</b>",
                        "Start: %{customdata[1]}",
                        "Finish: %{customdata[2]}"
                    ])

                    # Add the 'Tile' column to customdata
                    trace.customdata = df.loc[df[graph_type] == f'{trace.legendgroup}'][
                        ["Tile", "Start", "Finish", "Medicine"]].values

                if trace.legendgroup == 'interface':
                    trace.marker.pattern = {'shape': 'x'}

            # Add timeline marker
            graph.add_shape(
                type="line",
                x0=0, x1=0,
                y0=1, y1=0,
                line=dict(color="red", width=2),
                xref='x', yref='paper',
                name="timeline-marker"
            )
            graph.update_layout(
                showlegend=show_legend,
                margin=dict(l=65, r=20, t=18, b=22),
                title=dict(
                    text=f'Colored by {graph_type}',
                    font=dict(size=13),
                    x=0.01,
                    y=0.99,
                    xanchor='left',
                    yanchor='top'
                ),
                autosize=True
            )
            if should_render:
                to_render.append((graph, raw_graph_type))
        html_dict = self.render_html(to_render)
        return html_dict, patient_color_dict

    def render_html(self, render_arr: list[tuple[go.Figure, GraphType]]) -> dict[GraphType, str]:
        """
        Renders the Plotly graphs into HTML strings using the Jinja2 template.

        Args:
            render_arr: List of tuples containing: (graph, graph_type)

        Returns:
            Dictionary containing graph type and HTML contents.
        """
        rendered_htmls = {}

        with open(settings.GRAPH_TEMPLATE_PATH, "r", encoding="utf-8") as template_file:
            j2_template = Template(template_file.read())

        for graph, graph_type in render_arr:
            plotly_jinja_data = {
                "fig": graph.to_html(full_html=False, include_plotlyjs='cdn'),
                "last_mover": self.movers[-1]
            }
            rendered_htmls[graph_type] = j2_template.render(plotly_jinja_data)

        return rendered_htmls
