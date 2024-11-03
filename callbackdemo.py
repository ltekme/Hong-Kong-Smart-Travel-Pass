def printNum(n2, callback):
    callback(n2)

def sN(n1, callback):
    print("sn", n1)
    callback(n1)

sN(1, printNum)