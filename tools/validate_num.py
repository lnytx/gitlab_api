

phone_nmber=['13660849971']
def validate_commit(num):
    for i in phone_nmber:
        if str(i)==str(num):
            return 1#验证通过
        else:
            return 0

if __name__=='__main__':
    flag = 1
    order = 1
    if flag and order:
        print("true")
    else:
        print("false")

