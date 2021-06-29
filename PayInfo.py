from configparser import NoOptionError
from enum import Enum, auto


class PayType(Enum):
    NOTYPE = auto()
    PAYMENT = auto()
    CHARGE = auto()


class PayInfo():
    __payType = PayType.NOTYPE
    __payVal = None
    __chargeVal = None
    __sudentID = None
    __storeID = None
    __products = None
    # __cartFlag = None
    __lackBalanceFlag = False

    @staticmethod
    def set_payType(arg):
        PayInfo.__payType = arg

    @staticmethod
    def set_payVal(arg):
        PayInfo.__payVal = arg

    @staticmethod
    def set_chargeVal(arg):
        PayInfo.__chargeVal = arg

    @staticmethod
    def set_studentID(arg):
        PayInfo.__sudentID = arg

    @staticmethod
    def set_storeID(arg):
        PayInfo.__storeID = arg

    @staticmethod
    def set_products(arg):
        PayInfo.__products = arg
    
    # @staticmethod
    # def set_cartFlag(arg):
    #     PayInfo.__cartFlag = arg

    @staticmethod
    def set_lackBalanceFlag(arg):
        PayInfo.__lackBalanceFlag = arg

    @staticmethod
    def get_payType():
        return PayInfo.__payType

    @staticmethod
    def get_payVal():
        return PayInfo.__payVal

    @staticmethod
    def get_chargeVal():
        return PayInfo.__chargeVal

    @staticmethod
    def get_studentID():
        return PayInfo.__sudentID

    @staticmethod
    def get_storeID():
        return PayInfo.__storeID

    @staticmethod
    def get_products():
        return PayInfo.__products
    
    # @staticmethod
    # def get_cartFlag():
    #     return PayInfo.__cartFlag

    @staticmethod
    def get_lackBalanceFlag():
        return PayInfo.__lackBalanceFlag

    @staticmethod
    def cleareChargeVal():
        PayInfo.__chargeVal = None

    @staticmethod
    def clearInfo():
        PayInfo.__payType = PayType.NOTYPE
        PayInfo.__payVal = None
        PayInfo.__chargeVal = None
        PayInfo.__sudentID = None
        PayInfo.__products = None
        PayInfo.__lackBalanceFlag = False

    @staticmethod
    def clearAllInfo():
        PayInfo.__payType = PayType.NOTYPE
        PayInfo.__payVal = None
        PayInfo.__chargeVal = None
        PayInfo.__sudentID = None
        PayInfo.__storeID = None
        PayInfo.__products = None
        PayInfo.__lackBalanceFlag = False

    @staticmethod
    def get_DictPaymentInfo():
        productIdList = ""
        for i in PayInfo.get_products():
            productIdList += str(i) + "$"
        productIdList = productIdList.rstrip("$")
        return {"customerId": str(PayInfo.get_studentID()), "storeId": str(PayInfo.get_storeID()), "productIdList": productIdList, "price": str(PayInfo.get_payVal())}

    @staticmethod
    def get_DictChargeInfo():
        return {"customerId": str(PayInfo.get_studentID()), "storeId": str(PayInfo.get_storeID()), "price": str(PayInfo.get_chargeVal())}
