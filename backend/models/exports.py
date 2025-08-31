from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ExportResponse(BaseModel):
    nodes_csv_url: Optional[str] = None
    relationships_csv_url: Optional[str] = None
    vertices_csv_url: Optional[str] = None
    edges_csv_url: Optional[str] = None
    download_expires_at: datetime