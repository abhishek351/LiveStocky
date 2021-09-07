from django.shortcuts import render
from yahoo_fin.stock_info import *

import queue
from threading import Thread

# Create your views here.
def stockpicker(request):
    allstocks=tickers_nifty50()
   
    return render(request,"stockpicker.html",{'allstocks':allstocks})
def about(request):
    
    return render(request,"about.html",)

def stocktracker(request):
    stockpicker= request.GET.getlist('stockpicker')
    stockshare=str(stockpicker)[1:-1]
  
    
    print(stockpicker)
   
    data={}
    n_threads=len(stockpicker)
    thread_list=[]
    que=queue.Queue()
    for i in range(n_threads):
        thread=Thread(target =lambda q,arg1: q.put({stockpicker[i]:get_quote_table(arg1)}),args =(que,stockpicker[i]))
        thread_list.append(thread)
        thread_list[i].start()

    for thread in thread_list:
        thread.join()

    while not que.empty():
        result=que.get()
        data.update(result)

    print(data)

    


   
    return render(request,"stocktracker.html",{'data':data,'room_name':'track','selectedstock':stockshare})