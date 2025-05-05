import math
import json

class Calculator():
    def __init__(self):
        self.value = 0
    
    def add(self,a,b):
        self.value = a+b

    def mult(self,a,b):
        self.value = a*b

    def sqrt(self,a):
        self.value = math.sqrt(a)

if __name__ == "__main__":
    with open('input.json', 'r') as file:
        data = json.load(file)
    calc=Calculator()
    for line in data:
        if line["operation"]=="add":
            calc.add(line["numbers"][0], line["numbers"][1])
        elif line["operation"]=="mult":
            calc.mult(line["numbers"][0], line["numbers"][1])
        elif line["operation"]=="sqrt":
            calc.sqrt(line["numbers"][0])
    print(calc.value)