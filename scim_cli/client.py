import asyncio
from typing import Dict
from typing import List
from typing import Optional
from typing import Type
from typing import TypeVar
from typing import Union

from aiohttp import ClientSession
from pydantic import ValidationError
from pydantic_scim2 import Error
from pydantic_scim2 import Group
from pydantic_scim2 import ListResponse
from pydantic_scim2 import PatchOp
from pydantic_scim2 import Resource
from pydantic_scim2 import User
from pydantic_scim2.rfc7644.search_request import SortOrder

# TODO: Force AllResource to be a union of subclasses of Resource
AllResources = TypeVar("AllResources")

# TODO: Force AnyResource to be part of AllResources
AnyResource = TypeVar("AnyResource", bound=Resource)

BASE_HEADERS = {
    "Accept": "application/scim+json",
    "Content-Type": "application/scim+json",
}


class SCIMClient[AllResources]:
    def __init__(
        self,
        server: str,
        session: ClientSession,
    ):
        self.session = session
        self.server = server

    async def create(self, resource: AnyResource) -> Union[AnyResource, Error]: ...

    async def query(
        self,
        resource_type: Optional[Type] = None,
        id: Optional[str] = None,
        attributes: Optional[List[str]] = None,
        excluded_attributes: Optional[List[str]] = None,
        filter: Optional[str] = None,
        sort_by: Optional[str] = None,
        sort_order: Optional[SortOrder] = None,
        start_index: Optional[int] = None,
        count: Optional[int] = None,
    ) -> Union[
        AnyResource, ListResponse[AnyResource], ListResponse[AllResources], Error
    ]:
        if not resource_type:
            url = self.server
            expected_type = ListResponse[AllResources]

        elif not id:
            url = f"{self.server}/{resource_type.__name__}s"
            expected_type = ListResponse[resource_type]

        else:
            url = f"{self.server}/{resource_type.__name__}s/{id}"
            expected_type = resource_type

        async with self.session.get(url) as response:
            json_body = await response.json()
            try:
                return Error.model_validate(json_body)
            except ValidationError:
                return expected_type.model_validate(json_body)

    async def delete(self, resource_type: Type, id: str) -> Optional[Error]: ...

    async def replace(self, resource: AnyResource) -> Union[AnyResource, Error]: ...

    async def modify(
        self, resource: AnyResource, op: PatchOp
    ) -> Optional[AnyResource]: ...


async def main():
    server = "http://synapse.localhost:8008/_matrix/client/unstable/coop.yaal/scim"
    token = "syt_YWRtaW4_fecFwLJiMlSIbqAYMlEZ_2SGLeE"
    headers = {**BASE_HEADERS, "Authorization": f"Bearer {token}"}

    async with ClientSession(headers=headers) as session:
        client = SCIMClient[Union[User, Group]](server, session)
        id = "@admin:synapse.localhost"
        user = await client.query(User, id)
        print(user)


asyncio.run(main())
