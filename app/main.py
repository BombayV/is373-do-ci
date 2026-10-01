from fastapi import FastAPI, Depends, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.database import engine, Base, get_db
from app.models import Item

# Create database tables automatically
Base.metadata.create_all(bind=engine)

app = FastAPI(title="IT373 App")
templates = Jinja2Templates(directory="app/templates")

@app.get("/", response_class=HTMLResponse)
def read_root(request: Request, db: Session = Depends(get_db)):
    items = db.query(Item).all()
    return templates.TemplateResponse("index.html", {"request": request, "items": items})

@app.post("/items", response_class=HTMLResponse)
def create_item(
    request: Request, 
    title: str = Form(...), 
    description: str = Form(...), 
    db: Session = Depends(get_db)
):
    db_item = Item(title=title, description=description)
    db.add(db_item)
    db.commit()
    db.refresh(db_item)
    items = db.query(Item).all()
    return templates.TemplateResponse("index.html", {"request": request, "items": items})
