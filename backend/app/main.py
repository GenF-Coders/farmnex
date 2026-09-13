from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def mian():
    return "hii"