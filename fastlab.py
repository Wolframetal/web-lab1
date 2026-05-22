from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
app = FastAPI()

def sum_two_args(x,y):
    return x+y

# Hello World route
@app.get("/")
def read_root():
    return {"Hello": "World"}

# Монтируем статические файлы
app.mount("/static", StaticFiles(directory="static"), name="static")

# Настраиваем шаблонизатор
templates = Jinja2Templates(directory="templates")

@app.get("/some_url/{something}", response_class=HTMLResponse)
async def read_something(request: Request, something: str):
    return templates.TemplateResponse(
        "some.html", 
        {"request": request,"something": something}
    )