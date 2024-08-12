from .taichuan.core.cloud import UCloud
import asyncio
import threading
import time
import logging
_LOGGER = logging.getLogger(__name__)
class Taichuanhub:
    def __init__(
       self,
       cloud: UCloud, 
    ):
        self._ucloud = cloud 
        #包含的场景
        self._devices = None 
        #包含的设备
        self._scenes = None 

        self._loop = asyncio.get_event_loop()
        self._thread = threading.Thread(target=self.start_loop())

    def start_loop(self):
        #  运行事件循环， loop以参数的形式传递进来运行
        asyncio.set_event_loop(self._loop)
            
    @property
    def loop(self):
        return self._loop 
    
    @property
    def ucloud(self):
        return self._ucloud

    @property 
    async def devices(self):
        self._devices = await self._ucloud.list_dev()
        return self._devices
    
    @property 
    async def scenes(self):
        self._scenes=await self._ucloud.list_scene()
        return self._scenes
    
    @property
    async def reflesh_token(self):
        await self.ucloud.login

    async def dev_opt(self,type,id,value:bool):
        await self._ucloud.dev_opt(type,id,value)