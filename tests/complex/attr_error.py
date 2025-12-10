class Calculator:
    def __init__(self, value):
        self.value = value

calc = Calculator(10)
print(calc.double())  # 错误：Calculator没有double方法