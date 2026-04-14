def ercimi(num: int) -> bool:
    """判断一个数是不是2的幂次方"""
    if num <= 0:
        return False
    return (num & (num - 1 )) == 0

if __name__ == "__main__":
    print(ercimi(1))  # True
    print(ercimi(5))  # False
    print(ercimi(8))  # True
    print(5 & 4)  # 4
    print(8 & 7)  # 0