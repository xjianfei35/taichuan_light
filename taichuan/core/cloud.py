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
from .security import CloudSecurity, MeijuCloudSecurity, MSmartCloudSecurity, TaichuanAirSecurity

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
        

    def _make_general_data(self):
        return {}

    async def _api_request(self, Interface,endpoint: str, data: dict, header=None) -> dict | None:
        header = header or {}      
        url = self._api_url + endpoint
        data_dict = json.loads(json.dumps(data))
        dump_data = urlencode(data_dict,doseq=True)
        header.update({
            "content-type": "application/x-www-form-urlencoded",
            "Connection": "keep-alive",
        })

        if self._access_token is not None and self._access_token_type is not None:
            header.update({
                "Authorization": self._access_token_type+" "+self._access_token
            })
        response: dict = {"error": "invalid client"}
        data = {}
        _LOGGER.info(f"url[{url}],dump_data[{dump_data}],headers[{header}]")
        try:
            if(Interface == "POST"):
                async with self._session.post(url, headers=header, data=dump_data, timeout=10) as response:
                    data = json.loads(await response.text())
            elif(Interface == "GET"):
                async with  self._session.get(url, headers=header, data=dump_data, timeout=10) as response:
                    data = json.loads(await response.text())
            elif(Interface == "PATCH"):
                async with  self._session.patch(url, headers=header, data=dump_data, timeout=10) as response:
                    data = json.loads(await response.text())
            else:
                async with  self._session.put(url, headers=header, data=dump_data, timeout=10) as response:
                    data = json.loads(await response.text())
            _LOGGER.info(f"data[{data}]")
            return data
        except Exception as e:
            _LOGGER.warning(f"Taichuan cloud API error, url: {url}, data:{dump_data},error: {repr(e)}")
        
        return None

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

    async def login(self) -> bool:
        data = {
            "client_id": "uhome.android",
            "client_secret": "123456",
            "grant_type": "password",
            "scope": "uhome",
            "username": self._username,
            "password": self._password 
        }
        
        if response := await self._api_request(
            "POST",
            endpoint="/connect/token",
            data=data
        ):
            if(response["access_token"]!=""):
                self._access_token = response["access_token"]
                self._access_token_type = response["token_type"]
                self._expire_in = response["expires_in"] 
                self._scope = response["scope"]
                return True
            else:
                _LOGGER.error(f"login error,data[{data}]")
                return False

    async def list_dev(self) -> dict:
        devices = []
        if response := await self._api_request(
            "GET",
            endpoint="/smarthome/api/v2/ctl/getDeviceSchemaList?num=C3201224000275&machineType=2003&timeout=6",
            data={}
        ):
            devices = {} 
            if(response["code"]==0):
                devices_list = response["data"]["devices"]
                for pdev in devices_list:
                    device_id = int(pdev["id"],10)
                    devices[device_id] = pdev 
                return devices

    async def list_scene(self) -> dict:
        scenes = {}
        if response := await self._api_request(
            "GET",
            endpoint="/smarthome/api/v2/ctl/getSceneInfoList?machineType=2003&num=C3201224000275&timeout=10",
            data={}
        ):
            if(response["code"]==0):
                scenes= response["data"]
                dev_list = scenes
        return scenes

    async def dev_opt(self,type:int,id:int,value: bool) -> bool:
        if response :=await self._api_request(
            "PATCH",
            endpoint="https://ucloud.taichuan.net/smarthome/api/v2/ctl/ctrlDevice?num=C3201224000275&machineType=2003&timeout=10"+f"&devType={type}"+f"&id={id}",
            data={"op":"replace","path":"/switch","value":{value}}
        ):
            if(response["code"]==0):
                if(len(response["data"])==1):
                    if((response["data"][0] =="true" and value == True) or (response["data"][0]=="false" and value ==False)):
                        return True
            return False

    async def list_home(self):
        if response := await self._api_request(
            endpoint="https://ucloud.taichuan.net/smarthome/api/v2/ctl/getDeviceSchemaList",
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
            dev_list=None
        )
    return cloud
