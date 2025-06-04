import main as dd

doc = dd.Document()

rect = doc.newRect("my-rectangle", x=0, y=0, width=200, height=100)
rect2 = doc.newRect("my-second-rectangle", fill="red")

doc.require(rect2.left() == rect.left() + 10)
doc.require(rect2.right() == rect.right() - 10)
doc.require(rect2.top() == rect.top() + 10)
doc.require(rect2.bottom() == rect.bottom() - 10)

print(doc.render())
