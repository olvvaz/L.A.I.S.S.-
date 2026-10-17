import json

with open("position.json", "w") as f:
    json.dump({"pos": 25, "p1d": None, "p2d": None, "p3d": None}, f)

print("position.json (na placa) resetado para pos=25, presets limpos")
