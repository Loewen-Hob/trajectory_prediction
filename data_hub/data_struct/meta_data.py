from enum import Enum, IntEnum, EnumMeta


# def getattribute(self, item: str):
#     print('HubMetaClass get_attr', item)
#     res = object().__getattribute__(item)
#     if not item.startswith('_'):
#         res.__hash__ = lambda x: hash(item)
#     # if item.startswith('_'):
#     #     return res
#     # if res is ...:
#     #     cls = self.__annotations__[item]
#     #     cls.__hash__ = lambda x: hash(item)
#     #     if issubclass(cls, HubIntEnum):
#     #         return cls
#     return res


class HubMetaClass(type):
    def __eq__(self, other):
        if other is ...:
            return True
        if hasattr(other, "__name__"):
            return self.__name__ == other.__name__
        else:
            return False
    __hash__ = object.__hash__


class HubEnumMeta(EnumMeta, HubMetaClass):
    pass


class HubIntEnum(IntEnum, metaclass=HubEnumMeta):
    pass


class HubMetaData(metaclass=HubMetaClass):
    def _update_from_dict(self, data_dict):
        """ 用于内部数据转换 """
        for k, v in data_dict.items():
            if hasattr(self, k):
                data = getattr(self, k)
                anno_type = self.__annotations__.get(k, None)
                if anno_type is None:   # 如果没有注释类型，就直接传
                    setattr(self, k, v)
                else:
                    setattr(self, k, self.__decode_data(anno_type, v, data))
            else:
                raise Exception(f'key {k} fot found in MetaData definition')
        return self

    def __decode_data(self, anno_type, value, pre_value=...):
        if issubclass(anno_type, HubMetaData):
            result = anno_type() if pre_value == ... else pre_value
            result: HubMetaData
            result._update_from_dict(value)
        elif hasattr(anno_type, '__origin__') and anno_type.__origin__ in (list, set, tuple):
            arg_type = anno_type.__args__[0]  # 只输入1个类型，暂时不支持多类型校对
            result: list = [self.__decode_data(arg_type, v) for v in value]
        elif hasattr(anno_type, '__origin__') and anno_type.__origin__ in (dict,):
            args = anno_type.__args__[0]
            if isinstance(args, slice):
                k_type, v_type = args.start, args.stop  # 对应dict[int:str]的注释方式
            else:
                k_type, v_type = anno_type.__args__[0], anno_type.__args__[1]  # 对应dict[int,str]的注释方式
            result: dict = {k_type(k): self.__decode_data(v_type, v, pre_value.get(k, ...)) for k, v in value.items()}
        else:
            result = anno_type(value)
        return result

    def __encode_data(self, value):
        if value == ...:
            result = value  # todo 这里默认参数待和前端确认，目前是 Ellipsis
        elif isinstance(value, Enum):
            result = value.value
        elif isinstance(value, HubMetaData):
            result = value._trans2dict()
        elif type(value) in (list, set, tuple):
            result = [self.__encode_data(v) for v in value]
        elif isinstance(value, dict):
            result = {k: self.__encode_data(v) for k, v in value.items()}
        else:
            result = value
        return result

    def _trans2dict(self):
        """ 用于内部数据转换 """
        result = {}
        for k, v in vars(self).items():
            if k.startswith('_') or k == ...:  # 内部数据和缺失数据不存
                continue
            result[k] = self.__encode_data(v)
        return result

    def __repr__(self):
        return '{}({})'.format(self.__class__.__name__, str(vars(self)))

    def __getattribute__(self, item):
        res = super(HubMetaData, self).__getattribute__(item)
        if item.startswith('_'):
            return res
        if res == ...:
            cls = self.__annotations__[item]
            if issubclass(cls, HubIntEnum):
                return cls
        return res

    # def update_from_proto(self):
    #     pass
    #
    # def get_proto_def(self):
    #     pass
    #
    # def trans2proto(self):
    #     pass


