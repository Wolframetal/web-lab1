import fastapi.responses
import numpy
import io
from PIL import Image
from fastapi import FastAPI, Request, Form, File, UploadFile
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader
from typing import List
import hashlib
from PIL import ImageDraw
import matplotlib
matplotlib.use('Agg')  # Важно для работы в серверной среде без GUI
import matplotlib.pyplot as plt
import base64
import os

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

env = Environment(loader=FileSystemLoader("templates"))

def sum_two_args(x, y):
    return x + y

# Hello World route
@app.get("/")
def read_root():
    return {"Hello": "World"}

# возвращаем some.html, сгенерированный из шаблона
@app.get("/some_url/{something}", response_class=HTMLResponse)
async def read_something(request: Request, something: str):
    template = env.get_template("some.html")
    content = template.render(something=something)
    return HTMLResponse(content=content)

def create_some_image(some_difs):
    imx = 200
    imy = 200
    image = numpy.zeros((imx, imy, 3), dtype=numpy.uint8)
    image[0:imy // 2, 0:imx // 2, 0] = some_difs
    image[imy // 2:, imx // 2:, 2] = 240
    image[imy // 2:, 0:imx // 2, 1] = 240
    return image

# возврат изображения в виде потока медиаданных по URL
@app.get("/bimage", response_class=StreamingResponse)
async def b_image(request: Request):
    image = create_some_image(100)
    im = Image.fromarray(image, mode="RGB")
    imgio = io.BytesIO()
    im.save(imgio, 'JPEG')
    imgio.seek(0)
    return StreamingResponse(content=imgio, media_type="image/jpeg")

# возврат двух изображений в таблице html
@app.get("/image", response_class=HTMLResponse)
async def make_image(request: Request):
    image_n = "image.jpg"
    image_dyn = "/bimage"
    image_st = f"/static/{image_n}"

    image = create_some_image(250)
    im = Image.fromarray(image, mode="RGB")
    im.save(f"./static/{image_n}")

    template = env.get_template("image.html")
    content = template.render(im_st=image_st, im_dyn=image_dyn)
    return HTMLResponse(content=content)

# --- ВАРИАНТ 11 ---

def create_color_histogram(images: List[numpy.ndarray]) -> str:
    """
    Создает гистограмму распределения цветов для списка изображений.
    Возвращает путь к сохраненному файлу гистограммы.
    """
    fig, axs = plt.subplots(len(images), 1, figsize=(10, 5 * len(images)))
    if len(images) == 1:
        axs = [axs]

    colors = ('r', 'g', 'b')
    for i, img_array in enumerate(images):
        for j, color in enumerate(colors):
            hist, bins = numpy.histogram(img_array[:, :, j], bins=256, range=(0, 256))
            axs[i].plot(bins[:-1], hist, color=color, alpha=0.7)
        axs[i].set_title(f'Изображение {i+1}')
        axs[i].set_xlabel('Интенсивность')
        axs[i].set_ylabel('Количество пикселей')
        axs[i].legend(['Red', 'Green', 'Blue'])

    plt.tight_layout()
    histogram_path = "static/histogram.png"
    plt.savefig(histogram_path)
    plt.close(fig)
    return histogram_path

def stitch_images(img1: Image.Image, img2: Image.Image, direction: str) -> Image.Image:
    """
    Склеивает два изображения по горизонтали или вертикали.
    """
    if direction == 'horizontal':
        h = max(img1.height, img2.height)
        img1 = img1.resize((int(img1.width * h / img1.height), h))
        img2 = img2.resize((int(img2.width * h / img2.height), h))
        new_width = img1.width + img2.width
        new_height = h
    else:  # vertical
        w = max(img1.width, img2.width)
        img1 = img1.resize((w, int(img1.height * w / img1.width)))
        img2 = img2.resize((w, int(img2.height * w / img2.width)))
        new_width = w
        new_height = img1.height + img2.height

    new_img = Image.new('RGB', (new_width, new_height))

    if direction == 'horizontal':
        new_img.paste(img1, (0, 0))
        new_img.paste(img2, (img1.width, 0))
    else:  # vertical
        new_img.paste(img1, (0, 0))
        new_img.paste(img2, (0, img1.height))

    return new_img

# Отображение HTML формы (GET запрос)
@app.get("/image_form", response_class=HTMLResponse)
async def show_image_form(request: Request):
    template = env.get_template("forms.html")
    content = template.render(request=request, ready=False, images=[])
    return HTMLResponse(content=content)

# Обработка POST запроса с формой
@app.post("/image_form", response_class=HTMLResponse)
async def process_image_form(
    request: Request,
    name_op: str = Form(),
    number_op: int = Form(),
    r: int = Form(),
    g: int = Form(),
    b: int = Form(),
    files: List[UploadFile] = File(description="Multiple files as UploadFile")
):
    ready = False
    images = []
    if files and len(files) > 0 and files[0].filename:
        ready = True
        images = ["static/" + hashlib.sha256(file.filename.encode('utf-8')).hexdigest() + ".jpg" for file in files]
        content = [await file.read() for file in files]
        for i, con in enumerate(content):
            img = Image.open(io.BytesIO(con)).convert("RGB").resize((200, 200))
            draw = ImageDraw.Draw(img)
            draw.ellipse((100, 100, 150, 200 + number_op), fill=(r, g, b), outline=(0, 0, 0))
            img.save("./" + images[i], 'JPEG')

    template = env.get_template("forms.html")
    content = template.render(request=request, ready=ready, images=images)
    return HTMLResponse(content=content)

# --- НОВЫЕ ЭНДПОИНТЫ ДЛЯ ВАРИАНТА 11 ---

@app.get("/stitch_form", response_class=HTMLResponse)
async def show_stitch_form(request: Request):
    """Отображает форму для склейки изображений."""
    template = env.get_template("stitch.html")
    content = template.render(request=request, ready=False)
    return HTMLResponse(content=content)

@app.post("/stitch_form", response_class=HTMLResponse)
async def process_stitch_form(
    request: Request,
    file1: UploadFile = File(...),
    file2: UploadFile = File(...),
    direction: str = Form(...)
):
    """Обрабатывает форму склейки изображений."""
    # Чтение и сохранение исходных изображений
    img1_data = await file1.read()
    img2_data = await file2.read()

    img1 = Image.open(io.BytesIO(img1_data)).convert("RGB")
    img2 = Image.open(io.BytesIO(img2_data)).convert("RGB")

    # Сохранение исходных изображений для отображения
    img1_path = f"static/{hashlib.sha256(file1.filename.encode()).hexdigest()}.jpg"
    img2_path = f"static/{hashlib.sha256(file2.filename.encode()).hexdigest()}.jpg"
    img1.save(img1_path)
    img2.save(img2_path)

    # Склейка
    stitched_img = stitch_images(img1, img2, direction)
    stitched_path = f"static/stitched_{hashlib.sha256((file1.filename + file2.filename).encode()).hexdigest()}.jpg"
    stitched_img.save(stitched_path)

    # Построение гистограмм
    img1_array = numpy.array(img1)
    img2_array = numpy.array(img2)
    stitched_array = numpy.array(stitched_img)
    
    histogram_path = create_color_histogram([img1_array, img2_array, stitched_array])

    # Подготовка данных для шаблона
    images = [img1_path.replace("static/", ""), img2_path.replace("static/", "")]
    stitched_image = stitched_path.replace("static/", "")
    histogram_image = histogram_path.replace("static/", "")

    template = env.get_template("stitch.html")
    content = template.render(
        request=request,
        ready=True,
        images=images,
        stitched_image=stitched_image,
        histogram_image=histogram_image
    )
    return HTMLResponse(content=content)