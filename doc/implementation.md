Implementation notes
====================

Directory structure
-------------------

3rdparty/cjlano_svg: a fork of cjlano's svg library that fixes a bug (cjlano has
not reacted to a pull request). Git submodule.


Model
-----

Shapes are in increasing Z order (back to front).
Groups refer to shapes, but shapes further back are clipped. 