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
        self._thread = threading.Thread(target=self.start_loop)
        self._thread.start()

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

    async def get_devices(self):
        """获取设备列表.

        Returns:
            dict: 设备字典，如果出错则返回空字典

        """
        try:
            self._devices = await self._ucloud.list_dev()
            if self._devices is None:
                _LOGGER.error("Failed to get devices list: API returned None")
                return {}
            return self._devices
        except Exception as e:
            _LOGGER.error(f"Error getting devices list: {str(e)}")
            return {}

    async def get_scenes(self):
        """获取场景列表.

        Returns:
            list: 场景列表

        """
        self._scenes = await self._ucloud.list_scene()
        return self._scenes

    async def reflesh_token(self):
        """刷新令牌."""
        await self.ucloud.login()

    async def dev_opt(self,type,id,value:bool):
        """_summary_.

        Args:
            type (_type_): _description_
            id (_type_): _description_
            value (bool): _description_

        """
        await self._ucloud.dev_opt(type,id,value)