from decimal import Decimal

def efficiency(item):
    p,r,n,g,c=(Decimal(item[k]) for k in ("planned","runtime","total","good","ideal_seconds"))
    if p==0:return {**item,"availability":None,"performance":None,"quality":None,"oee":None,"status":"无计划"}
    a=r/p
    if r==0:
        return {**item,"availability":str(a),"performance":None,"quality":str(g/n) if n else None,"oee":"0" if n==0 else None,"status":"停机有产量" if n else "全停机"}
    if n==0:return {**item,"availability":str(a),"performance":"0","quality":None,"oee":"0","status":"零产量"}
    performance=c*n/(r*60);quality=g/n
    return {**item,"availability":str(a),"performance":str(performance),"quality":str(quality),"oee":str(c*g/(p*60)),"status":"超产" if performance>1 else "通过"}
