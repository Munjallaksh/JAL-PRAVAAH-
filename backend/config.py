import os
from pydantic import BaseModel

class Settings(BaseModel):
    PROJECT_NAME: str = "Geospatial Flood Simulation & HADR Platform"
    API_V1_STR: str = "/api"
    DATA_DIR: str = os.path.join(os.path.dirname(__file__), "data")
    EXPORT_DIR: str = os.path.join(os.path.dirname(__file__), "exports_storage")
    
    # Delft3D configuration
    DELFT3D_BIN_PATH: str = os.getenv("DELFT3D_BIN_PATH", "")
    DELFT3D_IS_CONFIGURED: bool = False
    
    # Google Earth Engine credentials (optional)
    GEE_SERVICE_ACCOUNT: str = os.getenv("GEE_SERVICE_ACCOUNT", "")
    GEE_PRIVATE_KEY_PATH: str = os.getenv("GEE_PRIVATE_KEY_PATH", "")
    GEE_IS_CONFIGURED: bool = False

settings = Settings()

os.makedirs(settings.EXPORT_DIR, exist_ok=True)
