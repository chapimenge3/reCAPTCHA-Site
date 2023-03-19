from pydantic import BaseModel
from typing import Union 


class TelegramWebhook(BaseModel):
    update_id: int
    message: Union[dict, None] = None
    edited_message: Union[dict, None] = None
    channel_post: Union[dict, None] = None
    edited_channel_post: Union[dict, None] = None
    inline_query: Union[dict, None] = None
    chosen_inline_result: Union[dict, None] = None
    callback_query: Union[dict, None] = None
    shipping_query: Union[dict, None] = None
    pre_checkout_query: Union[dict, None] = None
    poll: Union[dict, None] = None
    poll_answer: Union[dict, None] = None
    my_chat_member: Union[dict, None] = None
    chat_member: Union[dict, None] = None
    chat_join_request: Union[dict, None] = None


    def to_json(self):
        '''
        Returns a JSON representation of the model
        '''
        data = {}
        for key, value in self.__dict__.items():
            if key.startswith('_'):
                continue
            if value is None:
                continue
            data[key] = value
        
        return data

class VerifyCapthca(BaseModel):
    code: str
    response: str

