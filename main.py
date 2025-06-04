from __future__ import annotations
import svg
import sys
import z3

def main():
    d = Document()
    next_left = 0
    next_top = 0
    for y in range(1, 11):
        for x in range(1, 11):
            if (x+y-1) % 15 == 0:
                color = "purple"
            elif (x+y-1) % 3 == 0:
                color = "red"
            elif (x+y-1) % 5 == 0:
                color = "blue"
            else:
                color = "white"

            r = d.newRect(f"rect{x}-{y}", width=15, height=15, fill=color)
            d.extra_constraints.append(r.get_attr("left") == next_left)
            d.extra_constraints.append(r.get_attr("top") == next_top)
            next_left = r.get_attr("right")
        next_top = r.get_attr("bottom")
        next_left = 0
    
    print(d.render())

class Rect:
    def __init__(self, document: Document, name: str, fill="white"):
        self.name = name
        self.document = document
        self.fill = fill

    def get_attr(self, attr_name: str) -> z3.ArithRef:
        return z3.Int(self.name + "__" + attr_name)

    def render(self, values: dict[str, int]) -> svg.Element:
        x = values[self.name + "__" + "x"]
        y = values[self.name + "__" + "y"]
        width = values[self.name + "__" + "width"]
        height = values[self.name + "__" + "height"]

        return svg.Rect(
            fill=self.fill, stroke_width=1, stroke="black",
            x=x, y=y, width=width, height=height
        )
    
class Document:
    def __init__(self):
        self.elements: list[Rect] = []
        self.extra_constraints: list[z3.z3.BoolRef] = []

    def render(self) -> svg.SVG:
        s = z3.Solver()
        for c in self.extra_constraints:
            s.add(c)

        if s.check().r != z3.Z3_L_TRUE:
            print("Couldn't satisfy the constraints, aborting", file=sys.stderr)
            sys.exit(1)

        values: dict[str, int] = {}
        m = s.model()
        for d in m.decls():
            values[d.name()] = m[d].as_long()

        es = [e.render(values) for e in self.elements]

        return svg.SVG(
            elements=es,
        )


    def newRect(self, name: str, fill="white", x: int | None = None, y: int | None = None, height: int | None = None, width: int | None = None) -> Rect:
        # First we need to get the new shape object
        r = Rect(self, name, fill=fill)

        # Add that object to our list of objects in the document
        self.elements.append(r)

        # We need to handle the (possibly impossible to satisfy) concrete constraints
        if x is not None:
            self.extra_constraints.append(r.get_attr("x") == x)
        if y is not None:
            self.extra_constraints.append(r.get_attr("y") == y)
        if height is not None:
            self.extra_constraints.append(r.get_attr("height") == height)
        if width is not None:
            self.extra_constraints.append(r.get_attr("width") == width)

        # We add some constraints that will be used to control the alignment of the shape
        # These will only drive the computation of the numbers above, which are used to create the SVG
        self.extra_constraints.append(r.get_attr("left") == r.get_attr("x"))
        self.extra_constraints.append(r.get_attr("right") == r.get_attr("left") + r.get_attr("width"))
        self.extra_constraints.append(r.get_attr("top") == r.get_attr("y"))
        self.extra_constraints.append(r.get_attr("bottom") == r.get_attr("top") + r.get_attr("height"))

        # Finally we give the shape back to the user
        return r
    

if __name__ == "__main__":
    main()

