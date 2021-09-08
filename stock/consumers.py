import json
from channels.generic.websocket import AsyncWebsocketConsumer
from urllib.parse import parse_qs 
from asgiref.sync import async_to_sync,sync_to_async
from django_celery_beat.models import PeriodicTask,IntervalSchedule
from stock.models import *
import copy


class StockConsumer(AsyncWebsocketConsumer):
    @sync_to_async
    def addCelerybeat(self,stockpicker):
        task=PeriodicTask.objects.filter(name="every-12-second")
        if len(task)>0:
            task=task.first()
            args=json.loads(task.args)
            args=args[0]
            for x in stockpicker:
                if x not in args:
                    args.append(x)
            task.args=json.dumps([args])
            task.save()
        else:
            schedule,created=IntervalSchedule.objects.get_or_create(every=12,period=IntervalSchedule.SECONDS)
            task=PeriodicTask.objects.create(interval=schedule,name="every-12-second", task="stock.tasks.update_stock",args=json.dumps([stockpicker]))

    


    
    @sync_to_async
    def addToStock(self,stockpicker):
        user=self.scope["user"]
        for i in stockpicker:
            stock,created=stockDetail.objects.get_or_create(stock=i)
            stock.user.add(user)



    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'stock_%s' % self.room_name

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        query_params=parse_qs(self.scope['query_string'].decode())
        #print(query_params)#for print the query you select

        stockpicker=query_params['stockpicker']




        await self.addCelerybeat(stockpicker)
        
        await self.addToStock(stockpicker)

        await self.accept()

    @sync_to_async
    def helperFunc(self):
        user=self.scope["user"]
        stocks=stockDetail.objects.filter(user__id=user.id)
        task=PeriodicTask.objects.get(name="every-12-seconds")
        args=json.loads(task.args)
        args=args[0]
        for i in stocks:
            i.user.remove(user)
            if i.user.count()==0:
                args.remove(i.stock)
                i.delete()
        if args ==None:
            args=[]

        if len(args)==0:
            task.delete()
        else:
            task.args=json.dumps([args])
            task.save




    async def disconnect(self, close_code):

        await self.helperFunc()
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'update_stock',
                'message': message
            }
        )
    @sync_to_async
    def selectUserStockOnly(self):
        user=self.scope["user"]
        user_stocks=user.stockdetail_set.values_list('stock',flat=True)
        return list(user_stocks)

    # Receive message from room group
    async def send_update_stock(self, event):
        message = event['message']
        message=copy.copy(message)

        user_stocks= await self.selectUserStockOnly()

        keys= message.keys()
        for key in list(keys):
            if key in user_stocks:
                pass
            else:
                del message[key]

        # Send message to WebSocket
        await self.send(text_data=json.dumps(message))
