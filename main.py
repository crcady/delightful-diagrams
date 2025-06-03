from __future__ import annotations
import svg
import sys
import z3

def main():
    d = Document()
    r1 = d.newRect("r1", x=0, y=0, width=100, height=100)
    r2 = d.newRect("r2", x=100, y=0, width=100, height=100, fill="red")
    
    print(d.render())

class Rect:
    def __init__(self, document: Document, name: str, fill="white"):
        self.name = name
        self.document = document
        self.fill = fill

    def get_attr(self, attr_name: str) -> str:
        return self.name + "__" + attr_name

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

        if not s.check():
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
            self.extra_constraints.append(z3.Int(r.get_attr("x")) == x)
        if y is not None:
            self.extra_constraints.append(z3.Int(r.get_attr("y")) == y)
        if height is not None:
            self.extra_constraints.append(z3.Int(r.get_attr("height")) == height)
        if width is not None:
            self.extra_constraints.append(z3.Int(r.get_attr("width")) == width)

        # Finally we give the shape back to the user
        return r
    

if __name__ == "__main__":
    main()

