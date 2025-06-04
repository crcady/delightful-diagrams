import main as dd

doc = dd.Document()

r1 = doc.newRect("boss", fill="red", x=0, width=10, height=10, labels={"tier": 0})
r2 = doc.newRect(
    "middle-manager", x=0, fill="green", width=10, height=10, labels={"tier": 1}
)
r3 = doc.newRect("peon", fill="blue", x=0, width=10, height=10, labels={"tier": 2})

doc.when(lambda x, y: x.labels["tier"] > y.labels["tier"]).then(
    lambda x, y: x.bottom() <= y.top() - 5
)

print(doc.render())
