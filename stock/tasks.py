from celery import shared_task
from yahoo_fin.stock_info import *
from django.shortcuts import render,HttpResponse
import asyncio
import queue
from threading import Thread
import simplejson as json

from channels.layers import get_channel_layer

@shared_task(bind = True)
def update_stock(self,stockpicker):
    data={}
    available_stocks=tickers_nifty50()
    for i in stockpicker:
        if i in available_stocks:
          pass
        else:
            return HttpResponse('Error')

   
    n_threads=len(stockpicker)
    thread_list=[]
    que=queue.Queue()
    for i in range(n_threads):
        thread=Thread(target =lambda q,arg1: q.put({stockpicker[i]:json.loads(json.dumps(get_quote_table(arg1),ignore_nan=True))}),args =(que,stockpicker[i]))
        thread_list.append(thread)
        thread_list[i].start()

    for thread in thread_list:
        thread.join()

    while not que.empty():
        result=que.get()
        data.update(result)

    channel_layer= get_channel_layer()
    loop=asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(channel_layer.group_send("stock_track",{
        'type':'send_update_stock',
        'message':data,
    }))



    return 'done'

    