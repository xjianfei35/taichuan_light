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

default_keys = {
    99: {
        "token": "ee755a84a115703768bcc7c6c13d3d629aa416f1e2fd798beb9f78cbb1381d09"
                 "1cc245d7b063aad2a900e5b498fbd936c811f5d504b2e656d4f33b3bbc6d1da3",
        "key": "ed37bd31558a4b039aaf4e7a7a59aa7a75fd9101682045f69baf45d28380ae5c"
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
        '''
        self._device_id = CloudSecurity.get_deviceid(account)
        self._session = session
        self._security = security
        self._api_lock = Lock()
        self._app_id = app_id
        self._app_key = app_key
        '''
        self._username= username 
        self._password = password
        self._api_url = api_url
        self._access_token = None
        self._expire_in = None
        self._access_token_type = None 
        self._session = session
        

    def _make_general_data(self):
        return {}

    async def _api_request(self, Interface,endpoint: str, data: dict, header=None) -> dict | None:
        header = header or {}      
        url = self._api_url + endpoint
        #dump_data = json.load(json.dump(data))
        data_dict = json.loads(json.dumps(data))
        dump_data = urlencode(data_dict,doseq=True)
        #sign = self._security.sign("", dump_data, random)
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
        _LOGGER.debug(f"url[{url}],dump_data[{dump_data}],headers[{header}]")
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
            _LOGGER.debug(f"data[{data}]")
            return data
        except Exception as e:
            _LOGGER.warning(f"Taichuan cloud API error, url: {url}, data:{dump_data},error: {repr(e)}")
        
        return None

    async def _get_login_id(self) -> str | None:
        data = self._make_general_data()
        data.update({
            "loginAccount": f"{self._account}"
        })

        if response := await self._api_request(
            endpoint="/v1/user/login/id/get",
            data=data
        ):
            return response.get("loginId")
        return None

    async def login(self) -> bool:
        raise NotImplementedError()

    async def get_keys(self, appliance_id: int):
        result = {}
        for method in [1, 2]:
            udp_id = self._security.get_udp_id(appliance_id, method)
            data = self._make_general_data()
            data.update({
                "udpid": udp_id
            })
            response = await self._api_request(
                endpoint="/v1/iot/secure/getToken",
                data=data
            )
            if response and "tokenlist" in response:
                for token in response["tokenlist"]:
                    if token["udpId"] == udp_id:
                        result[method] = {
                            "token": token["token"].lower(),
                            "key": token["key"].lower()
                        }
        result.update(default_keys)
        return result

    async def list_home(self) -> dict | None:
        return {1: "My home"}

    async def list_dev(self) -> dict:
        raise NotImplementedError()
    
    async def list_scene(self) -> dict:
        raise NotImplementedError()

    async def list_appliances(self, home_id) -> dict | None:
        raise NotImplementedError()

    async def get_device_info(self, device_id: int):
        if response := await self.list_appliances(home_id=None):
            if device_id in response.keys():
                return response[device_id]
        return None

    async def download_lua(
            self, path: str,
            device_type: int,
            sn: str,
            model_number: str | None,
            manufacturer_code: str = "0000",
    ):
        raise NotImplementedError()


class UCloud(TaichuanCloud):
    def __init__(
            self,
            cloud_name: str,
            session: ClientSession,
            username: str,
            password: str,
            dev_list
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

    async def list_appliances(self, home_id) -> dict | None:
        data = {
            "homegroupId": home_id
        }

        if response := await self._api_request(
            endpoint="/v1/appliance/home/list/get",
            data=data
        ):
            appliances = {}
            for home in response.get("homeList") or []:
                for room in home.get("roomList") or []:
                    for appliance in room.get("applianceList"):
                        try:
                            model_number = int(appliance.get("modelNumber", 0))
                        except ValueError:
                            model_number = 0
                        device_info = {
                            "name": appliance.get("name"),
                            "type": int(appliance.get("type"), 16),
                            "sn": self._security.aes_decrypt(appliance.get("sn")) if appliance.get("sn") else "",
                            "sn8": appliance.get("sn8", "00000000"),
                            "model_number": model_number,
                            "manufacturer_code":appliance.get("enterpriseCode", "0000"),
                            "model": appliance.get("productModel"),
                            "online": appliance.get("onlineStatus") == "1",
                        }
                        if device_info.get("sn8") is None or len(device_info.get("sn8")) == 0:
                            device_info["sn8"] = "00000000"
                        if device_info.get("model") is None or len(device_info.get("model")) == 0:
                            device_info["model"] = device_info["sn8"]
                        appliances[int(appliance["applianceCode"])] = device_info
            return appliances
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
