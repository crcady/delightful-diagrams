import main as dd

doc = dd.Document()

r = doc.newRect("square", x=2, y=2, width=100, height=100)
c = doc.newCircle("circle", cx=60, cy=60)

doc.require(r.width() == c.width())
#doc.require(r.right() == c.right())
#doc.require(r.top() == c.top())


print(doc.render())
