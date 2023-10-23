from pydantic import BaseModel, Field


class UserModel(BaseModel):
    vk_id: int = Field(...)
    first_name: str = Field(...)
    last_name: str = Field(...)
    group_name: str = Field(...)
    group_url: str = Field(...)
    is_received_message: bool = Field(default=False)


class AccountModel(BaseModel):
    login: str = Field(...)
    password: str = Field(...)
    is_blocked: bool = Field(default=False)
    access_token: str = Field(default='')

    proxy_ip: str = Field(...)
    proxy_port: str = Field(...)
    proxy_login: str = Field(...)
    proxy_pass: str = Field(...)
    messages_written: int = Field(default=0)


class GroupInfoSubModule(BaseModel):
    groupName: str
    groupUrl: str
    usersAmount: int


class InfoModel(BaseModel):
    last_cache_dump_date: str
    # groups_info: GroupInfoSubModule
    # total_user_amount: int

