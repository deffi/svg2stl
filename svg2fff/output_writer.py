from contextlib import contextmanager
from typing import Iterable, Sequence, TextIO, Dict, Optional
import re

from svg2fff.model import Shape, Group
from svg2fff.scad import Writer as ScadWriter, Identifier
from svg2fff.util import with_remaining, FactoryDict, conditional

# Identifiers are generated from SVG element IDs.
#   * First, the ID is sanitized. Invalid characters are replaced with an
#     underscore, followed by their character value:
#         foo.bar -> foo_2Ebar
#     Underscores are replaced with two underscores:
#         foo_bar -> foo__bar
#     The result should be unique for different ID.
#   * The identifier is generated by appending a suffix (see ShapeNames and
#     GroupNames). Since the suffixes are suffix free (i. e., no suffix ends
#     with another suffix), all generated identifiers should be unique. Also,
#     there should be no collisions with OpenSCAD reserved words.
#
# Alternatives:
#   1. Also escape underscores.
#   2. Keep single underscores as long as they don't cause cause collisions.
#   3. Replace invalid characters by underscores and append a number to make the
#      result unique.
# (1) and (2) would make the result for one element ID depend on the value of
# other element IDs, making it hard to predict.


def sanitize_identifier(identifier: str):
    def replace(match):
        text = match.group(0)
        assert len(text) == 1

        if text == "_":
            return "__"
        else:
            value = ord(text[0])
            return f"_{value:02X}"

    return re.sub(r'[^a-zA-Z0-9]', replace, identifier)


# TODO these should be wrappers around the respective object; that would
# simplify the code
class ShapeNames:
    def __init__(self, shape: Shape):
        name = sanitize_identifier(shape.name)
        path_count = len(shape.polygon.paths)
        self.points = Identifier(f"points_{name}")
        self.paths = [Identifier(f"path_{name}_{index}") for index in range(path_count)]
        self.shape = Identifier(f"shape_{name}")
        self.clipped_shape = Identifier(f"clipped_{name}")


class GroupNames:
    def __init__(self, group: Group):
        name = sanitize_identifier(group.color.display_name())
        self.group = Identifier(f"group_{name}")


class OutputWriter:
    def __init__(self, file: TextIO):
        self.scad_writer = ScadWriter(file)
        self._shape_names: Dict[Shape, ShapeNames] = FactoryDict(ShapeNames)
        self._group_names: Dict[Group, GroupNames] = FactoryDict(GroupNames)

    @contextmanager
    def at_height(self, offset: float):
        with conditional(offset != 0, self.scad_writer.translate([0, 0, offset]), None):
            yield

    def write_points_and_paths(self, shapes: Iterable[Shape]):
        self.scad_writer.blank_line()
        self.scad_writer.comment("Points and paths for each shape")

        for shape in shapes:
            points, paths = shape.polygon.index_paths()
            self.scad_writer.assignment(self._shape_names[shape].points, points)
            for index, path in enumerate(paths):
                self.scad_writer.assignment(self._shape_names[shape].paths[index], path)

    def write_shapes(self, shapes: Iterable[Shape]):
        self.scad_writer.blank_line()
        self.scad_writer.comment("Shapes")

        for index, shape in enumerate(shapes):
            self.scad_writer.comment(f"{shape.name}")
            names = self._shape_names[shape]
            with self.scad_writer.define_module(names.shape):
                self.scad_writer.polygon(names.points, names.paths, short=True)

    def write_clipped_shapes(self, shapes: Sequence[Shape]):
        self.scad_writer.blank_line()
        self.scad_writer.comment("Clipped shapes")

        for shape, remaining in with_remaining(shapes):
            names = self._shape_names[shape]
            with self.scad_writer.define_module(names.clipped_shape):
                with self.scad_writer.difference():
                    self.scad_writer.instance(names.shape)
                    for upper_shape in remaining:
                        self.scad_writer.instance(self._shape_names[upper_shape].shape)

    def write_groups(self, groups: Iterable[Group]):
        self.scad_writer.blank_line()
        self.scad_writer.comment("Groups")

        for group in groups:
            with self.scad_writer.define_module(self._group_names[group].group):
                # Implicit union
                for shape in group.shapes:
                    shape_names = self._shape_names[shape]
                    self.scad_writer.instance(shape_names.clipped_shape)

    def instantiate_groups(self, groups: Iterable[Group], *, height: float, offset: float):
        self.scad_writer.blank_line()
        self.scad_writer.comment("Extrude groups")

        for index, group in enumerate(groups):
            with self.at_height(offset):
                with self.scad_writer.color(group.color):
                    with self.scad_writer.extrude(height):
                        self.scad_writer.instance(self._group_names[group].group)

    def instantiate_overlay(self, shapes: Iterable[Shape], *, height: float, offset: float):
        if height:
            with self.at_height(offset):
                with self.scad_writer.extrude(height):
                    for shape in shapes:
                        self.scad_writer.instance(self._shape_names[shape].shape)

    @contextmanager
    def flip(self, total_height):
        with self.scad_writer.translate([0, 0, total_height]):
            with self.scad_writer.rotate([180, 0, 0]):
                yield

    def write(self, shapes: Sequence[Shape], groups: Sequence[Group], thickness: float,
              overlay_thickness: Optional[float] = None, *, flip: float) -> None:
        """Note that we can't collect the shapes from the groups because their
        order matters for clipping."""

        # We always write all shapes, even if we don't end up using them.

        # Write an introductory comment
        self.scad_writer.comment("Written by svg2fff")

        # Write the definitions
        self.write_points_and_paths(shapes)
        self.write_shapes(shapes)
        self.write_clipped_shapes(shapes)
        self.write_groups(groups)

        # Write the instantiations
        with conditional(flip is not None, self.flip(flip), None):
            self.instantiate_groups(groups, height=thickness, offset=0)
            self.instantiate_overlay(shapes, height=overlay_thickness, offset=thickness)
