import fastapi.responses
import numpy
import io
from PIL import Image
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

env = Environment(loader=FileSystemLoader("templates"))

def sum_two_args(x,y):
    return x+y

# Hello World route
@app.get("/")
def read_root():
    return {"Hello": "World"}

# возвращаем some.html, сгенерированный из шаблона
# передав туда одно значение something
@app.get("/some_url/{something}", response_class=HTMLResponse)
async def read_something(request: Request, something: str):
    template = env.get_template("some.html")
    content = template.render(something=something)
    return HTMLResponse(content=content)

def create_some_image(some_difs):
    imx = 200
    imy = 200
    image = numpy.zeros((imx,imy, 3), dtype=numpy.uint8)
    image[0:imy//2,0:imx//2,0] = some_difs
    image[imy//2:,imx//2:,2] = 240
    image[imy//2:,0:imx//2, 1] = 240
    return image

# возврат изображения в виде потока медиаданных по URL
@app.get("/bimage", response_class=fastapi.responses.StreamingResponse)
async def b_image(request: Request):
    # рисуем изображение, сюда можете вставить GAN, WGAN сети и т. д.
    
    # взять изображение из массива в Image PIL
    image = create_some_image(100)
    im = Image.fromarray(image, mode="RGB")
    # сохраняем изображение в буфере оперативной памяти
    imgio = io.BytesIO()
    im.save(imgio, 'JPEG')
    imgio.seek(0)
    # Возвращаем изображение в виде mime типа image/jpeg
    return fastapi.responses.StreamingResponse(content=imgio, media_type="image/jpeg")


# возврат двух изображений в таблице html, одна ячейка ссылается на url bimage
# другая ячейка указывает на файл из папки static по ссылке
# при этом файл туда предварительно сохраняется после генерации из массива
@app.get("/image", response_class=HTMLResponse)
async def make_image(request: Request):
    image_n = "image.jpg"
    image_dyn = "/bimage"
    image_st = f"/static/{image_n}"
    
    image = create_some_image(250)
    im = Image.fromarray(image, mode="RGB")
    im.save(f"./static/{image_n}")
    
    # передаем в шаблон две переменные, к которым сохранили url
    template = env.get_template("image.html")
    content = template.render(im_st=image_st, im_dyn=image_dyn)
    return HTMLResponse(content=content)