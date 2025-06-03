# Delightful Diagrams
Generating technical diagrams should be a delight, but it's not. Diagrams are a representation of data, so they should be a mapping of that data into some useful visual representation.

It stands to reason (maybe) that since SMT solvers can do very complex layouts for circuit boards, integrated circuits, FPGAs, etc. they can probably also do the relatively simple layout required for boxes and lines intended for human use.

Right now, this project is developing a Python API for declaring diagrams with shapes that have constrained relationships, then solving those constraints and emitting a concrete diagram in SVG form. Eventually, I intend to turn that into a domain-specific language (DSL) for describing diagrams that doesn't require you to use Python.
