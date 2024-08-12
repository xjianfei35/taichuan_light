import logging
import time
import datetime
import json
import base64
from threading import Lock
from aiohttp import ClientSession
from secrets import token_hex
from urllib.request import quote
import json
from urllib.parse import urlencode
from ..devices.__init__ import device_selector
from .security import CloudSecurity, MeijuCloudSecurity, MSmartCloudSecurity, TaichuanAirSecurity
import asyncio
import aiohttp
import time
_LOGGER = logging.getLogger(__name__)

clouds = {
    "珠海U家": {
        "class_name": "UCloud",
        "api_url": "https://ucloud.taichuan.net",
    }
}

class TaichuanCloud:
    def __init__(
            self,
            session: ClientSession,
            username: str,
            password: str,
            api_url: str,
    ):
        self._username= username 
        self._password = password
        self._api_url = api_url
        self._session = session
        self._access_token=None
        self._access_token_type=None
        self._expire_in=0
        self._time_update_token=0
        self._scope=None
        

    def _make_general_data(self):
        return {}

    async def _api_request(self, method:str,endpoint: str, data, header=None) -> dict | None:
        url = self._api_url + endpoint
        response: dict = {"error": "invalid client"}
        _LOGGER.info(f"url:{url},data:{data},header:{header}") 
        async with asyncio.timeout(10):
            try:
                r = await self._session.request(method, url, headers=header, data=data, timeout=10)
                raw = await r.read()
                response = json.loads(raw)
            except TimeoutError:
                _LOGGER.error(f"api_request timeout!")
        _LOGGER.info(f"response[{response}]")
        return response

    async def login(self) -> bool:
        raise NotImplementedError()

    async def list_home(self) -> dict | None:
        return {1: "My home"}

    async def list_dev(self) -> dict:
        raise NotImplementedError()
    
    async def list_scene(self) -> dict:
        raise NotImplementedError()

    async def list_appliances(self, home_id) -> dict | None:
        raise NotImplementedError()

class UCloud(TaichuanCloud):
    def __init__(
            self,
            cloud_name: str,
            session: ClientSession,
            username: str,
            password: str,
    ):
        super().__init__(
            session=session,
            username=username,
            password=password,
            api_url=clouds[cloud_name]["api_url"]
        )
        self._header={}

    async def login(self) -> bool:
        data = {
            "client_id": "uhome.android",
            "client_secret": "123456",
            "grant_type": "password",
            "scope": "uhome",
            "username": self._username,
            "password": self._password 
        }
        
        data_json = json.dumps(data)
        jdata = f"[{data_json}]"
        data_dict = json.loads(data_json)
        dump_data = urlencode(data_dict,doseq=True)

        self._header.update({
            "Connection": "keep-alive",
            "Content-Type":"application/x-www-form-urlencoded"
        })
 
        if response := await self._api_request(
            "POST",
            endpoint="/connect/token",
            data=dump_data,
            header=self._header
        ):
            if "access_token" in response:
                self._access_token = response["access_token"]
                self._access_token_type = response["token_type"]
                self._expire_in = response["expires_in"] 
                self._scope = response["scope"]
                self._time_update_token = int(time.time())
                return True
            else:
                _LOGGER.error(f"login error,data[{data}]")
                return False

    async def list_dev(self) -> dict:
        devices ={} 
        self._header.update({
            "Content-Type":"application/x-www-form-urlencoded",
            "Authorization": self._access_token_type+" "+self._access_token
        })
        
        if response := await self._api_request(
            "GET",
            endpoint="/smarthome/api/v2/ctl/getDeviceSchemaList?num=C3201224000275&machineType=2003&timeout=6",
            data={},
            header=self._header
        ):
            if(response["code"]==0):
                devices_list = response["data"]["devices"]
                for pdev in devices_list:
                    device_id = int(pdev["id"],10)
                    device_type=pdev["devType"]
                    device_name=pdev["name"]
                    if(device_type==0x06):
                        dev = device_selector(
                            name = device_name,
                            device_id = device_id,
                            device_type= device_type
                        )
                        devices[device_id]=dev
            return devices

    async def list_scene(self) -> dict:
        scenes = {}
        self._header.update({
            "Content-Type":"application/x-www-form-urlencoded",
            "Authorization": self._access_token_type+" "+self._access_token
        })
        if response := await self._api_request(
            "GET",
            endpoint="/smarthome/api/v2/ctl/getSceneInfoList?machineType=2003&num=C3201224000275&timeout=10",
            data={},
            header=self._header
        ):
            if(response["code"]==0):
                scenes= response["data"]
                dev_list = scenes
        return scenes

    async def dev_opt(self,type:int,id:int,value: bool) -> bool:
        data = {
            "op": "replace",
            "path": "/switch",
            "value": value 
        }

        data_json = json.dumps(data)
        jdata = f"[{data_json}]"
        data_dict = json.loads(data_json)
        dump_data = urlencode(data_dict,doseq=True)
        
        self._header.update({
            "Content-Type":"application/json-patch+json;charset=UTF-8",
        })
        async with asyncio.timeout(10):
            try:
                if response :=await self._api_request(
                    "PATCH",
                    endpoint="/smarthome/api/v2/ctl/ctrlDevice?num=C3201224000275&machineType=2003&timeout=10"+f"&devType={type}"+f"&id={id}",
                    data=jdata,
                    header=self._header
                ):
                    if "code" in response:
                        if(response["code"]==0):
                            if(len(response["data"])==1):
                                if((response["data"][0] =="true" and value == True) or (response["data"][0]=="false" and value ==False)):
                                    return True
                    elif "exp" in response:
                        if(response["exp"]=="token expired"):
                            res = await self.login()
                        return False
                    else:
                        _LOGGER(f"dev_opt timeout!")
            except TimeoutError:
                _LOGGER.error(f"cloud.dev_opt timeout!")

    async def list_home(self):
        if response := await self._api_request(
            endpoint="/smarthome/api/v2/ctl/getDeviceSchemaList",
            data={}
        ):
            homes = {}
            for home in response["homeList"]:
                homes.update({
                    int(home["homegroupId"]): home["name"]
                })
            return homes
        return None

    async def get_device_info(self, device_id: int):
        devices = {}
        devices = self.list_dev()
        for device in devices:
            if(device_id == device.get("id")):
                device_info = {
                    "name": device.get("name"),
                    "type": device.get("type"),
                    "device_id": device.get("id"),
                    "events": device.get("events"),
                    "properties": device.get("properties")
                }
                return device_info

def get_taichuan_cloud(cloud_name: str, session: ClientSession, username: str, password: str) -> TaichuanCloud | None:
    cloud = None
    if cloud_name in clouds.keys():
        cloud = globals()[clouds[cloud_name]["class_name"]](
            cloud_name=cloud_name,
            session=session,
            username=username,
            password=password,
        )
    return cloud
