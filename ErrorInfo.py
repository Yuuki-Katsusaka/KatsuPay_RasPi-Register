from enum import Enum, auto

class ErrorInfo(Enum):
    E0 = auto() # 予期しないエラー
    E1 = auto() # 残高不足エラー
    E2 = auto() # IDカード認証エラー

def ErrorMessage(e):
    if e == ErrorInfo.E0:
        em = "予期しないエラー．" 
    elif e == ErrorInfo.E1:
        em = "残高が不足しています．"
    elif e == ErrorInfo.E2:
        em = "不正なIDカードです．"
    
    return em