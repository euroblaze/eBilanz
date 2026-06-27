from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.deps import get_db
from app.models import Wirtschaftsjahr
from app.schemas.wj import WirtschaftsjahrIn, WirtschaftsjahrOut

router = APIRouter(prefix="/api/wirtschaftsjahre", tags=["wirtschaftsjahr"])


@router.get("", response_model=list[WirtschaftsjahrOut])
def liste(db: Session = Depends(get_db)):
    return list(
        db.scalars(select(Wirtschaftsjahr).order_by(Wirtschaftsjahr.von.desc())).all()
    )


@router.post("", response_model=WirtschaftsjahrOut, status_code=201)
def anlegen(body: WirtschaftsjahrIn, db: Session = Depends(get_db)):
    wj = Wirtschaftsjahr(**body.model_dump())
    db.add(wj)
    db.commit()
    db.refresh(wj)
    return wj
