from enum import Enum, auto

class PayType(Enum):
    NOTYPE = auto()
    PAYMENT = auto()
    CHARGE = auto()


class PayInfo():
    __payType = PayType.NOTYPE
    __payVal = None
    __sudentID = None
    __storeID = None

    @staticmethod
    def set_payType(arg):
        PayInfo.__payType = arg

    @staticmethod
    def set_payVal(arg):
        PayInfo.__payVal = arg

    @staticmethod
    def set_studentID(arg):
        PayInfo.__sudentID = arg

    @staticmethod
    def set_storeID(arg):
        PayInfo.__storeID = arg

    @staticmethod
    def get_payType():
        return PayInfo.__payType

    @staticmethod
    def get_payVal():
        return PayInfo.__payVal

    @staticmethod
    def get_studentID():
        return PayInfo.__sudentID

    @staticmethod
    def get_storeID():
        return PayInfo.__storeID

    @staticmethod
    def clearInfo():
        PayInfo.__payType = PayType.NOTYPE
        PayInfo.__payVal = None
        PayInfo.__sudentID = None
        PayInfo.__storeID = None
