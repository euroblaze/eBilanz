import datetime

from pydantic import BaseModel, ConfigDict


class WirtschaftsjahrOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    bezeichnung: str
    von: datetime.date
    bis: datetime.date
    taxonomie_version: str
    taxonomie_label: str
    status: str


class WirtschaftsjahrIn(BaseModel):
    bezeichnung: str
    von: datetime.date
    bis: datetime.date
    taxonomie_version: str
    taxonomie_label: str
    status: str = "Entwurf"
