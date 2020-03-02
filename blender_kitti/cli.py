#!/bin/env python
# -*- coding: utf-8 -*-
"""

"""

import click
import numpy as np
import re
import logging
import typing
from collections import defaultdict

from .blender_kitti import add_point_cloud, add_voxels
from .blender_kitti import execute_data_tasks


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter(
    fmt="%(asctime)s - %(levelname)s - %(module)s - %(message)s"
)
handler = logging.StreamHandler()
handler.setFormatter(formatter)
handler.setLevel(logging.INFO)
logger.addHandler(handler)


regex_key = re.compile(r"(.+)\+(.+)\+(.+)")

data_structures = {
    "point_cloud": add_point_cloud,
    "voxels": add_voxels,
}
data_tree = defaultdict(lambda: defaultdict(dict))


def extract_data_tasks_from_file(
    filepath: str,
) -> [(typing.Callable, {str: typing.Any})]:
    logger.info("Processing data file '{}'.".format(filepath))
    data = np.load(filepath)

    def filter_fn(x):
        if x[1] is None:
            logger.warning("Ignoring unknown entry key '{}'.".format(x[0]))
        return x[1] is not None

    matches = [(x, regex_key.fullmatch(x)) for x in data.keys()]
    matches = list(filter(filter_fn, matches))
    matches = [(data[x[0]], x[1].groups()) for x in matches]
    matches = [((x[1][0], x[1][2], x[1][1]), x[0]) for x in matches]

    x = data_tree
    for key, data in matches:
        x[key[0]][key[1]][key[2]] = data

    tasks = []
    for data_type, instances in x.items():
        try:
            f = data_structures[data_type]
            tasks.extend([(f, {"name_prefix": k, **v}) for k, v in instances.items()])

        except KeyError:
            logger.warning("Ignoring unknown entry '{}'.".format(data_type))

    return tasks


def add_data_from_file(filename: str):
    tasks = extract_data_tasks_from_file(filename)
    execute_data_tasks(tasks)


@click.command(
    context_settings={"ignore_unknown_options": True, "allow_extra_args": True}
)
@click.option("--python", required=False)
@click.option("--background/--no-background", required=False)
@click.argument("filenames", type=click.Path(exists=True), nargs=-1)
def render(python, background, filenames):
    """

    """
    for filename in filenames:
        tasks = extract_data_tasks_from_file(filename)
        execute_data_tasks(tasks)
