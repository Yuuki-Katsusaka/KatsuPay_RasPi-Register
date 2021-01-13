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
    __products = None

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
    def set_products(arg):
        PayInfo.__products = arg

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
    def get_products():
        return PayInfo.__products

    @staticmethod
    def clearInfo():
        PayInfo.__payType = PayType.NOTYPE
        PayInfo.__payVal = None
        PayInfo.__sudentID = None
        PayInfo.__products = None

    @staticmethod
    def clearAllInfo():
        PayInfo.__payType = PayType.NOTYPE
        PayInfo.__payVal = None
        PayInfo.__sudentID = None
        PayInfo.__storeID = None
        PayInfo.__products = None

    @staticmethod
    def get_DictPaymentInfo():
        productIdList = ""
        for i in PayInfo.get_products():
            productIdList += str(i) + "$"
        productIdList = productIdList.rstrip("$")
        print(productIdList)
        return {"customerId": str(PayInfo.get_studentID()), "storeId": str(PayInfo.get_storeID()), "productIdList": productIdList, "price": str(PayInfo.get_payVal())}

    @staticmethod
    def get_DictChargeInfo():
        return {"customerId": str(PayInfo.get_studentID()), "storeId": str(PayInfo.get_storeID()), "price": str(PayInfo.get_payVal())}
