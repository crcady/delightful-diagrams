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
        # Helper functions cribbed from https://stackoverflow.com/questions/67043494/max-and-min-of-a-set-of-variables-in-z3py
        def max(vs):
            m = vs[0]
            for v in vs[1:]:
                m = z3.If(v > m, v, m)
            return m
        
        def min(vs):
            m = vs[0]
            for v in vs[1:]:
                m = z3.If(v < m, v, m)
            return m

        s = z3.Solver()
    
        for c in self.extra_constraints:
            s.add(c)

        min_left = min([shape.get_attr("left") for shape in self.elements])
        min_top = min([shape.get_attr("top") for shape in self.elements])
        max_right = max([shape.get_attr("right") for shape in self.elements])
        max_bottom = max([shape.get_attr("bottom") for shape in self.elements])

        s.add(min_left == 0)
        s.add(min_top == 0)
        s.add(z3.Int("doc__width") == max_right)
        s.add(z3.Int("doc__height") == max_bottom)        

        if s.check().r != z3.Z3_L_TRUE:
            print("Couldn't satisfy the constraints, aborting", file=sys.stderr)
            sys.exit(1)

        values: dict[str, int] = {}
        m = s.model()
        for d in m.decls():
            values[d.name()] = m[d].as_long()

        es = [e.render(values) for e in self.elements]

        vb = svg.ViewBoxSpec(0, 0, values["doc__width"], values["doc__height"])
        return svg.SVG(
            viewBox=vb,
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

