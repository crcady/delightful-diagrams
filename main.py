from __future__ import annotations
from inspect import signature
from typing import Any
import svg
import sys
import z3


def main():
    d = Document()
    next_left = 0
    next_top = 0
    for y in range(1, 16):
        for x in range(1, 16):
            if (x + y - 1) % 15 == 0:
                color = "purple"
            elif (x + y - 1) % 3 == 0:
                color = "red"
            elif (x + y - 1) % 5 == 0:
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


class Shape:
    def __init__(
        self, document: Document, name: str, fill="white", labels: dict[str, any] = {}
    ):
        self.name = name
        self.document = document
        self.fill = fill
        self.labels = labels

    def get_attr(self, attr_name: str) -> z3.ArithRef:
        return z3.Int(self.name + "__" + attr_name)

    def left(self):
        return self.get_attr("left")

    def right(self):
        return self.get_attr("right")

    def top(self):
        return self.get_attr("top")

    def bottom(self):
        return self.get_attr("bottom")

    def x(self):
        return self.get_attr("x")

    def y(self):
        return self.get_attr("y")

    def height(self):
        return self.get_attr("height")

    def width(self):
        return self.get_attr("width")

class Rect(Shape):
    def render(self, values: dict[str, int]) -> svg.Element:
        x = values[self.name + "__" + "x"]
        y = values[self.name + "__" + "y"]
        width = values[self.name + "__" + "width"]
        height = values[self.name + "__" + "height"]

        return svg.Rect(
            fill=self.fill,
            stroke_width=1,
            stroke="black",
            x=x,
            y=y,
            width=width,
            height=height,
        )
    

class Circle(Shape):
    def render(self, values: dict[str, int]) -> svg.Element:
        cx = values[self.name + "__" + "cx"]
        cy = values[self.name + "__" + "cy"]
        r = values[self.name + "__" + "r"]
        print(values, file=sys.stderr)

        return svg.Circle(
            fill=self.fill,
            stroke_width=1,
            stroke="black",
            cx=cx,
            cy=cy,
            r=r
        )

class Document:
    def __init__(self):
        self.elements: list[Rect] = []
        self.extra_constraints: list[z3.z3.BoolRef] = []
        self.deferred_constraints: list[DeferredConstraint] = []

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

        for dc in self.deferred_constraints:
            dc.invoke(self)

        for c in self.extra_constraints:
            s.add(c)

        min_left = min([shape.get_attr("left") for shape in self.elements])
        min_top = min([shape.get_attr("top") for shape in self.elements])
        max_right = max([shape.get_attr("right") for shape in self.elements])
        max_bottom = max([shape.get_attr("bottom") for shape in self.elements])

        s.add(min_left >= 0)
        s.add(min_top >= 0)
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

    def require(self, c):
        self.extra_constraints.append(c)

    def newRect(
        self,
        name: str,
        fill="white",
        x: int | None = None,
        y: int | None = None,
        height: int | None = None,
        width: int | None = None,
        labels: dict[str, Any] = {},
    ) -> Rect:
        # First we need to get the new shape object
        r = Rect(self, name, fill=fill, labels=labels)

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
        self.require(r.left() == r.x())
        self.require(r.right() == r.left() + r.width())
        self.require(r.top() == r.y())
        self.require(r.bottom() == r.top() + r.height())

        # Finally we give the shape back to the user
        return r
    
    def newCircle(
            self,
            name: str,
            fill="white",
            cx: int | None = None,
            cy: int | None = None,
            r: int | None = None,
            labels: dict[str, Any] = {},
    ) -> Circle:
        # First we need to get the new shape object
        c = Circle(self, name, fill=fill, labels=labels)

        # Add that object to our list of objects in the document
        self.elements.append(c)

        # We need to handle the (possibly impossible to satisfy) concrete constraints
        if cx is not None:
            self.extra_constraints.append(c.get_attr("cx") == cx)
        if cy is not None:
            self.extra_constraints.append(c.get_attr("cy") == cy)
        if r is not None:
            self.extra_constraints.append(c.get_attr("r") == r)

        # We add some constraints that will be used to control the alignment of the shape
        # These will only drive the computation of the numbers above, which are used to create the SVG
        self.require(c.left() == c.x())
        self.require(c.right() == c.left() + c.width())
        self.require(c.top() == c.y())
        self.require(c.bottom() == c.top() + c.height())

        self.require(c.width() == c.height())
        
        self.require(c.left() == c.get_attr("cx") - c.get_attr("r"))
        self.require(c.top() == c.get_attr("cy") - c.get_attr("r"))
        self.require(c.right() == c.get_attr("cx") + c.get_attr("r"))
        self.require(c.bottom() == c.get_attr("cy") + c.get_attr("r"))

        # Finally we give the shape back to the user
        return c


    def when(self, test):
        dc = DeferredConstraint(test)
        self.deferred_constraints.append(dc)
        return dc


class DeferredConstraint:
    def __init__(self, test):
        self.test = test
        self.then_func = None
        self.other_func = None

    def then(self, then_func):
        self.then_func = then_func
        return self

    def otherwise(self, other_func):
        self.other_func = other_func
        return self

    def invoke(self, doc: Document):
        match len(signature(self.test).parameters):
            case 1:
                for shape in doc.elements:
                    res = self.test(shape)
                    if res:
                        if self.then_func is not None:
                            c = self.then_func(shape)
                            doc.require(c)
                    else:
                        if self.other_func is not None:
                            c = self.other_func(shape)
                            doc.require(c)

            case 2:
                for shape1 in doc.elements:
                    for shape2 in doc.elements:
                        if shape1 is shape2:
                            continue

                        res = self.test(shape1, shape2)
                        if res:
                            if self.then_func is not None:
                                c = self.then_func(shape1, shape2)
                                doc.require(c)
                        else:
                            if self.other_func is not None:
                                c = self.other_func(shape1, shape2)
                                doc.require(c)


if __name__ == "__main__":
    main()
