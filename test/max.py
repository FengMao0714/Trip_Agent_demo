def Two_Max(a, b):
    """返回两个数中的较大值"""
    if a > b:
        return a
    elif a == b:
        return "两个数相等"
    else:
        return b
    
if __name__ == "__main__":
    num1 = 10
    num2 = 20
    result = Two_Max(num1, num2)
    print(f"{num1}和{num2}中的较大值是: {result}")