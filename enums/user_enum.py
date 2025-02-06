
from enum import Enum

class RoleEnum(Enum):
    guest = "guest"
    admin = "admin"
    superadmin = "superadmin"
    agentetb = "agentetb"
    

class StatuEnum(Enum):
    active = "active"
    inactive = "inactive"
    
    
class ServiceTypeEnum(Enum):
    ASG_CUM_01 = "ASG_CUM_01"
    ASG_CUM_03 = "ASG_CUM_03"
    ASG_CUM_04 = "ASG_CUM_04"
    
    
class TypeIHistoryEnum(Enum):
    indicator = "indicator"
    calculated = "calculated"
    registered = "registered"
    
    
    
    