import logging
import time
import datetime
import json
import base64
from threading import Lock
from aiohttp import ClientSession
from secrets import token_hex
from urllib.request import quote
from .security import CloudSecurity, MeijuCloudSecurity, MSmartCloudSecurity, TaichuanAirSecurity

_LOGGER = logging.getLogger(__name__)

clouds = {
    "珠海U家": {
        "class_name": "UCloud",
        "app_id": "900",
        "app_key": "46579c15",
        "login_key": "ad0ee21d48a64bf49f4fb583ab76e799",
        "iot_key": bytes.fromhex(format(9795516279659324117647275084689641883661667, 'x')).decode(),
        "hmac_key": bytes.fromhex(format(117390035944627627450677220413733956185864939010425, 'x')).decode(),
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
            #session: ClientSession,
            #security: CloudSecurity,
            #app_id: str,
            client_id: str,
            grand_type: str,
            #app_key: str,
            username: str,
            scope: str,
            password: str,
            api_url: str,
            bearer_token: str
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
        self._scope = scope 

    def _make_general_data(self):
        return {}

    async def _api_request(self, Interface,endpoint: str, data: dict, header=None) -> dict | None:
        header = header or {}
        if not data.get("client_id"):
            data.update({
                "reqId": "uhome.android" 
            })
        if not data.get("client_secret"):
            data.update({
                "client_secret": "123456"
            })

        if not data.get("grant_type"):
            data.update({
                "grant_type": "password"
            })
        
        if not data.get("scope"):
            data.update({
                "scope": "client_id=uhome.android"
            })

        if not date.get("username"):
            date.update({
                "username": "17375830293"
            })
        if not date.get("password"):
            data.update({
                "password": quote(_password)
            })
        
        url = self._api_url + endpoint
        dump_data = json.dumps(data)
        #sign = self._security.sign("", dump_data, random)
        header.update({
            "content-type": "application/x-www-form-urlencoded",
            "Connection": "keep-alive",
        })

        if self._access_token is not None:
            header.update({
                "Authorization": self._access_token_type+" "+self._access_token
            })
        response: dict = {"error": "invalid client"}
        try:
            r = await self._session.request(Interface, url, headers=header, data=dump_data, timeout=10)
            raw = await r.read()
            _LOGGER.info(f"Taichuan cloud API url: {url}, data: {data}, response: {raw}")
        except Exception as e:
            _LOGGER.warning(f"Taichuan cloud API error, url: {url}, error: {repr(e)}")
        
        if int(response["code"]) == 0 and "data" in response:
            return response["data"]
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

    async def list_dev(self)  ->dict | None:
        raise NotImplementedError();

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
            deviceNum: str,
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
            "scope": "client_id=uhome.android",
            "username": username,
            "password": quote(password),
        }
        
        if response := await self._api_request(
            "POST",
            endpoint="/system/token",
            data=data
        ):
        #self._access_token = response["mdata"]["accessToken"]
        #获取bearer token
            _LOGGER.info(f"response[{response}]")
            if(response["access_token"]!=""):
                self._access_token = response["access_token"]
                self._access_token_type = response["token_type"]
                self._expire_in = response["expire_in"] 
                self._scope = response["scope"]
                _LOGGER.info(f"response:[{response}]")
                return True
            else:
                _LOGGER.error(f"login error,endpoint[{endpoint}],data[{data}]")
                return False

    async def list_dev(self):
        devices = {}
        if response := await self._api_request(
            "GET",
            endpoint="/smarthome/api/v2/ctl/getDeviceSchemaList?num=C3201224000275&machineType=2003&timeout=6",
            data={}
        ):
            if(response["code"]==0):
                devices = response["data"]["devices"]
        return devices
    async def list_scene(self):
        scenes = {}
        if response := await self._api_request(
            "GET",
            endpoint="/smarthome/api/v2/ctl/getSceneInfoList?machineType=2003&num=C3201224000275&timeout=10",
            data={}
        ):
            if(response["code"]==0):
                scenes = response["data"]
        return scenes

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
        data = {
            "applianceCode": device_id
        }
        if response := await self._api_request(
            endpoint="/v1/appliance/info/get",
            data=data
        ):
            try:
                model_number = int(response.get("modelNumber", 0))
            except ValueError:
                model_number = 0
            device_info = {
                "name": response.get("name"),
                "type": int(response.get("type"), 16),
                "sn": self._security.aes_decrypt(response.get("sn")) if response.get("sn") else "",
                "sn8": response.get("sn8", "00000000"),
                "model_number": model_number,
                "manufacturer_code": response.get("enterpriseCode", "0000"),
                "model": response.get("productModel"),
                "online": response.get("onlineStatus") == "1",
            }
            if device_info.get("sn8") is None or len(device_info.get("sn8")) == 0:
                device_info["sn8"] = "00000000"
            if device_info.get("model") is None or len(device_info.get("model")) == 0:
                device_info["model"] = device_info["sn8"]
            return device_info
        return None

    async def download_lua(
            self, path: str,
            device_type: int,
            sn: str,
            model_number: str | None,
            manufacturer_code: str = "0000",
    ):
        data = {
            "applianceSn": sn,
            "applianceType": "0x%02X" % device_type,
            "applianceMFCode": manufacturer_code,
            'version': "0",
            "iotAppId": self._app_id
        }
        fnm = None
        if response := await self._api_request(
            endpoint="/v1/appliance/protocol/lua/luaGet",
            data=data
        ):
            res = await self._session.get(response["url"])
            if res.status == 200:
                lua = await res.text()
                if lua:
                    stream = ('local bit = require "bit"\n' +
                              self._security.aes_decrypt_with_fixed_key(lua))
                    stream = stream.replace("\r\n", "\n")
                    fnm = f"{path}/{response['fileName']}"
                    with open(fnm, "w") as fp:
                        fp.write(stream)
        return fnm

'''
class MSmartHomeCloud(TaichuanCloud):
    def __init__(
            self,
            cloud_name: str,
            session: ClientSession,
            account: str,
            password: str,
    ):
        super().__init__(
            session=session,
            security=MSmartCloudSecurity(
                login_key=clouds[cloud_name]["app_key"],
                iot_key=clouds[cloud_name]["iot_key"],
                hmac_key=clouds[cloud_name]["hmac_key"],
            ),
            app_id=clouds[cloud_name]["app_id"],
            app_key=clouds[cloud_name]["app_key"],
            account=account,
            password=password,
            api_url=clouds[cloud_name]["api_url"]
        )
        self._auth_base = base64.b64encode(
            f"{self._app_key}:{clouds['MSmartHome']['iot_key']}".encode("ascii")
        ).decode("ascii")

    def _make_general_data(self):
        return {
            # "appVersion": self.APP_VERSION,
            "src": self._app_id,
            "format": "2",
            "stamp": datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
            "platformId": "1",
            "deviceId": self._device_id,
            "reqId": token_hex(16),
            "uid": self._uid,
            "clientType": "1",
            "appId": self._app_id
        }

    async def _api_request(self, endpoint: str, data: dict, header=None) -> dict | None:
        header = header or {}
        header.update({
            "x-recipe-app": self._app_id,
            "authorization": f"Basic {self._auth_base}"
        })

        return await super()._api_request(endpoint, data, header)

    async def _re_route(self):
        data = self._make_general_data()
        data.update({
            "userType": "0",
            "userName": f"{self._account}"
        })
        if response := await self._api_request(
            endpoint="/v1/multicloud/platform/user/route",
            data=data
        ):
            if api_url := response.get("masUrl"):
                self._api_url = api_url

    async def login(self) -> bool:
        await self._re_route()
        if login_id := await self._get_login_id():
            self._login_id = login_id
            iot_data = self._make_general_data()
            iot_data.pop("uid")
            stamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            iot_data.update({
                "iampwd": self._security.encrypt_iam_password(self._login_id, self._password),
                "loginAccount": self._account,
                "password": self._security.encrypt_password(self._login_id, self._password),
                "stamp": stamp
            })
            data = {
                "iotData": iot_data,
                "data": {
                    "appKey": self._app_key,
                    "deviceId": self._device_id,
                    "platform": "2"
                },
                "stamp": stamp
            }
            if response := await self._api_request(
                endpoint="/mj/user/login",
                data=data
            ):
                self._uid = response["uid"]
                self._access_token = response["mdata"]["accessToken"]
                self._security.set_aes_keys(response["accessToken"], response["randomData"])
                return True
        return False

    async def list_appliances(self, home_id) -> dict | None:
        data = self._make_general_data()
        if response := await self._api_request(
            endpoint="/v1/appliance/user/list/get",
            data=data
        ):
            appliances = {}
            for appliance in response["list"]:
                try:
                    model_number = int(appliance.get("modelNumber", 0))
                except ValueError:
                    model_number = 0
                device_info = {
                    "name": appliance.get("name"),
                    "type": int(appliance.get("type"), 16),
                    "sn": self._security.aes_decrypt(appliance.get("sn")) if appliance.get("sn") else "",
                    "sn8": "",
                    "model_number": model_number,
                    "manufacturer_code":appliance.get("enterpriseCode", "0000"),
                    "model": "",
                    "online": appliance.get("onlineStatus") == "1",
                }
                device_info["sn8"] = device_info.get("sn")[9:17] if len(device_info["sn"]) > 17 else ""
                device_info["model"] = device_info.get("sn8")
                appliances[int(appliance["id"])] = device_info
            return appliances
        return None

    async def download_lua(
        self, path: str,
        device_type: int,
        sn: str,
        model_number: str | None,
        manufacturer_code: str = "0000",
    ):
        data = {
            "clientType": "1",
            "appId": self._app_id,
            "format": "2",
            "deviceId": self._device_id,
            "iotAppId": self._app_id,
            "applianceMFCode": manufacturer_code,
            "applianceType": "0x%02X" % device_type,
            "modelNumber": model_number,
            "applianceSn": self._security.aes_encrypt_with_fixed_key(sn.encode("ascii")).hex(),
            "version": "0",
            "encryptedType ": "2"
        }
        fnm = None
        if response := await self._api_request(
            endpoint="/v2/luaEncryption/luaGet",
            data=data
        ):
            res = await self._session.get(response["url"])
            if res.status == 200:
                lua = await res.text()
                if lua:
                    stream = ('local bit = require "bit"\n' +
                              self._security.aes_decrypt_with_fixed_key(lua))
                    stream = stream.replace("\r\n", "\n")
                    fnm = f"{path}/{response['fileName']}"
                    with open(fnm, "w") as fp:
                        fp.write(stream)
        return fnm


class TaichuanAirCloud(TaichuanCloud):
    def __init__(
            self,
            cloud_name: str,
            session: ClientSession,
            account: str,
            password: str,
    ):
        super().__init__(
            session=session,
            security=TaichuanAirSecurity(
                login_key=clouds[cloud_name]["app_key"]
            ),
            app_id=clouds[cloud_name]["app_id"],
            app_key=clouds[cloud_name]["app_key"],
            account=account,
            password=password,
            api_url=clouds[cloud_name]["api_url"]
        )
        self._session_id = None

    def _make_general_data(self):
        data = {
            "src": self._app_id,
            "format": "2",
            "stamp": datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
            "deviceId": self._device_id,
            "reqId": token_hex(16),
            "clientType": "1",
            "appId": self._app_id
        }
        if self._session_id is not None:
            data.update({
                "sessionId": self._session_id
            })
        return data

    async def _api_request(self, endpoint: str, data: dict, header=None) -> dict | None:
        header = header or {}
        if not data.get("reqId"):
            data.update({
                "reqId": token_hex(16)
            })
        if not data.get("stamp"):
            data.update({
                "stamp":  datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            })
        url = self._api_url + endpoint

        sign = self._security.sign(url, data, "")
        data.update({
            "sign": sign
        })
        if self._uid is not None:
            header.update({
                "uid": self._uid
            })
        if self._access_token is not None:
            header.update({
                "accessToken": self._access_token
            })
        response: dict = {"code": -1}
        for i in range(0, 3):
            try:
                with self._api_lock:
                    r = await self._session.request("POST", url, headers=header, data=data, timeout=10)
                    raw = await r.read()
                    _LOGGER.info(f"Taichuan cloud API url: {url}, data: {data}, response: {raw}")
                    response = json.loads(raw)
                    break
            except Exception as e:
                _LOGGER.warning(f"Taichuan cloud API error, url: {url}, error: {repr(e)}")
        if int(response["errorCode"]) == 0 and "result" in response:
            return response["result"]
        return None

    async def login(self) -> bool:
        if login_id := await self._get_login_id():
            self._login_id = login_id
            data = self._make_general_data()
            data.update({
                "loginAccount": self._account,
                "password": self._security.encrypt_password(self._login_id, self._password),
            })
            if response := await self._api_request(
                    endpoint="/v1/user/login",
                    data=data
            ):
                self._access_token = response["accessToken"]
                self._uid = response["userId"]
                self._session_id = response["sessionId"]
                return True
        return False

    async def list_appliances(self, home_id) -> dict | None:
        data = self._make_general_data()
        if response := await self._api_request(
            endpoint="/v1/appliance/user/list/get",
            data=data
        ):
            appliances = {}
            for appliance in response["list"]:
                try:
                    model_number = int(appliance.get("modelNumber", 0))
                except ValueError:
                    model_number = 0
                device_info = {
                    "name": appliance.get("name"),
                    "type": int(appliance.get("type"), 16),
                    "sn": appliance.get("sn"),
                    "sn8": "",
                    "model_number": model_number,
                    "manufacturer_code":appliance.get("enterpriseCode", "0000"),
                    "model": "",
                    "online": appliance.get("onlineStatus") == "1",
                }
                device_info["sn8"] = device_info.get("sn")[9:17] if len(device_info["sn"]) > 17 else ""
                device_info["model"] = device_info.get("sn8")
                appliances[int(appliance["id"])] = device_info
            return appliances
        return None
'''

def get_taichuan_cloud(cloud_name: str, session: ClientSession, account: str, password: str) -> TaichuanCloud | None:
    cloud = None
    if cloud_name in clouds.keys():
        cloud = globals()[clouds[cloud_name]["class_name"]](
            cloud_name=cloud_name,
            session=session,
            account=account,
            password=password
        )
    return cloud
