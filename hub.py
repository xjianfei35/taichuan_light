from .taichuan.core.cloud import UCloud
import asyncio
import threading
import time
import logging
_LOGGER = logging.getLogger(__name__)
class Taichuanhub:
    """_summary_."""

    def __init__(
       self,
       cloud: UCloud
    ):
        """_summary_.

        Args:
            cloud (UCloud): _description_

        """
        self._ucloud = cloud
        #包含的场景
        self._devices = None

        #包含的设备
        self._scenes = None

        self._loop = asyncio.get_event_loop()
        self._thread = threading.Thread(target=self.start_loop())

    def start_loop(self):
        #  运行事件循环， loop以参数的形式传递进来运行
        """

        """  # noqa: D419
        asyncio.set_event_loop(self._loop)
    @property
    def loop(self):
        """_summary_.

        Returns:
            _type_: _description_

        """
        return self._loop

    @property
    def ucloud(self):
        """_summary_.

        Returns:
            _type_: _description_

        """
        return self._ucloud

    @property 
    async def devices(self):
        """_summary_.

        Returns:
            _type_: _description_

        """
        self._devices = await self._ucloud.list_dev()
        return self._devices

    @property
    async def scenes(self):
        """_summary_.

        Returns:
            _type_: _description_

        """
        self._scenes=await self._ucloud.list_scene()
        return self._scenes

    @property
    async def reflesh_token(self):
        """_summary_."""
        await self.ucloud.login

    async def dev_opt(self,type,id,value:bool):
        """_summary_.

        Args:
            type (_type_): _description_
            id (_type_): _description_
            value (bool): _description_

        """
        await self._ucloud.dev_opt(type,id,value)